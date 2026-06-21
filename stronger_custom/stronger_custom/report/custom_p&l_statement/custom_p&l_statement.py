# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.financial_statements import (
    get_columns,
    get_data,
    get_filtered_list_for_consolidated_report,
    get_period_list,
)

def execute(filters=None):
    if not filters: filters = frappe._dict()
    
    # Force presentation currency to IQD
    filters.presentation_currency = "IQD"
    
    # Core framework requires these exact field references
    period_list = get_period_list(
        filters.get("from_fiscal_year"),
        filters.get("to_fiscal_year"),
        filters.get("period_start_date"),
        filters.get("period_end_date"),
        filters.get("filter_based_on"),
        filters.get("periodicity"),
        company=filters.company,
    )

    income = get_data(
        filters.company,
        "Income",
        "Credit",
        period_list,
        filters=filters,
        accumulated_values=filters.accumulated_values,
        ignore_closing_entries=True,
        ignore_accumulated_values_for_fy=True,
    )

    expense = get_data(
        filters.company,
        "Expense",
        "Debit",
        period_list,
        filters=filters,
        accumulated_values=filters.accumulated_values,
        ignore_closing_entries=True,
        ignore_accumulated_values_for_fy=True,
    )

    columns = get_columns(
        filters.periodicity, period_list, filters.accumulated_values, filters.company
    )

    def get_row_values(dataset, account_name=None):
        row_map = {}
        for col in columns[2:]:
            fieldname = col.get("fieldname")
            row_map[fieldname] = 0.0
            
        if not dataset:
            return row_map
            
        for row in dataset:
            if account_name and row.get("account_name") == account_name:
                for col in columns[2:]:
                    fn = col.get("fieldname")
                    row_map[fn] = flt(row.get(fn, 0.0))
                return row_map
            elif not account_name and row.get("account_name") in ["Total Income", "Total Expense"]:
                for col in columns[2:]:
                    fn = col.get("fieldname")
                    row_map[fn] = flt(row.get(fn, 0.0))
        return row_map

    revenue_vals = get_row_values(income)
    cogs_vals = get_row_values(expense, "Cost of Goods Sold")
    admin_vals = get_row_values(expense, "Administrative Expenses")
    marketing_vals = get_row_values(expense, "Selling and Marketing Expenses")
    other_exp_vals = get_row_values(expense, "Other Expenses")
    depr_vals = get_row_values(expense, "Depreciation Expenses")
    finance_vals = get_row_values(expense, "Finance Costs")
    tax_vals = get_row_values(expense, "Income Tax Expenses")
    
    custom_data = []
    
    gross_profit = {"account_name": _("Gross profit"), "add_class": "bold"}
    profit_ops = {"account_name": _("Profit from operations"), "add_class": "bold"}
    ebitda = {"account_name": _("EBITDA"), "add_class": "bold", "description": _("Earnings Before Interest, Taxes, Depreciation, and Amortization")}
    ebit = {"account_name": _("EBIT"), "add_class": "bold", "description": _("Earnings Before Interest and Taxes")}
    profit_after_tax = {"account_name": _("Profit After tax"), "add_class": "bold"}

    for col in columns[2:]:
        fn = col.get("fieldname")
        gross_profit[fn] = revenue_vals[fn] - cogs_vals[fn]
        profit_ops[fn] = gross_profit[fn] - (admin_vals[fn] + marketing_vals[fn])
        ebitda[fn] = profit_ops[fn] - other_exp_vals[fn]
        ebit[fn] = ebitda[fn] - depr_vals[fn]
        profit_after_tax[fn] = ebit[fn] - finance_vals[fn] - tax_vals[fn]

    custom_data.append(dict({"account_name": _("Revenue")}, **revenue_vals))
    custom_data.append(dict({"account_name": _("Cost of sales")}, **{k: -v for k,v in cogs_vals.items()}))
    custom_data.append(gross_profit)
    custom_data.append(dict({"account_name": _("Administrative expenses")}, **{k: -v for k,v in admin_vals.items()}))
    custom_data.append(dict({"account_name": _("Sales and Marketing")}, **{k: -v for k,v in marketing_vals.items()}))
    custom_data.append(profit_ops)
    custom_data.append(dict({"account_name": _("Other expenses/(income)")}, **other_exp_vals))
    custom_data.append(ebitda)
    custom_data.append(dict({"account_name": _("Depreciation & Amortization")}, **{k: -v for k,v in depr_vals.items()}))
    custom_data.append(ebit)
    custom_data.append(dict({"account_name": _("Net financing income /(costs)")}, **{k: -v for k,v in finance_vals.items()}))
    custom_data.append(dict({"account_name": _("Income tax")}, **{k: -v for k,v in tax_vals.items()}))
    custom_data.append(profit_after_tax)

    chart = get_chart_data(filters, columns, income, expense, profit_after_tax)
    report_summary = get_report_summary(period_list, filters.periodicity, income, expense, profit_after_tax, "IQD", filters)

    return columns, custom_data, None, chart, report_summary


# Keep original core functions unchanged (get_report_summary, get_chart_data) below...


def get_report_summary(
	period_list, periodicity, income, expense, net_profit_loss, currency, filters, consolidated=False
):
	net_income, net_expense, net_profit = 0.0, 0.0, 0.0

	# from consolidated financial statement
	if filters.get("accumulated_in_group_company"):
		period_list = get_filtered_list_for_consolidated_report(filters, period_list)

	for period in period_list:
		key = period if consolidated else period.key
		if income:
			net_income += income[-2].get(key)
		if expense:
			net_expense += expense[-2].get(key)
		if net_profit_loss:
			net_profit += net_profit_loss.get(key)

	if len(period_list) == 1 and periodicity == "Yearly":
		profit_label = _("Profit This Year")
		income_label = _("Total Income This Year")
		expense_label = _("Total Expense This Year")
	else:
		profit_label = _("Net Profit")
		income_label = _("Total Income")
		expense_label = _("Total Expense")

	return [
		{"value": net_income, "label": income_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "-"},
		{"value": net_expense, "label": expense_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "=", "color": "blue"},
		{
			"value": net_profit,
			"indicator": "Green" if net_profit > 0 else "Red",
			"label": profit_label,
			"datatype": "Currency",
			"currency": currency,
		},
	]


def get_net_profit_loss(income, expense, period_list, company, currency=None, consolidated=False):
	total = 0
	net_profit_loss = {
		"account_name": "'" + _("Profit for the year") + "'",
		"account": "'" + _("Profit for the year") + "'",
		"warn_if_negative": True,
		"currency": currency or frappe.get_cached_value("Company", company, "default_currency"),
	}

	has_value = False

	for period in period_list:
		key = period if consolidated else period.key
		total_income = flt(income[-2][key], 3) if income else 0
		total_expense = flt(expense[-2][key], 3) if expense else 0

		net_profit_loss[key] = total_income - total_expense

		if net_profit_loss[key]:
			has_value = True

		total += flt(net_profit_loss[key])
		net_profit_loss["total"] = total

	if has_value:
		return net_profit_loss


def get_chart_data(filters, columns, income, expense, net_profit_loss):
	labels = [d.get("label") for d in columns[2:]]

	income_data, expense_data, net_profit = [], [], []

	for p in columns[2:]:
		if income:
			income_data.append(income[-2].get(p.get("fieldname")))
		if expense:
			expense_data.append(expense[-2].get(p.get("fieldname")))
		if net_profit_loss:
			net_profit.append(net_profit_loss.get(p.get("fieldname")))

	datasets = []
	if income_data:
		datasets.append({"name": _("Income"), "values": income_data})
	if expense_data:
		datasets.append({"name": _("Expense"), "values": expense_data})
	if net_profit:
		datasets.append({"name": _("Net Profit/Loss"), "values": net_profit})

	chart = {"data": {"labels": labels, "datasets": datasets}}

	if not filters.accumulated_values:
		chart["type"] = "bar"
	else:
		chart["type"] = "line"

	chart["fieldtype"] = "Currency"

	return chart
