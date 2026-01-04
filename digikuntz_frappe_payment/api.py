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




#Lien de paiement pour la redirection vers la page externe de paiement
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
    
    
   
#Webhook pour le callback de paiement; utiliser pour le payement direct et QR Code
@frappe.whitelist(allow_guest=True)
def payment_callback():
    payment_status = None

    if payment_status:
        payment_handler.on_success_payment(None,None)
    return None

#Methode pour marquer une ressource comme payée
def mark_payment_as_paid(ref):
    payment_link = frappe.get_doc("DigikuntzPay Link", {"name": ref})
    ressource_to_pay = frappe.get_doc(payment_link.type_ressource, payment_link.id_ressource)
    company = frappe.get_doc("Company", ressource_to_pay.company)
    payment_entry = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "posting_date": frappe.utils.nowdate(),
        "party_type": "Customer",
        "party": ressource_to_pay.customer,
        "paid_from": ressource_to_pay.company,
        "paid_amount": ressource_to_pay.outstanding_amount,
        "received_amount": ressource_to_pay.outstanding_amount,
        "reference_no": ressource_to_pay.name,
        "reference_date": frappe.utils.nowdate(),
        "company":ressource_to_pay.company,
        "paid_from" :  company.default_receivable_account,
        "paid_to": company.default_cash_account,
        "references": [{
            "reference_doctype": payment_link.type_ressource,
            "reference_name": payment_link.id_ressource,
            "total_amount": ressource_to_pay.outstanding_amount,
            "outstanding_amount": ressource_to_pay.outstanding_amount,
            "allocated_amount": ressource_to_pay.outstanding_amount
        }]
    })

    payment_entry.insert()
    payment_entry.submit()
    return payment_entry



@frappe.whitelist()
def send_customer_payment_receipt(payment_id, email):
    """Send payment receipt email"""
    payment = frappe.get_doc("Payment Entry", payment_id)
    invoice = frappe.get_doc("Sales Invoice", payment.references[0].reference_name)
    
    # Create PDF receipt
    pdf = frappe.get_print("Payment Entry", payment_id, "Payment Receipt")
    
    # Send email
    frappe.sendmail(
        recipients=[email],
        subject=f"Reçu de paiement - {payment.reference_no}",
        message=frappe.render_template("digikuntz_frappe_payment/templates/emails/customer_payment_receipt.html", {
            "customer_name": payment.party_name,
            "payment_id": payment.reference_no,
            "payment_date": payment.posting_date,
            "invoice_number": invoice.name,
            "amount": f"{payment.paid_amount} {payment.paid_from_account_currency}",
            "payment_method": payment.mode_of_payment,
            "company_name": frappe.defaults.get_global_default("company"),
            "company_email": frappe.defaults.get_global_default("company_email"),
            "company_phone": frappe.defaults.get_global_default("phone"),
            "company_address": frappe.defaults.get_global_default("company_address"),
            # "receipt_url": frappe.get_url(f"/api/method/frappe.utils.print_format.download_pdf?doctype=Payment%20Entry&name={payment_id}&format=Payment%20Receipt&no_letterhead=0")
        }),
        attachments=[{
            "fname": f"receipt_{payment.reference_no}.pdf",
            "fcontent": pdf
        }]
    )
    
    return {"status": "sent"}


@frappe.whitelist()
def send_team_payment_receipt(payment_id):
    """Send payment receipt email"""
    payment = frappe.get_doc("Payment Entry", payment_id)
    invoice = frappe.get_doc("Sales Invoice", payment.references[0].reference_name)
    
    # Create PDF receipt
    pdf = frappe.get_print("Payment Entry", payment_id, "Payment Receipt")
    
    team_emails = frappe.db.get_single_value("Email Account", "email_id")
    
    if not team_emails:
        frappe.log_error("No team email configured for payment notifications")
        return
    
    # Send email
    frappe.sendmail(
        recipients=[team_emails],
        subject=f"Reçu de paiement - {payment.reference_no}",
        message=frappe.render_template("digikuntz_frappe_payment/templates/emails/team_payment_receipt.html", {
            "customer_name": payment.party_name,
            "payment_id": payment.reference_no,
            "payment_date": payment.posting_date,
            "invoice_number": invoice.name,
            "amount": f"{payment.paid_amount} {payment.paid_from_account_currency}",
            "payment_method": payment.mode_of_payment,
            "company_name": frappe.defaults.get_global_default("company"),
            "company_email": frappe.defaults.get_global_default("company_email"),
            "company_phone": frappe.defaults.get_global_default("phone"),
            "company_address": frappe.defaults.get_global_default("company_address"),
            # "receipt_url": frappe.get_url(f"/api/method/frappe.utils.print_format.download_pdf?doctype=Payment%20Entry&name={payment_id}&format=Payment%20Receipt&no_letterhead=0"),
            "current_datetime": frappe.utils.now_datetime()
        }),
        attachments=[{
            "fname": f"receipt_{payment.reference_no}.pdf",
            "fcontent": pdf
        }]
    )
    
    return {"status": "sent"}


