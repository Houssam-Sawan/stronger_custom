import frappe
from frappe import auth

@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.response['message'] = {
            "success_key": 0,
            "message": "Invalid credentials"
        }
        return

    # User is now authenticated in this session
    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)
    company = frappe.db.get_value('User Permission', {"user": frappe.session.user,"allow": "Company"}, 'for_value') or None
    company_abbr = frappe.db.get_value('Company', company, 'abbr') if company else None

    frappe.response['message'] = {
        "success_key": 1,
        "message": "Logged in deep",
        "sid": frappe.session.sid,
        "api_key": user.api_key,
        "api_secret": api_generate,
        "username": user.username,
        "email": user.email,
        "company": company,
        "company_abbr": company_abbr
    }

def generate_keys(user):
    # Use ignore_permissions because a standard user can't usually edit their own User doc via .save()
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key

    user_details.api_secret = api_secret
    
    # Save without triggering full validation/permission checks
    user_details.save(ignore_permissions=True)
    
    return api_secret