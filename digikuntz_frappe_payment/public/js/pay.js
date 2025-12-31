class PaymentGateway {
    constructor(invoiceData) {
        this.invoice = invoiceData;
        this.currentMethod = 'card';
        this.stripe = null;
        this.cardElement = null;
        this.init();
    }

    init() {
        this.loadInvoiceData();
        this.updatePaymentSteps();
        this.setupEventListeners();
    }

    setupEventListeners() {
        console.log("PAy button ",document.getElementById('pay-button'))
        document.getElementById('pay-button').addEventListener('click', (e) => {
            e.preventDefault();
            this.processRedirectUrlPayment();
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

    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: this.invoice.currency || 'EUR'
        }).format(amount);
    }

    async processRedirectUrlPayment() {
        this.showLoading();
        
        try {
            const response = await this.sendPaymentToBackend({
                method: 'pay',
                amount: this.invoice.grand_total,
                invoice: this.invoice.name,
                return_url: window.location.origin + '/payment/success',
                cancel_url: window.location.origin + '/payment/cancel'
            });

            // Redirect to pay
            // window.location.href = response.approval_url;
            
        } catch (error) {
            this.showError(error.message);
            this.hideLoading();
        }
    }


    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    async sendPaymentToBackend(paymentData) {
        console.log("paymentData 2", paymentData);
        const response = await fetch('/api/method/digikuntz_frappe_payment.api.generate_payment_link_to_api_gateway', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': csrf_token
            },
            body: JSON.stringify(paymentData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Erreur lors du traitement du paiement');
        }

        console.log("response", response);

        return await response.json();
    }

    showLoading() {
        document.getElementById('loading-overlay').style.display = 'flex';
        document.getElementById('pay-button').disabled = true;
        // document.getElementById('button-loading').style.display = 'inline-block';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
        document.getElementById('pay-button').disabled = false;
        // document.getElementById('button-loading').style.display = 'none';
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
    window.paymentGateway = new PaymentGateway(invoiceData);

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

