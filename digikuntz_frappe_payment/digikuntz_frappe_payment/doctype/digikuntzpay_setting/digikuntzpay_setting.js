// Copyright (c) 2025, GIC Promote Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("DigikuntzPay Setting", {
	before_save: function (frm) {
        if(frm.doc.mode_de_paiement_par_défaut =="E-Nkap" && (!frm.doc.enkap_public_key || !frm.doc.enkap_private_key))
        {
            frappe.show_alert({ message:__('Clefs d\'API de E-Nkap non définis.'), indicator:'red' });
            frappe.throw(null);
        }
        return true;
    }
});
