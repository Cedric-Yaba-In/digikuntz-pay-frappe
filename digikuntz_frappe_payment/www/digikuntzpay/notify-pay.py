import frappe 
import datetime
import digikuntz_frappe_payment.api as digikuntzpay_api

@frappe.whitelist(allow_guest=True)
def get_context(context):
    ref = frappe.form_dict.get("ref")

    if not ref:
        context.has_ref = False
        return context
    
    context.has_ref = True
    
    # Si le status a été précisé dans l'URL, on l'utilise pour déterminer si le paiement a réussi
    pay_req_status = frappe.form_dict.get("pay_req_status")
    if pay_req_status and pay_req_status.lower() != "success":
        context.has_paid = False
        return context
    

    payment_link = frappe.get_doc("DigikuntzPay Link", {"name": ref})
    doc = frappe.get_doc(payment_link.type_ressource, payment_link.id_ressource)

    
    context.has_paid = True



    company = frappe.get_doc("Company", doc.company)
    # print(context.company.__dict__)

    context.company = company.company_name
    context.amount = doc.outstanding_amount
    context.currency = doc.currency
    context.description = "" #doc.description
    context.customer_name = doc.customer_name
    context.customer_email = customer_email
    context.docname = doc.name
    context.invoice=doc
    context.year = datetime.datetime.now().year
    context.company_phone = company.phone_no
    context.company_email = company.email



    