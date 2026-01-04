import frappe
import time
import hmac
import hashlib
import base64
from urllib import parse
import requests
from .abstract_gatway import AbstractPaymentApiGateway

class HMACSignature:
    def __init__(self, method, url, params):
        self.method = method
        self.url = url
        self.params = params

    def generate(self, secret):
        signature_raw = hmac.new(secret.encode(), self.get_base_string().encode(), hashlib.sha1).digest()
        return base64.b64encode(signature_raw).decode()

    def get_base_string(self):
        glue = '&'
        #Sort the parameters
        sorted_params = sorted(self.params.items())
        # Construct the parameter string
        parameter_string = "&".join(f"{key}={str(value)}" for key, value in sorted_params)
        #Generate and return the base string
        return f"{self.method.upper()}{glue}{parse.quote(self.url, safe='-')}{glue}{parse.quote(parameter_string, safe='-')}"
    
class EnkapApiGateway(AbstractPaymentApiGateway):
    def __init__(self,ressource_to_pay,customer_data,success_url=None, cancel_url=None):
        self.load_credential_api_gateway()
        self.api_url="https://s3papidoc.smobilpay.maviance.info/v2"
        self.api_version="3.0.0"
        self.debug=True
        self.success_url = success_url
        self.cancel_url = cancel_url
        self.ressource_to_pay = ressource_to_pay
        self.customer_data = customer_data


    def load_credential_api_gateway(self):
        digikuntz_setting = frappe.get_single('DigikuntzPay Setting')
        self.public_key = digikuntz_setting.get("enkap_public_key")
        self.private_key = digikuntz_setting.get("enkap_private_key")
        print("digikuntz_setting", digikuntz_setting.__dict__)
        if not (self.public_key or self.private_key):
            frappe.throw("Enkap API credentials are not configured properly.")

        print("enkap_credentials", self.public_key, self.private_key)

    def get_url_to_redirect(self):
        return self.ping()

    def make_direct_payment(self):
        pass

    def make_payment_by_qrcode(self):
        pass

    def call_back(self):
        pass

    def create_authorization_header(self, method, additional_params=None):
        nonce = str(int(time.time()))
        timestamp = str(int(time.time()))
        parameters = {
            's3pAuth_nonce': nonce,
            's3pAuth_signature_method': "HMAC-SHA1",
            's3pAuth_timestamp': timestamp,
            's3pAuth_token': self.public_key,
            **(additional_params if additional_params else {})
        }
        signature_helper = HMACSignature(method, self.api_url, parameters)
        signature = signature_helper.generate(self.private_key)
        auth_header = (
            f's3pAuth, s3pAuth_nonce="{nonce}", s3pAuth_signature="{signature}", '
            f's3pAuth_signature_method="HMAC-SHA1", s3pAuth_timestamp="{timestamp}", '
            f's3pAuth_token="{self.public_key}"'
        )
        if self.debug:
            print(f"Authorization Header: {auth_header}")
        return auth_header
    
    #for testing
    def ping(self):
        headers = {
            'Authorization': self.create_authorization_header('GET'),
            'x-api-version': self.api_version
        }
        try:
            response = requests.get(f"{self.api_url}/ping", headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                frappe.throw(f"Authentication failed: {response.text}")
                return ("Request could not be authenticated.")
            else:
                frappe.throw(f"Failed to ping: {response.text}")
                return ("An error occurred.")
        except requests.RequestException as e:
            frappe.throw(f"Network error occurred: {str(e)}")
            return (f"Network error occurred: {str(e)}")