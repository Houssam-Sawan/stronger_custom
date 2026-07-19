frappe.query_reports["Custom Profit Loss"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            reqd: 1
        },
        {
            fieldname: "fiscal_year",
            label: __("Fiscal Year"),
            fieldtype: "Link",
            options: "Fiscal Year",
            reqd: 1,
            default: frappe.defaults.get_user_default("fiscal_year")
        }
    ]
};