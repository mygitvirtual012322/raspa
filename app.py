from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import json

app = Flask(__name__, static_folder='.')
CORS(app)

# Credentials (Managed via Env Vars for Security, defaults provided for dev)
CLIENT_ID = os.environ.get("WAYMB_CLIENT_ID", "modderstore_c18577a3")
CLIENT_SECRET = os.environ.get("WAYMB_CLIENT_SECRET", "850304b9-8f36-4b3d-880f-36ed75514cc7")
ACCOUNT_EMAIL = os.environ.get("WAYMB_ACCOUNT_EMAIL", "modderstore@gmail.com")
# Pushcut URL
PUSHCUT_URL = "https://api.pushcut.io/XPTr5Kloj05Rr37Saz0D1/notifications/Pendente%20delivery"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/payment', methods=['POST'])
def create_payment():
    data = request.json
    print(f"\n[DIAGNOSTIC] Incoming Payment Request: {json.dumps(data)}")
    
    try:
        payer = data.get("payer", {})
        method = data.get("method")
        amount = data.get("amount", 9.00)

        # Force valid number types
        try:
            amount = float(amount)
        except:
            amount = 9.0

        # INTELLIGENT SANITIZATION (Strict 9 digits for NIF/Phone)
        if "phone" in payer:
            p = "".join(filter(str.isdigit, str(payer["phone"])))
            if p.startswith("351") and len(p) > 9: p = p[3:]
            if len(p) > 9: p = p[-9:]
            payer["phone"] = p
            print(f"[DIAGNOSTIC] Sanitized Phone: {p}")
            
        if "document" in payer:
            d = "".join(filter(str.isdigit, str(payer["document"])))
            if len(d) > 9: d = d[-9:]
            payer["document"] = d
            print(f"[DIAGNOSTIC] Sanitized NIF: {d}")

        # Construct Payload
        waymb_payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "account_email": ACCOUNT_EMAIL,
            "amount": amount,
            "method": method,
            "currency": "EUR",
            "payer": payer
        }
        
        print(f"[DIAGNOSTIC] Outgoing to WayMB: {json.dumps(waymb_payload)}")

        try:
            r = requests.post("https://api.waymb.com/transactions/create", 
                             json=waymb_payload, 
                             headers={'Content-Type': 'application/json'}, 
                             timeout=30)
            
            status = r.status_code
            raw_text = r.text
            print(f"[DIAGNOSTIC] WayMB Status Code: {status}")
            print(f"[DIAGNOSTIC] WayMB Raw Content: {raw_text}")

            try:
                resp = r.json()
            except:
                resp = {"raw_error": raw_text}
            
            # Check Success
            is_success = False
            if status in [200, 201]:
                # If it's a success status and no explicit "error" key
                if not resp.get("error") and (resp.get('success') == True or resp.get('statusCode') == 200 or 'id' in resp or 'transaction' in resp):
                    is_success = True

            if is_success:
                print("[DIAGNOSTIC] Gateway Success. Triggering Pushcut...")
                try:
                    requests.post(PUSHCUT_URL, json={
                        "text": f"Novo pedido: {amount}€ ({method.upper()})",
                        "title": "Worten Venda"
                    }, timeout=3)
                except Exception as e:
                    print(f"[DIAGNOSTIC] Pushcut Notify Fail: {e}")

                return jsonify({"success": True, "data": resp})
            else:
                print(f"[DIAGNOSTIC] Gateway Rejection detail: {resp}")
                return jsonify({
                    "success": False, 
                    "error": resp.get("error", "Gateway Rejection"),
                    "details": resp
                }), status

        except Exception as e:
            print(f"[DIAGNOSTIC] Inner Exception: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        print(f"[DIAGNOSTIC] Outer Exception: {str(e)}")
        return jsonify({"success": False, "error": "Internal Server Error"}), 500

@app.route('/api/status', methods=['POST'])
def check_status():
    data = request.json
    tx_id = data.get("id")
    try:
        r = requests.post("https://api.waymb.com/transactions/info", json={"id": tx_id}, timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/notify', methods=['POST'])
def send_notification():
    data = request.json
    type = data.get("type", "Pendente delivery")
    text = data.get("text", "Novo pedido")
    title = data.get("title", "Worten")
    
    url = f"https://api.pushcut.io/XPTr5Kloj05Rr37Saz0D1/notifications/{type.replace(' ', '%20')}"
    
    try:
        p_res = requests.post(url, json={"text": text, "title": title}, timeout=5)
        print(f"[Backend] Generic Pushcut ({type}) Response: {p_res.status_code}")
        return jsonify({"success": True})
    except Exception as e:
        print(f"[Backend] Generic Pushcut error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
