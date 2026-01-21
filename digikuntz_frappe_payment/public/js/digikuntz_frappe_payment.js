// public/js/accounts_settings.js

// Custom Script pour Accounts Settings - Ajout du bouton CinetPay
frappe.ui.form.on('Accounts Settings', {
    refresh: function(frm) {
        console.log('✅ Script CinetPay chargé pour Accounts Settings');
        
        // Vérifier les permissions
        if (!frappe.user_roles.includes('Accounts Manager') && 
            !frappe.user_roles.includes('System Manager')) {
            return;
        }
        
        // Méthode 1: Ajouter un bouton dans la toolbar
        frm.add_custom_button(__('Configuration CinetPay'), function() {
            frappe.set_route('Form', 'Digikuntz Payment Settings');
        }, __('Paiement'));
        
        // Méthode 2: Ajouter une section HTML personnalisée
        add_digikuntzpayment_section(frm);
    },
    
    
});

function add_digikuntzpayment_section(frm) {
    // Vérifier si la section existe déjà
    if (document.getElementById('digitunzpayment-section')) {
        return;
    }
    
    // Trouver où insérer (après "deferred_accounting" ou à la fin)
    let target = document.querySelector('[data-fieldname="deferred_accounting"]');
    if (!target) {
        target = document.querySelector('.form-section:last-child');
    }
    
    if (target) {
        const sectionHTML = `
            <div id="digitunzpayment-section" class="form-section">
                <div class="section-head">
                    <span class="collapse-indicator mb-1" style="display: none;"></span>
                    <i class="fa fa-credit-card"></i> DigkuntzPay Settings
                </div>
                <div class="section-body">
                    <div class="row">
                        <div class="col-md-8">
                            <p style="margin-bottom: 20px;">
                                Activate online payments via DigikuntzPay. Accept payments
                                Orange Money, MTN Mobile Money, Moov Money and bank cards.
                            </p>
                        </div>
                        <div class="col-md-4 text-right">
                            <button class="btn btn-primary btn-lg" onclick="frappe.set_route('Form', 'DigikuntzPay Setting')"
                                style="margin-top: 10px;">
                                <i class="fa fa-cog"></i> Configure
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insérer après l'élément cible
        target.insertAdjacentHTML('afterend', sectionHTML);
    }
}