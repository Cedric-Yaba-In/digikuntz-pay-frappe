
from enum import Enum


class GatyewayPaymentBehavior(Enum):
    REDIRECTION_URL = "Rédirection URL"
    DIRECT_PAYMENT_REQUEST = "Requête de payment"
    PAYMENT_BY_QRCODE = "Paiement par QRCode"


class GatyewayPaymentType(Enum):
    E_NKAP = "E-Nkap"
    FLUTTERWAVE = "Flutterwave"
    CINET_PAY = "Cinet Pay"
    MTN_MOMO = "MTN MoMo"

class PaymentRequestStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUSED = "CANCELLED"