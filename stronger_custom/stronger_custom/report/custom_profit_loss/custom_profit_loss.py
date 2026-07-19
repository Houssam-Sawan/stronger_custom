import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):

    columns = get_columns()

    fiscal_year = frappe.get_doc("Fiscal Year", filters.fiscal_year)

    from_date = fiscal_year.year_start_date
    to_date = fiscal_year.year_end_date

    company_currency = frappe.get_cached_value(
        "Company",
        filters.company,
        "default_currency"
    )

    revenue = get_group_balance(
        filters.company,
        "Income",
        from_date,
        to_date
    )

    cost_of_sales = get_group_balance(
        filters.company,
        "Cost of Goods Sold",
        from_date,
        to_date
    )

    admin_expenses = get_group_balance(
        filters.company,
        "Administrative Expenses",
        from_date,
        to_date
    )

    sales_marketing = get_group_balance(
        filters.company,
        "Sales and Marketing",
        from_date,
        to_date
    )

    other_income = get_group_balance(
        filters.company,
        "Other Income",
        from_date,
        to_date
    )

    other_expenses = get_group_balance(
        filters.company,
        "Other Expenses",
        from_date,
        to_date
    )

    depreciation = get_group_balance(
        filters.company,
        "Depreciation",
        from_date,
        to_date
    )

    amortization = get_group_balance(
        filters.company,
        "Amortization",
        from_date,
        to_date
    )

    finance_costs = get_group_balance(
        filters.company,
        "Finance Cost",
        from_date,
        to_date
    )

    income_tax = get_group_balance(
        filters.company,
        "Income Tax",
        from_date,
        to_date
    )

    gross_profit = revenue - cost_of_sales

    profit_from_operations = (
        gross_profit
        - admin_expenses
        - sales_marketing
    )

    ebitda = (
        profit_from_operations
        + other_income
        - other_expenses
    )

    ebit = (
        ebitda
        - depreciation
        - amortization
    )

    profit_after_tax = (
        ebit
        - finance_costs
        - income_tax
    )

    data = [
        row("Revenue", revenue, company_currency),
        row("Cost of Sales", -cost_of_sales, company_currency),
        row("Gross Profit", gross_profit, company_currency),

        {},

        row("Administrative Expenses", -admin_expenses, company_currency),
        row("Sales and Marketing", -sales_marketing, company_currency),
        row("Profit from Operations", profit_from_operations, company_currency),

        {},

        row(
            "Other Expenses/(Income)",
            other_income - other_expenses,
            company_currency
        ),

        row("EBITDA", ebitda, company_currency),

        row("Depreciation", -depreciation, company_currency),
        row("Amortization", -amortization, company_currency),

        row("EBIT", ebit, company_currency),

        {},

        row(
            "Net Financing Income/(Costs)",
            -finance_costs,
            company_currency
        ),

        row("Income Tax", -income_tax, company_currency),

        row(
            "Profit After Tax",
            profit_after_tax,
            company_currency
        )
    ]

    return columns, data


def get_columns():
    return [
        {
            "label": _("Description"),
            "fieldname": "description",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 180
        }
    ]


def row(description, amount, currency):
    return {
        "description": description,
        "amount": amount,
        "currency": currency
    }


def get_group_balance(company, account_name, from_date, to_date):

    account = frappe.db.get_value(
        "Account",
        {
            "company": company,
            "account_name": account_name
        },
        ["lft", "rgt"],
        as_dict=True
    )

    if not account:
        return 0

    balance = frappe.db.sql(
        """
        SELECT
            ABS(IFNULL(SUM(gl.debit - gl.credit),0))
        FROM `tabGL Entry` gl
        INNER JOIN `tabAccount` acc
            ON gl.account = acc.name
        WHERE
            acc.lft >= %s
            AND acc.rgt <= %s
            AND acc.company = %s
            AND gl.posting_date BETWEEN %s AND %s
        """,
        (
            account.lft,
            account.rgt,
            company,
            from_date,
            to_date
        )
    )[0][0]

    return flt(balance)