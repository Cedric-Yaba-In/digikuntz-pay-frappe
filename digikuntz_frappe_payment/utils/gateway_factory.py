import frappe
from ..gateways import enkap, mtn_momo,cinet_pay
from . import enum
from . import constant


def load_default_gateway(ressource_to_pay,customer_data,ref):
    default_gateway = enum.GatyewayPaymentType.E_NKAP.value

    digikuntz_setting = frappe.get_single('DigikuntzPay Setting')

    if  digikuntz_setting.get("mode_de_paiement_par_défaut"):
        default_gateway = digikuntz_setting.get("mode_de_paiement_par_défaut")
    
    #Initiate API Gateway by default gateway
    if default_gateway == enum.GatyewayPaymentType.E_NKAP.value:
        enkapApiGateway = enkap.EnkapApiGateway(ressource_to_pay,customer_data,f"{constant.RETURN_SUCCESS_URL}&ref={ref}",f"{constant.RETURN_CANCEL_URL}&ref={ref}")
        return enkapApiGateway
    elif default_gateway == enum.GatyewayPaymentType.MTN_MOMO.value:
        mtn_momo_gateway = mtn_momo.MTNMoMoGateway(ressource_to_pay,customer_data,f"{constant.RETURN_SUCCESS_URL}&ref={ref}",f"{constant.RETURN_CANCEL_URL}&ref={ref}")
        return mtn_momo_gateway
    elif default_gateway == enum.GatyewayPaymentType.CINET_PAY.value:
        cinet_pay_gateway = cinet_pay.CinetPayApiGateway(ressource_to_pay,customer_data,f"{constant.RETURN_SUCCESS_URL}&ref={ref}",f"{constant.RETURN_CANCEL_URL}&ref={ref}")
        return cinet_pay_gateway

    return None

