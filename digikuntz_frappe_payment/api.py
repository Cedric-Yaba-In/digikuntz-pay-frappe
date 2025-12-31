    # from digikuntz_frappe_payment.payment_gateway import create_payment_link


import frappe
import json
import digikuntz_frappe_payment.gateways.utils as gateway_utils
import digikuntz_frappe_payment.gateways.enum as enum_utils


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

    gateway_payment = gateway_utils.load_default_gateway()

    behavior_for_payment = frappe.db.get_single_value('DigikuntzPay Setting', 'behavior_mode')

    if behavior_for_payment == enum_utils.GatyewayPaymentBehavior.REDIRECTION_URL.value: #Comportement lors de la rédirection vers l'urm
        return gateway_payment.get_url_to_redirect()
    elif behavior_for_payment == enum_utils.GatyewayPaymentBehavior.DIRECT_PAYMENT_REQUEST.value: #Pour le paiement request
        return gateway_payment.make_direct_payment()
    else: #Dans le cas contraire QRCode
        return gateway_payment.make_payment_by_qrcode()
 
    
    # your API logic here
   

