// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.require("assets/erpnext/js/financial_statements.js", function() {
    // Standard ERPNext layout features core toggles natively!
    frappe.query_reports["Custom P&L Statement"] = $.extend({}, erpnext.financial_statements);

    // Inject custom structural line item formatter rules
    frappe.query_reports["Custom P&L Statement"]["formatter"] = function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data && data.add_class === "bold") {
            value = value.bold();
        }
        return value;
    };

    // Append extra dimension layers matching core functionality
    frappe.query_reports["Custom P&L Statement"]["filters"].push(
        {
            "fieldname": "project",
            "label": __("Project"),
            "fieldtype": "MultiSelectList",
            get_data: function(txt) {
                return frappe.db.get_link_options('Project', txt);
            }
        },
        {
            "fieldname": "include_default_book_entries",
            "label": __("Include Default Book Entries"),
            "fieldtype": "Check",
            "default": 1
        }
    );
});