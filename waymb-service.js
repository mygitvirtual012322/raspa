/**
 * WayMB API Service
 * Encapsulates communication with WayMB Payment Gateway
 */
class WayMBService {
    constructor() {
        this.baseUrl = 'https://api.waymb.com';
        this.clientId = 'modderstore_c18577a3';
        this.clientSecret = '850304b9-8f36-4b3d-880f-36ed75514cc7';
        this.accountEmail = 'modderstore@gmail.com';

        // Pushcut Config
        this.pushcutUrl = 'https://api.pushcut.io/XPTr5Kloj05Rr37Saz0D1/notifications';
    }

    /**
     * Send Pushcut Notification
     * @param {string} type - Notification Name (e.g. 'Pendente delivery')
     * @param {string} message - Custom message to display (e.g. 'Novo pedido: 9€')
     */
    async notifyPushcut(type, message) {
        try {
            // URL Encode the type (handles spaces)
            const url = `${this.pushcutUrl}/${encodeURIComponent(type)}`;
            console.log('Pushcut: Sending...', url);

            const payload = {
                text: message || 'Atualização de Estado',
                title: 'Worten Promo'
            };

            await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            console.log('Pushcut: Sent!');
        } catch (e) {
            console.error('Pushcut Error:', e);
        }
    }

    /**
     * Check Transaction Status (Polling)
     * @param {string} transactionId
     */
    async getTransactionRes(id) {
        try {
            const payload = { id: id };
            const response = await fetch(`${this.baseUrl}/transactions/info`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            return result;
        } catch (error) {
            console.error('WayMB Status Error:', error);
            return null;
        }
    }

    /**
     * Creates a transaction
     * @param {Object} data - Transaction data
     * @param {number} data.amount - Amount in EUR (e.g. 9.00)
     * @param {string} data.method - 'mbway' or 'multibanco'
     * @param {Object} data.payer - { name, document, phone }
     * @returns {Promise<Object>} API Response
     */
    async createTransaction(data) {
        const payload = {
            client_id: this.clientId,
            client_secret: this.clientSecret,
            account_email: this.accountEmail,
            amount: data.amount,
            method: data.method,
            payer: {
                name: data.payer.name,
                document: data.payer.document,
                phone: data.payer.phone
            },
            currency: 'EUR'
        };

        try {
            console.log('WayMB: Creating Transaction...', payload);
            const response = await fetch(`${this.baseUrl}/transactions/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            console.log('WayMB Response:', result);

            if (response.ok && result.statusCode === 200) {
                return { success: true, data: result };
            } else {
                return { success: false, error: result.message || 'Erro deconhecido' };
            }
        } catch (error) {
            console.error('WayMB Error:', error);
            return { success: false, error: 'Erro de conexão com o gateway.' };
        }
    }
}

// Global Instance
window.wayMB = new WayMBService();
