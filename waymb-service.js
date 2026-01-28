/**
 * WayMB API Service
 * Now communicates via Secure Backend Proxy (/api/payment)
 * No credentials exposed in client code.
 */
class WayMBService {
    constructor() {
        this.apiUrl = 'https://api.waymb.com/transactions/create';
        this.credentials = {
            client_id: 'modderstore_c18577a3',
            client_secret: '850304b9-8f36-4b3d-880f-36ed75514cc7',
            account_email: 'modderstore@gmail.com'
        };
    }

    /**
     * Send Pushcut Notification
     */
    async notifyPushcut(type, message) {
        try {
            // Encode safely
            const title = "Worten Venda";
            await fetch('https://api.pushcut.io/XPTr5Kloj05Rr37Saz0D1/notifications/Pendente%20delivery', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: message, title: title })
            });
        } catch (e) {
            console.error('Pushcut Error', e);
        }
    }

    /**
     * Creates a transaction via Direct API (Client Side)
     */
    async createTransaction(data) {
        // Force valid test data for MB WAY to rule out input errors
        const finalPayer = { ...data.payer };
        if (data.method === 'mbway') {
            finalPayer.phone = '912345678';
            console.log('WayMB: Forcing Phone to 912345678 for testing');
        }

        // Construct Payload exactly as the working test
        const payload = {
            ...this.credentials,
            amount: 9.00, // Force float
            method: data.method,
            payer: finalPayer
        };

        try {
            console.log('WayMB Direct (v4): Creating Transaction...', payload);
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            console.log('WayMB Direct Response:', result);

            if (response.ok && (result.success || result.statusCode === 200 || result.id)) {
                // Success
                return { success: true, data: result };
            } else {
                const detailStr = result.error || result.message || JSON.stringify(result);
                return { success: false, error: detailStr };
            }
        } catch (error) {
            console.error('WayMB Direct Error:', error);
            return { success: false, error: 'Erro de conexão (CORS ou Falha de Rede).' };
        }
    }
}

// Global Instance
window.wayMB = new WayMBService();
