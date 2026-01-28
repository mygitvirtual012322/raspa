from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import json
import sys

app = Flask(__name__, static_folder='.')
CORS(app)

# Credentials
CLIENT_ID = os.environ.get("WAYMB_CLIENT_ID", "modderstore_c18577a3")
CLIENT_SECRET = os.environ.get("WAYMB_CLIENT_SECRET", "850304b9-8f36-4b3d-880f-36ed75514cc7")
ACCOUNT_EMAIL = os.environ.get("WAYMB_ACCOUNT_EMAIL", "modderstore@gmail.com")
PUSHCUT_URL = "https://api.pushcut.io/XPTr5Kloj05Rr37Saz0D1/notifications/Pendente%20delivery"

def log(msg):
    print(f"[BACKEND] {msg}")
    sys.stdout.flush()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/payment', methods=['POST'])
def create_payment():
    try:
        data = request.json
        log(f"New Payment Request: {json.dumps(data)}")
        
        payer = data.get("payer", {})
        method = data.get("method")
        amt_raw = data.get("amount", 9)

        # Force Amount Formatting (Int if whole, else float)
        try:
            val = float(amt_raw)
            amount = int(val) if val == int(val) else val
        except:
            amount = 9

        # STRICT SANITIZATION
        if "phone" in payer:
            p = "".join(filter(str.isdigit, str(payer["phone"])))
            if p.startswith("351") and len(p) > 9: p = p[3:]
            if len(p) > 9: p = p[-9:]
            payer["phone"] = p
            log(f"Sanitized Phone: {p}")
            
        if "document" in payer:
            d = "".join(filter(str.isdigit, str(payer["document"])))
            if len(d) > 9: d = d[-9:]
            payer["document"] = d
            log(f"Sanitized NIF: {d}")

        # Construct WayMB Body
        waymb_body = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "account_email": ACCOUNT_EMAIL,
            "amount": amount,
            "method": method,
            "currency": "EUR",
            "payer": payer
        }
        
        log(f"Calling WayMB API with: {json.dumps(waymb_body)}")

        try:
            r = requests.post("https://api.waymb.com/transactions/create", 
                             json=waymb_body, 
                             headers={'Content-Type': 'application/json'}, 
                             timeout=30)
            
            log(f"WayMB Status Code: {r.status_code}")
            log(f"WayMB Raw Response: {r.text}")

            try:
                resp = r.json()
            except:
                resp = {"raw_error": r.text}
            
            # success flags
            is_ok = False
            if r.status_code in [200, 201] and not resp.get("error"):
                is_ok = True

            if is_ok:
                log("Payment Created OK.")
                # Notify Pushcut
                try:
                    requests.post(PUSHCUT_URL, json={
                        "text": f"Pedido: {amount}€ ({method.upper()})",
                        "title": "Worten Promo"
                    }, timeout=3)
                except: pass
                return jsonify({"success": True, "data": resp})
            else:
                log(f"Payment Failed by Gateway: {resp}")
                # Return success: False BUT with details
                return jsonify({
                    "success": False, 
                    "error": resp.get("error", "Gateway Rejection"),
                    "details": resp,
                    "gateway_status": r.status_code
                })

        except Exception as e:
            log(f"Gateway Communication Error: {str(e)}")
            return jsonify({"success": False, "error": f"Erro de comunicação: {str(e)}"}), 502

    except Exception as e:
        log(f"Fatal Route Error: {str(e)}")
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"}), 500

@app.route('/api/status', methods=['POST'])
def check_status():
    data = request.json
    tx_id = data.get("id")
    try:
        r = requests.post("https://api.waymb.com/transactions/info", json={"id": tx_id}, timeout=15)
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
        requests.post(url, json={"text": text, "title": title}, timeout=5)
        return jsonify({"success": True})
    except:
        return jsonify({"success": False}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
