import frappe

PAYMENT_NOTIFU_URL = f"{frappe.utils.get_url()}/payment_notification"
RETURN_URL = f"{frappe.utils.get_url()}/return_url"