import frappe

# PAYMENT_NOTIF_URL = f"{frappe.utils.get_url()}/digikuntzpay/notify-pay?pay_req_status={{status}}"
PAYMENT_NOTIF_URL = f"{frappe.utils.get_url()}/api/method/digikuntz_frappe_payment.api.payment_callback?pay_req_status={{status}}"

RETURN_SUCCESS_URL = f"{frappe.utils.get_url()}/api/method/digikuntz_frappe_payment.api.payment_callback?pay_req_status=success"
RETURN_CANCEL_URL = f"{frappe.utils.get_url()}/api/method/digikuntz_frappe_payment.api.payment_callback?pay_req_status=cancel"
