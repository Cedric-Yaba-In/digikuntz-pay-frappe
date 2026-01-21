import frappe

def get_request_data():
    """
    Récupère TOUTES les données de la requête, peu importe la méthode ou le format
    """
    data = {}
    
    # 1. Données dans l'URL (query string) - pour GET et POST
    data.update(frappe.form_dict.copy())
    
    # 2. Données dans le body (pour POST, PUT, etc.)
    if frappe.request.method in ['POST', 'PUT', 'PATCH']:
        # A. Essayer de lire comme JSON d'abord
        try:
            raw_data = frappe.request.get_data(as_text=True)
            if raw_data and raw_data.strip():
                json_data = frappe.parse_json(raw_data)
                if isinstance(json_data, dict):
                    data.update(json_data)
        except:
            pass  # Ce n'est pas du JSON valide, essayer autre chose
        
    # 3. Nettoyer les valeurs (convertir 'true'/'false' en booléens)
    for key, value in data.items():
        if isinstance(value, str):
            if value.lower() == 'true':
                data[key] = True
            elif value.lower() == 'false':
                data[key] = False
            elif value.lower() == 'null':
                data[key] = None
    return data