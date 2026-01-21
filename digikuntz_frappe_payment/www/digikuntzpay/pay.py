import frappe
import datetime
import time

def get_context(context):
    ref = frappe.form_dict.get("ref")
    
    if not ref:
        context.has_ref = False
        return context
    
    context.has_ref = True
    context.ref=ref

    payment_link = frappe.get_doc("DigikuntzPay Link", {"name": ref})
    
    print("Payment Link Doc ",payment_link)

    doc = frappe.get_doc(payment_link.type_ressource, payment_link.id_ressource)

    if doc.outstanding_amount <= 0:
        context.has_paid = True
        return context

    context.has_paid = False

    company = frappe.get_doc("Company", doc.company)
    # print(context.company.__dict__)

    context.company = company.company_name
    context.amount = doc.outstanding_amount
    context.currency = doc.currency
    context.description = "" #doc.description
    context.customer_name = doc.customer_name
    context.customer_email = doc.contact_email or frappe.db.get_value("Customer", doc.customer, "email_id")
    context.docname = doc.name
    context.invoice=doc
    context.year = datetime.datetime.now().year
    context.company_phone = company.phone_no
    # context.company_address = company.company_address   
    context.company_email = company.email
    context.version = time.time()
    context.csrf_token = frappe.sessions.get_csrf_token()
    