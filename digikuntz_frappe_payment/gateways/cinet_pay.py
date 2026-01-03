import frappe
import time
import hmac
import hashlib
import base64
from urllib import parse
import requests
from .abstract_gatway import AbstractPaymentApiGateway

class CinetPayApiGateway(AbstractPaymentApiGateway):
    def __init__(self, ressource_to_pay,customer_data,return_url=None, notify_url=None):
        self.load_credential_api_gateway()
        self.api_url="https://api-checkout.cinetpay.com/v2"
        # self.api_version="3.0.0"
        self.return_url = return_url
        self.notify_url = notify_url
        self.debug=True
        self.ressource_to_pay = ressource_to_pay
        self.customer_data = customer_data


    def load_credential_api_gateway(self):
        digikuntz_setting = frappe.get_single('DigikuntzPay Setting')
        self.cinetpay_api_key = digikuntz_setting.get("cinetpay_api_key")
        self.private_key = digikuntz_setting.get("cinetpay_private_key")
        self.cinetpay_site_id = digikuntz_setting.get("cinetpay_site_id")

        if not (self.cinetpay_api_key or self.private_key):
            frappe.throw("CinetPay API credentials are not configured properly.")

    def get_url_to_redirect(self):

        payment_data = self.prepare_payment_data()
        url = f"{self.api_url}/payment" 

        requests_response = requests.post(url, data=payment_data)
        if requests_response.status_code != 200:
            frappe.throw(f"Failed to initiate payment: {requests_response.text}")
        response_data = requests_response.json()
        print("CinetPay Response Data:", response_data)  # Debugging line
        return response_data.get("data", {}).get("payment_url")
    

    def make_direct_payment(self):
        pass

    def make_payment_by_qrcode(self):
        pass

    def call_back(self):
        pass

    def prepare_payment_data(self):
        timestamp = int(time.time())
        data = {
            "amount": str(self.ressource_to_pay.outstanding_amount),
            "currency": self.ressource_to_pay.currency,
            "customer_email": self.ressource_to_pay.contact_email,
            "customer_name": self.ressource_to_pay.contact_display,
            "customer_surname": "",
            "customer_phone_number": "",
            "customer_address": "",
            "customer_city": "",
            "customer_country": "",
            "customer_state": "",
            "transaction_id": str(self.ressource_to_pay.doctype)+"-"+str(self.ressource_to_pay.name),
            "site_id": str(self.cinetpay_site_id),
            "apikey": str(self.cinetpay_api_key),
            "return_url": self.return_url,
            "notify_url": self.notify_url,
            "timestamp": str(timestamp),
            "description": f"Payment for {self.ressource_to_pay.doctype} {self.ressource_to_pay.name}",
            "channels": "ALL",
            "lang": self.customer_data.language or "FR",
        }

        # Generate signature
        # signature_string = f"{self.cinetpay_site_id}{data['transaction_id']}{data['amount']}{data['currency']}{timestamp}"
        # signature = hmac.new(
        #     self.private_key.encode('utf-8'),
        #     signature_string.encode('utf-8'),
        #     hashlib.sha256
        # ).hexdigest()

        # data["signature"] = signature

        return data

    