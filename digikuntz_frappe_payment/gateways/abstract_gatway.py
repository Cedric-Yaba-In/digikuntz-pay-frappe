from abc import ABC, abstractmethod
class AbstractPaymentApiGateway(ABC):

    @abstractmethod
    def get_url_to_redirect(self):
        pass

    @abstractmethod
    def make_direct_payment(self):
        pass

    @abstractmethod
    def make_payment_by_qrcode(self):
        pass

    @abstractmethod
    def call_back(self):
        pass
    
    @abstractmethod
    def load_credential_api_gateway(self):
        pass