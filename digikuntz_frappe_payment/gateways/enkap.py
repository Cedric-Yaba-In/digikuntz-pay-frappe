import frappe
from .abstract_gatway import AbstractPaymentApiGateway

class EnkapApiGateway(AbstractPaymentApiGateway):
    def __init__(self):
        self.load_credential_api_gateway()

    def load_credential_api_gateway(self):
        digikuntz_setting = frappe.get_single('DigikuntzPay Setting')
        self.public_key = digikuntz_setting.get("enkap_public_key")
        self.private_key = digikuntz_setting.get("enkap_private_key")
        print("digikuntz_setting", digikuntz_setting.__dict__)
        if not (self.public_key or self.private_key):
            frappe.throw("Enkap API credentials are not configured properly.")

        print("enkap_credentials", self.public_key, self.private_key)

    def get_url_to_redirect(self):
        pass

    def make_direct_payment(self):
        pass

    def make_payment_by_qrcode(self):
        pass