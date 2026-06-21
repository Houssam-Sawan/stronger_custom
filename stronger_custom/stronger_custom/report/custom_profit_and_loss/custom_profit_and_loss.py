import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters: filters = {}
    
    # 1. Define Columns (forcing IQD currency formatting)
    columns = [
        {"label": "Account / Line Item", "fieldname": "line_item", "fieldtype": "Data", "width": 300},
        {"label": "Actual (IQD)", "fieldname": "actual", "fieldtype": "Currency", "options": "IQD", "width": 150},
        {"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 300}
    ]
    
    # 2. Fetch Aggregated Data from GL Entries
    company = filters.get("company")
    filter_based_on = filters.get("filter_based_on")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
	# If filtering by Fiscal Year, automatically extract the start and end dates
    if filter_based_on == "Fiscal Year" and filters.get("fiscal_year"):
       fy_doc = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
       from_date = fy_doc.year_start_date
       to_date = fy_doc.year_end_date

	# Guard rail check to ensure dates exist before running SQL queries
       if not from_date or not to_date:
         frappe.throw(_("Please select a valid date range or fiscal year."))
         
def get_balance(account_type=None, root_type=None):
    # Added voucher_type != 'Period Closing Voucher' to ignore year-end reset entries
    cond = """company = %(company)s 
              AND posting_date BETWEEN %(from_date)s AND %(to_date)s 
              AND voucher_type != 'Period Closing Voucher'"""
    
    params = {"company": company, "from_date": from_date, "to_date": to_date}
    
    if account_type:
        cond += " AND account in (select name from tabAccount where account_type=%(account_type)s)"
        params["account_type"] = account_type
    elif root_type:
        cond += " AND account in (select name from tabAccount where root_type=%(root_type)s)"
        params["root_type"] = root_type
        
    gl_data = frappe.db.sql(f"SELECT SUM(credit) - SUM(debit) FROM `tabGL Entry` WHERE {cond}", params)
    return flt(gl_data[0][0]) if gl_data and gl_data[0][0] else 0.0

    # 3. Calculate metrics mimicking your exact template structure
    # NOTE: Map these to your actual ERPNext Account Categories or Group Accounts
    revenue = get_balance(root_type="Income") 
    cost_of_sales = get_balance(account_type="Cost of Goods Sold") # Ensure negative in display if preferred
    gross_profit = revenue - abs(cost_of_sales)
    
    admin_expenses = get_balance(account_type="Administrative Expense")
    marketing_expenses = get_balance(account_type="Selling Expense")
    profit_from_ops = gross_profit - (admin_expenses + marketing_expenses)
    
    other_income_expense = get_balance(account_type="Other Expense") # Adjust sign logically
    ebitda = profit_from_ops + other_income_expense
    
    depreciation_amortization = get_balance(account_type="Depreciation")
    ebit = ebitda - abs(depreciation_amortization)
    
    net_financing = get_balance(account_type="Finance Equity") 
    income_tax = get_balance(account_type="Tax")
    profit_after_tax = ebit - net_financing - income_tax

    # 4. Construct Data Rows matching the PDF Layout
    data = [
        {"line_item": "Revenue", "actual": revenue, "description": ""},
        {"line_item": "Cost of sales", "actual": -cost_of_sales, "description": ""},
        {"line_item": "Gross profit", "actual": gross_profit, "description": "", "add_class": "bold"},
        {"line_item": "Administrative expenses", "actual": -admin_expenses, "description": ""},
        {"line_item": "Sales and Marketing", "actual": -marketing_expenses, "description": ""},
        {"line_item": "Profit from operations", "actual": profit_from_ops, "description": "", "add_class": "bold"},
        {"line_item": "Other expenses/(income)", "actual": other_income_expense, "description": ""},
        {"line_item": "EBITDA", "actual": ebitda, "description": "Earnings Before Interest, Taxes, Depreciation, and Amortization", "add_class": "bold"},
        {"line_item": "Depreciation & Amortization", "actual": -depreciation_amortization, "description": ""},
        {"line_item": "EBIT", "actual": ebit, "description": "Earnings Before Interest and Taxes", "add_class": "bold"},
        {"line_item": "Net financing income /(costs)", "actual": -net_financing, "description": ""},
        {"line_item": "Income tax", "actual": -income_tax, "description": ""},
        {"line_item": "Profit After tax", "actual": profit_after_tax, "description": "", "add_class": "bold"}
    ]

    return columns, data