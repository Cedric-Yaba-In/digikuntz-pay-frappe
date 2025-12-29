function createPaymentLink(data,type) {

    //Call the backend to generate the payment link
    frappe.call({
        method: "digikuntz_frappe_payment.api.generate_payment_link",
        args: {
            "ressource_data_name": data.name,
            "ressource_type": type
        },
        callback: function(r) {
            if(r.message) {
                frappe.msgprint({
                    title: __('Notification'),
                    message: __('Lien de paiement créé <b/><br/>{0}', [r.message]),
                    primary_action: {
                    'label': 'Copier le lien',
                    action: function() {
                         navigator.clipboard.writeText(r.message)
                            .then(function() {
                                frappe.show_alert({ message:__('Lien copié dans le press-papier'), indicator:'green' }, 5);
                            })
                        }
                    }
                });

            } else {
                frappe.msgprint(__('Erreur lors de la création du lien de paiement.'));
            }
        }
    })
}

function attachPaymentButton() {
    frappe.ui.form.on('Sales Invoice', {
        refresh: function(frm) {
            // Vérifier si le bouton existe déjà
            if(frm.custom_buttons && frm.custom_buttons['payer']) {
                return; // Ne pas ajouter en double
            }
            
            if(frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0) {
                frm.add_custom_button(__('💳 Obtenir un lien de paiement'), ()=> createPaymentLink(frm.doc,'Sales Invoice'));
            }
        }
    });
}

attachPaymentButton();

http://erpnext.localhost:8000/digikuntzpay/payment-link/019b69ad-f5e7-7023-b91b-948081294988

console.log("Voir le globale payement button")