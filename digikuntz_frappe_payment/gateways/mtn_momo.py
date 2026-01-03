import frappe
import requests
import base64
from .abstract_gatway import AbstractPaymentApiGateway


class MTNMoMoGateway(AbstractPaymentApiGateway):
    def __init__(self,ressource_to_pay,customer_data,return_url=None, notify_url=None):
        self.load_credential_api_gateway()
        self.api_url="https://ericssonbasicapi2.azure-api.net/collection"
        self.api_version="1.0"
        self.ressource_to_pay = ressource_to_pay   
        self.customer_data = customer_data
        self.return_url = return_url
        self.notify_url = notify_url 
        self.debug=True

    def load_credential_api_gateway(self):
        digikuntz_setting = frappe.get_single('DigikuntzPay Setting')
        self.subscription_id = digikuntz_setting.get("mtnmomo_subscription_id")
        self.secondary_key = digikuntz_setting.get("mtnmomo_secondary_key")

        if not (self.subscription_id or self.secondary_key):
            frappe.throw("MTN MoMo API credentials are not configured properly.")


    def get_url_to_redirect(self):
        api_key = self.get_api_key()
        print("Apikey ",api_key)

    def make_direct_payment(self):
        pass

    def make_payment_by_qrcode(self):
        pass

    def call_back(self):
        pass

    def get_api_key(self):
        str_api = f"{self.subscription_id}:{self.secondary_key}"
        print("Getting API Key... ", self.subscription_id, self.secondary_key, f'Basic: {base64.b64encode(str_api.encode())}')

        response = requests.post(f"{self.api_url}/token", headers={
            'Authorization': f'Basic {base64.b64encode(str_api.encode())}',
            'Ocp-Apim-Subscription-Key': self.subscription_id})
        if response.status_code != 200:
            frappe.throw(f"Failed to get API key: {response.text}")
        return response.json()