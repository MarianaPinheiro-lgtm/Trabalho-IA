from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

BACKEND_URL = "http://localhost:8000/mensagem"  # FastAPI
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("📩 Mensagem recebida:", data)

    # ✅ Formato Telegram
    message = data.get("message", {})
    texto = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not texto or not chat_id:
        return jsonify({"status": "no message"}), 200

    telefone = str(chat_id)  # usamos o chat_id no lugar do telefone

    # ── Envia para o FastAPI ────────────────────────────────────────────────────
    try:
        requests.post(
            BACKEND_URL,
            json={"mensagem": texto, "telefone": telefone},
            timeout=30,
        )
    except Exception as e:
        print("Erro ao enviar para backend:", e)

    return jsonify({"status": "ok"}), 200


@app.route("/teste", methods=["GET"])
def teste():
    return "Webhook rodando 🚀"


if __name__ == "__main__":
    app.run(port=5000)
