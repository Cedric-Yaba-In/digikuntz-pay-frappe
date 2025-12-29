import frappe

def get_context(context):
    ref = frappe.form_dict.get("ref")

    payment_link = frappe.get_doc("DigikuntzPay Link", {"name": ref})
    
    doc = frappe.get_doc(payment_link.type_ressource, payment_link.id_ressource)

    print("Doc link")
    print(doc.__dict__)
    context.company = frappe.get_value("Company", doc.company, "company_name")
    # print(context.company.__dict__)

    context.amount = doc.outstanding_amount
    context.currency = doc.currency
    context.description = "" #doc.description
    context.customer_name = doc.customer_name
    context.customer_email =""  #doc.customer_email
    context.docname = doc.name
    context.invoice=doc