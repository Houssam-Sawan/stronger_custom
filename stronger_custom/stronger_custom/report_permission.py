import frappe
from frappe.desk.query_report import run as original_run


@frappe.whitelist()
def run(report_name, filters=None, user=None, ignore_prepared_report=False):

    current_user = frappe.session.user

    # Check whether this user is restricted from this report
    restriction = frappe.db.exists(
        "Report Access Restriction",
        {
            "user": current_user,
        }
    )

    if restriction:
        blocked = frappe.db.exists(
            "Blocked Reports",
            {
                "parent": restriction,
                "parenttype": "Report Access Restriction",
                "report": report_name,
            }
        )

        if blocked:
            frappe.throw(
                "You do not have permission to access this report.",
                frappe.PermissionError
            )

    return original_run(
        report_name,
        filters,
        user,
        ignore_prepared_report
    )