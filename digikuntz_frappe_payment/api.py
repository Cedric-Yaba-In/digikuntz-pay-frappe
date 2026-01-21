    # from digikuntz_frappe_payment.payment_gateway import create_payment_link


import frappe
import json
import digikuntz_frappe_payment.utils.gateway_factory as gateway_factory
import digikuntz_frappe_payment.utils.enum as enum_utils
import digikuntz_frappe_payment.utils.utils_func as utils_func


@frappe.whitelist(allow_guest=True)
def get_doc_of(doctype, data):
    """Fetch a document from the database."""
    return frappe.get_doc(doctype, data)

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
    if not frappe.db.exists("DigikuntzPay Link", {"name": data.get("ref")}):
        throw = frappe.throw("Payment link not found")

    payment_link_doc = frappe.get_doc("DigikuntzPay Link", {"name": data.get("ref")})

    ressource_to_pay = frappe.get_doc(payment_link_doc.type_ressource, payment_link_doc.id_ressource)

    if ressource_to_pay.outstanding_amount <= 0:
        frappe.throw(_("Invoice is already paid"))
    
    if not frappe.db.exists("Customer", ressource_to_pay.customer):
        frappe.throw(_("Customer information is missing in the resource to pay."))

    customer_data =frappe.get_doc("Customer", ressource_to_pay.customer)

    gateway_payment = gateway_factory.load_default_gateway(ressource_to_pay, customer_data, data.get("ref"))

    behavior_for_payment = frappe.db.get_single_value('DigikuntzPay Setting', 'behavior_mode')

    if behavior_for_payment == enum_utils.GatyewayPaymentBehavior.PAYMENT_BY_QRCODE.value: #Comportement lors du paiement par QrCode
        return gateway_payment.make_payment_by_qrcode()
    elif behavior_for_payment == enum_utils.GatyewayPaymentBehavior.DIRECT_PAYMENT_REQUEST.value: #Pour le paiement request
        return gateway_payment.make_direct_payment()
    else: #Dans le cas contraire Redirection URL
        return gateway_payment.get_url_to_redirect()
    
    
   
#Webhook pour le callback de paiement; utiliser pour le payement direct et QR Code
@frappe.whitelist(allow_guest=True,  methods=['GET','POST'])
def payment_callback():
    # /api/method/digikuntz_frappe_payment.api.payment_callback
    request_data = utils_func.get_request_data()

    if not request_data.get("ref"):
        frappe.throw("Payment ref not provided in the callback.")

    #Get the payment link and resource to pay
    payment_link = frappe.get_doc("DigikuntzPay Link", {"name": request_data.get("ref")})
    ressource_to_pay = frappe.get_doc(payment_link.type_ressource, payment_link.id_ressource)

    #if the resource is already paid, no need to process further
    if ressource_to_pay.outstanding_amount <= 0:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = f"{frappe.utils.get_url()}/digikuntzpay/notify_pay?pay_req_status=success&ref={request_data.get('ref')}"
        return
    
    #get customer data and load gateway
    customer_data = frappe.get_doc("Customer", ressource_to_pay.customer)
    gateway_payment = gateway_factory.load_default_gateway(ressource_to_pay, customer_data,request_data.get("ref"))

    #call the callback method of the gateway
    is_paid = gateway_payment.call_back(request_data)

    if is_paid == enum_utils.PaymentRequestStatus.REFUSED.value:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = f"{frappe.utils.get_url()}/digikuntzpay/notify_pay?pay_req_status=cancel&ref={request_data.get('ref')}"
        return
    
    #switch as administrator
    original_user = frappe.session.user
    frappe.set_user("Administrator")


    #mark payment as successful
    payment_entry = mark_payment_as_paid(request_data.get('ref'))

    #send receipts to team and customer
    customer_email = ressource_to_pay.contact_email or frappe.db.get_value("Customer", ressource_to_pay.customer, "email_id")
    send_customer_payment_receipt(payment_entry.name, customer_email)



    send_team_payment_receipt(payment_entry.name)
    
    frappe.set_user(original_user)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = f"{frappe.utils.get_url()}/digikuntzpay/notify_pay?pay_req_status=success&ref={request_data.get('ref')}"

#Methode pour marquer une ressource comme payée
@frappe.whitelist(allow_guest=True)
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

    payment_entry.insert(ignore_permissions=True)
    payment_entry.submit()
    return payment_entry



@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
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


