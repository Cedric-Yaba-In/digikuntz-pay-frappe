    # from digikuntz_frappe_payment.payment_gateway import create_payment_link

import frappe

def get_payment_link(doc):
    
    return f"{frappe.utils.get_url()}/digikuntzpay/pay?ref={doc.name}"


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