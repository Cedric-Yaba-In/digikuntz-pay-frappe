import frappe
from . import enkap
from . import enum


def load_default_gateway():
    default_gateway = "E-Nkap"

    digikuntz_setting = frappe.get_single('DigikuntzPay Setting')

    # if frappe.db.exists('DigikuntzPay Setting', 'mode_de_paiement_par_défaut'):      
    #     default_gateway = frappe.db.get_single_value('DigikuntzPay Setting', 'mode_de_paiement_par_défaut')
    if  digikuntz_setting.get("mode_de_paiement_par_défaut"):
        default_gateway = digikuntz_setting.get("mode_de_paiement_par_défaut")
    
    #Initiate API Gateway by default gateway
    if default_gateway == enum.GatyewayPaymentType.E_NKAP.value:
        enkapApiGateway = enkap.EnkapApiGateway()
        return enkapApiGateway
    
    return None

