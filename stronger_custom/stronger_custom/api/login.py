import frappe
from frappe import auth

@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
  try:
    login_manager = frappe.auth.LoginManager()
    login_manager.authenticate(user=usr, pwd=pwd)
    login_manager.post_login()
  except frappe.execeptions.AuthenticationError:
    frappe.clear_messages()
    frappe.local.reponse['message'] = {
      "success_key": 0,
      "message": "Invalid credentials"
    }
    return 'Invalid credentials'
  
  api_generate = generate_keys(frappe.session.user)
  user = frappe.get_doc('User', frappe.session.user)

  frappe.response['message'] = {
    "success_key": 1,
    "message": "Logged in",
    "sid": frappe.session.sid,
    "api_key": user.api_key,
    "api_secret": api_generate,
    "username": user.username,
    "email": user.email
  }

def generate_keys(user):
  user_details = frappe.get_doc('User', user)
  api_secret = frappe.generate_hash(length=15)

  if not user_details.api_key:
    api_key = frappe.generate_hash(length=15)
    user_details.api_key = api_key
  
  user_details.api_secret = api_secret
  user_details.save()

  return api_secret