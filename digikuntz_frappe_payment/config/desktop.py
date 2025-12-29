from frappe import _

def get_data():
    return [
        {
            "module_name": "Digikuntz Frappe Payment",  # Nom court
            "label": _("Digikuntz Payment"),     # Libellé traduisible
            "icon": "fa fa-money",               # Icône Font Awesome
            "type": "module",                    # Type: module
            "category": "Modules",               # Catégorie
            "color": "#e74c3c",                  # Couleur de la carte
            "reverse": 0,                        # 0 ou 1 pour l'effet
            "description": _("Gestion des paiements mobiles"),
            "link": "List/ApiKeys",              # Page par défaut
            "onboard": 0                         # 1 pour afficher sur l'onboarding
        }
    ]