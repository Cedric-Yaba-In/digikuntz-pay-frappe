class PaymentGateway {
    constructor(invoiceData) {
        this.invoice = invoiceData;
        this.currentMethod = 'card';
        this.stripe = null;
        this.cardElement = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInvoiceData();
        this.setupStripe();
        this.updatePaymentSteps();
    }

    setupEventListeners() {
        // Method tabs
        document.querySelectorAll('.method-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchPaymentMethod(e.target.dataset.method);
            });
        });

        // Method icons
        document.querySelectorAll('.method-icon').forEach(icon => {
            icon.addEventListener('click', (e) => {
                this.switchPaymentMethod(e.currentTarget.dataset.method);
            });
        });

        // Form submission
        document.getElementById('payment-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.processCardPayment();
        });

        document.getElementById('paypal-button').addEventListener('click', (e) => {
            e.preventDefault();
            this.processPayPalPayment();
        });

        document.getElementById('mobile-money-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.processMobilePayment();
        });

        // Card number formatting
        document.getElementById('card-number').addEventListener('input', (e) => {
            this.formatCardNumber(e.target);
        });

        // Expiry date formatting
        document.getElementById('card-expiry').addEventListener('input', (e) => {
            this.formatExpiryDate(e.target);
        });

        // CVC formatting
        document.getElementById('card-cvc').addEventListener('input', (e) => {
            this.formatCVC(e.target);
        });
    }

    loadInvoiceData() {
        // Populate items table
        const itemsList = document.getElementById('items-list');
        itemsList.innerHTML = '';
        
        this.invoice.items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.item_name || item.description}</td>
                <td>${item.qty}</td>
                <td>${this.formatCurrency(item.rate)}</td>
                <td>${this.formatCurrency(item.amount)}</td>
            `;
            itemsList.appendChild(row);
        });

        // Update amounts
        document.getElementById('subtotal').textContent = this.formatCurrency(this.invoice.net_total);
        document.getElementById('tax').textContent = this.formatCurrency(this.invoice.total_taxes_and_charges);
        document.getElementById('grand-total').textContent = this.formatCurrency(this.invoice.grand_total);
    }

    setupStripe() {
        // Initialize Stripe
        this.stripe = Stripe(this.invoice.stripe_public_key);
        
        // Create card element
        const elements = this.stripe.elements();
        this.cardElement = elements.create('card', {
            style: {
                base: {
                    fontSize: '16px',
                    color: '#32325d',
                    fontFamily: 'Poppins, sans-serif',
                }
            }
        });
        
        // Mount card element
        this.cardElement.mount('#card-element');
    }

    switchPaymentMethod(method) {
        this.currentMethod = method;
        
        // Update tabs
        document.querySelectorAll('.method-tab').forEach(tab => {
            tab.classList.remove('active');
            if(tab.dataset.method === method) {
                tab.classList.add('active');
            }
        });

        // Update method icons
        document.querySelectorAll('.method-icon').forEach(icon => {
            icon.classList.remove('active');
            if(icon.dataset.method === method) {
                icon.classList.add('active');
            }
        });

        // Show corresponding form
        document.querySelectorAll('.payment-method-form').forEach(form => {
            form.classList.remove('active');
        });
        document.getElementById(`${method}-form`).classList.add('active');

        this.updatePaymentSteps();
    }

    updatePaymentSteps() {
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, index) => {
            step.classList.remove('active');
            if(index === 1) { // Payment step
                step.classList.add('active');
            }
        });
    }

    formatCardNumber(input) {
        let value = input.value.replace(/\D/g, '');
        value = value.replace(/(\d{4})/g, '$1 ').trim();
        input.value = value.substring(0, 19);
    }

    formatExpiryDate(input) {
        let value = input.value.replace(/\D/g, '');
        if (value.length >= 2) {
            value = value.substring(0, 2) + '/' + value.substring(2, 4);
        }
        input.value = value.substring(0, 5);
    }

    formatCVC(input) {
        input.value = input.value.replace(/\D/g, '').substring(0, 4);
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: this.invoice.currency || 'EUR'
        }).format(amount);
    }

    async processCardPayment() {
        this.showLoading();
        
        try {
            // Validate form
            if (!this.validateCardForm()) {
                this.hideLoading();
                return;
            }

            // Create payment method
            const { paymentMethod, error } = await this.stripe.createPaymentMethod({
                type: 'card',
                card: this.cardElement,
                billing_details: {
                    name: document.getElementById('card-name').value,
                    email: document.getElementById('email').value
                }
            });

            if (error) {
                throw new Error(error.message);
            }

            // Process payment with backend
            const response = await this.sendPaymentToBackend({
                method: 'card',
                payment_method_id: paymentMethod.id,
                amount: this.invoice.grand_total,
                currency: this.invoice.currency,
                invoice: this.invoice.name
            });

            // Confirm payment
            const { error: confirmError } = await this.stripe.confirmCardPayment(
                response.client_secret
            );

            if (confirmError) {
                throw new Error(confirmError.message);
            }

            // Success
            this.showSuccess(response);
            
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    async processPayPalPayment() {
        this.showLoading();
        
        try {
            const response = await this.sendPaymentToBackend({
                method: 'paypal',
                amount: this.invoice.grand_total,
                currency: this.invoice.currency,
                invoice: this.invoice.name,
                return_url: window.location.origin + '/payment/success',
                cancel_url: window.location.origin + '/payment/cancel'
            });

            // Redirect to PayPal
            window.location.href = response.approval_url;
            
        } catch (error) {
            this.showError(error.message);
            this.hideLoading();
        }
    }

    async processMobilePayment() {
        this.showLoading();
        
        try {
            const provider = document.getElementById('mobile-provider').value;
            const phone = document.getElementById('mobile-number').value;

            if (!phone) {
                throw new Error('Veuillez entrer un numéro de téléphone');
            }

            const response = await this.sendPaymentToBackend({
                method: 'mobile',
                provider: provider,
                phone: phone,
                amount: this.invoice.grand_total,
                currency: this.invoice.currency,
                invoice: this.invoice.name
            });

            this.showNotification('Demande de paiement envoyée ! Vérifiez votre téléphone.', 'success');
            
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    validateCardForm() {
        const cardNumber = document.getElementById('card-number').value;
        const expiry = document.getElementById('card-expiry').value;
        const cvc = document.getElementById('card-cvc').value;
        const name = document.getElementById('card-name').value;
        const email = document.getElementById('email').value;
        const terms = document.getElementById('terms').checked;

        // Basic validation
        if (!cardNumber || cardNumber.replace(/\s/g, '').length < 16) {
            this.showError('Numéro de carte invalide');
            return false;
        }

        if (!expiry || !/^\d{2}\/\d{2}$/.test(expiry)) {
            this.showError('Date d\'expiration invalide (format MM/AA)');
            return false;
        }

        if (!cvc || cvc.length < 3) {
            this.showError('Code CVC invalide');
            return false;
        }

        if (!name) {
            this.showError('Nom sur la carte requis');
            return false;
        }

        if (!email || !this.validateEmail(email)) {
            this.showError('Email invalide');
            return false;
        }

        if (!terms) {
            this.showError('Vous devez accepter les conditions générales');
            return false;
        }

        return true;
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    async sendPaymentToBackend(paymentData) {
        const response = await fetch('/api/method/votre_app.payments.api.process_payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify(paymentData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Erreur lors du traitement du paiement');
        }

        return await response.json();
    }

    showLoading() {
        document.getElementById('loading-overlay').style.display = 'flex';
        document.getElementById('pay-button').disabled = true;
        document.getElementById('button-loading').style.display = 'inline-block';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('pay-button').disabled = false;
        document.getElementById('button-loading').style.display = 'none';
    }

    showNotification(message, type = 'info') {
        const toast = document.getElementById('notification-toast');
        const icon = toast.querySelector('.toast-icon');
        const messageEl = toast.querySelector('.toast-message');

        // Set icon based on type
        icon.className = 'toast-icon';
        switch (type) {
            case 'success':
                icon.classList.add('fas', 'fa-check-circle');
                break;
            case 'error':
                icon.classList.add('fas', 'fa-exclamation-circle');
                break;
            case 'warning':
                icon.classList.add('fas', 'fa-exclamation-triangle');
                break;
            default:
                icon.classList.add('fas', 'fa-info-circle');
        }

        // Set message
        messageEl.textContent = message;

        // Show toast
        toast.className = `toast ${type}`;
        toast.style.display = 'block';

        // Auto hide
        setTimeout(() => {
            toast.style.display = 'none';
        }, 5000);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(response) {
        // Update steps
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, index) => {
            step.classList.remove('active');
            if(index === 2) {
                step.classList.add('active');
            }
        });

        // Show success page or redirect
        setTimeout(() => {
            window.location.href = `/payment/success?payment_id=${response.payment_id}`;
        }, 2000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get invoice data from template or API
    const invoiceData = window.invoiceData || {};
    
    console.log("Invoice Data:", invoiceData);
    // If no data in template, fetch from API
    if (!invoiceData.name && window.invoiceName) {
        fetchInvoiceData(window.invoiceName);
    } else {
        window.paymentGateway = new PaymentGateway(invoiceData);
    }

    // Copy to clipboard functionality
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(() => {
                this.classList.add('copied');
                this.innerHTML = '<i class="fas fa-check"></i> Copié';
                setTimeout(() => {
                    this.classList.remove('copied');
                    this.innerHTML = '<i class="fas fa-copy"></i> Copier';
                }, 2000);
            });
        });
    });
});

async function fetchInvoiceData(invoiceName) {
    try {
        const response = await fetch(`/api/method/votre_app.payments.api.get_invoice?invoice=${invoiceName}`);
        const data = await response.json();
        
        if (data.message) {
            window.paymentGateway = new PaymentGateway(data.message);
        }
    } catch (error) {
        console.error('Error fetching invoice:', error);
        document.getElementById('error-message').textContent = 'Impossible de charger les données de la facture.';
        document.getElementById('error-message').style.display = 'block';
    }
}