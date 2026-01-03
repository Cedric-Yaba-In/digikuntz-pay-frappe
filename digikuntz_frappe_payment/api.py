    # from digikuntz_frappe_payment.payment_gateway import create_payment_link


import frappe
import json
import digikuntz_frappe_payment.utils.gateway_factory as gateway_factory
import digikuntz_frappe_payment.utils.payment_handler as payment_handler
import digikuntz_frappe_payment.utils.enum as enum_utils


def get_payment_link(doc):
    
    return f"{frappe.utils.get_url()}/digikuntzpay/pay?ref={doc.name}"


#Lien de paiement pour la page en interne
@frappe.whitelist()
def generate_payment_link(ressource_data_name,ressource_type):
    payment_link = None

    if not frappe.db.exists("DigikuntzPay Link", {"id_ressource": ressource_data_name, "type_ressource": ressource_type}):
        payment_link = frappe.get_doc({
            "doctype": "DigikuntzPay Link",
            "id_ressource": ressource_data_name,
            "type_ressource": ressource_type
        })
        payment_link.insert()
    else:
        payment_link = frappe.get_doc("DigikuntzPay Link", {"id_ressource": ressource_data_name, "type_ressource": ressource_type})
       
    return get_payment_link(payment_link)




#Lien de paiement pour la redirection vers la page les pages externes
@frappe.whitelist(allow_guest=True)
def generate_payment_link_to_api_gateway():
    data = json.loads(frappe.request.data)
    if not frappe.db.exists("DigikuntzPay Link", {"id_ressource": data.get("invoice")}):
        throw = frappe.throw("Payment link not found")

    payment_link_doc = frappe.get_doc("DigikuntzPay Link", {"id_ressource": data.get("invoice")})

    ressource_to_pay = frappe.get_doc(payment_link_doc.type_ressource, payment_link_doc.id_ressource)

    if ressource_to_pay.outstanding_amount <= 0:
        frappe.throw(_("Invoice is already paid"))
    
    if not frappe.db.exists("Customer", ressource_to_pay.customer):
        frappe.throw(_("Customer information is missing in the resource to pay."))

    customer_data =frappe.get_doc("Customer", ressource_to_pay.customer)

    gateway_payment = gateway_factory.load_default_gateway(ressource_to_pay, customer_data)

    behavior_for_payment = frappe.db.get_single_value('DigikuntzPay Setting', 'behavior_mode')

    if behavior_for_payment == enum_utils.GatyewayPaymentBehavior.PAYMENT_BY_QRCODE.value: #Comportement lors du paiement par QrCode
        return gateway_payment.make_payment_by_qrcode()
    elif behavior_for_payment == enum_utils.GatyewayPaymentBehavior.DIRECT_PAYMENT_REQUEST.value: #Pour le paiement request
        return gateway_payment.make_direct_payment()
    else: #Dans le cas contraire Redirection URL
        return gateway_payment.get_url_to_redirect()
    
    # your API logic here
   

@frappe.whitelist(allow_guest=True)
def payment_callback():
    payment_status = None

    if payment_status:
        payment_handler.on_success_payment(None,None)
    return None

