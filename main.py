from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import psycopg2
import requests
import os
import json
from datetime import datetime
from google_calendar import criar_evento_google

from database import (
    init_db as init_eventos_db,
    salvar_evento,
    listar_eventos_do_dia,
    cancelar_evento
)

load_dotenv()

app = FastAPI(title="Bot Telegram - Agenda com IA")

# ─── Clientes ──────────────────────────────────────────────────────────────────

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_URL   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ─── Datas BR / Banco ──────────────────────────────────────────────────────────

def br_para_iso(data_str):
    """
    Aceita datas em formato brasileiro e converte para ISO.
    Ex:
    08/05/2026 -> 2026-05-08
    08-05-2026 -> 2026-05-08
    2026-05-08 -> 2026-05-08
    """

    if not data_str:
        return None

    formatos = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]

    for formato in formatos:
        try:
            return datetime.strptime(data_str, formato).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def iso_para_br(data_str):
    """
    Converte data ISO para formato brasileiro.
    Ex:
    2026-05-08 -> 08/05/2026
    """

    if not data_str:
        return None

    try:
        return datetime.strptime(str(data_str), "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return str(data_str)

# ─── Banco de Dados ─────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def init_mensagens_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id SERIAL PRIMARY KEY,
            telefone TEXT NOT NULL,
            role TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


init_mensagens_db()
init_eventos_db()

# ─── Helpers ────────────────────────────────────────────────────────────────────

def buscar_historico(telefone: str, limite: int = 10) -> list[dict]:
    """Retorna as últimas mensagens do usuário para montar o contexto."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT role, conteudo
        FROM mensagens
        WHERE telefone = %s
        ORDER BY criado_em DESC
        LIMIT %s
        """,
        (telefone, limite),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Inverte para ordem cronológica correta
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def salvar_mensagem(telefone: str, role: str, conteudo: str):
    """Persiste uma mensagem no banco."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO mensagens (telefone, role, conteudo) VALUES (%s, %s, %s)",
        (telefone, role, conteudo),
    )
    conn.commit()
    cur.close()
    conn.close()


def chamar_groq(historico: list[dict], mensagem_nova: str) -> dict:
    """
    Usa a IA para transformar a mensagem do usuário em JSON estruturado.
    """

    messages = [
        {
            "role": "system",
            "content": """
Você é um assistente de agenda para WhatsApp.

Sua tarefa é interpretar a mensagem do usuário e retornar APENAS um JSON válido.

Não escreva explicações.
Não use markdown.
Não use crases.

A data atual para interpretar "hoje", "amanhã", "sexta", etc. é 2026-05-04.

As intenções possíveis são:
- marcar
- consultar
- cancelar
- incompleto
- desconhecido

O JSON deve seguir este formato:

{
  "intencao": "marcar",
  "evento": "reunião",
  "data": "08/05/2026",
  "hora": "14:00",
  "local": "sala 3",
  "mensagem": null
}

Regras:
- Use data no formato brasileiro DD/MM/AAAA.
- Use hora no formato HH:MM.
- Se faltar evento, data, hora ou local para marcar, use intencao "incompleto".
- Para consultar, a data é obrigatória.
- Para cancelar, tente extrair data, hora e local.
- Se faltar informação, coloque null no campo.
- O campo "mensagem" deve explicar o que está faltando quando a intenção for "incompleto".
"""
        },
        *historico,
        {"role": "user", "content": mensagem_nova}
    ]

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=500,
        temperature=0.2
    )

    texto = response.choices[0].message.content.strip()

    try:
        return json.loads(texto)
    except Exception:
        return {
            "intencao": "desconhecido",
            "evento": None,
            "data": None,
            "hora": None,
            "local": None,
            "mensagem": "Não consegui entender sua mensagem. Pode tentar escrever de outro jeito?"
        }


# ─── Respostas ─────────────────────────────────────────────────────────────────

def montar_resposta(dados: dict) -> str:
    intencao = dados.get("intencao")

    evento = dados.get("evento")
    data = dados.get("data")
    hora = dados.get("hora")
    local = dados.get("local")
    
    data_iso = br_para_iso(data)
    data_br = iso_para_br(data_iso) if data_iso else data

    if intencao == "marcar":
        if not evento or not data or not hora or not local:
            return "Para marcar, preciso do evento, data, hora e local."

        if not data_iso:
            return "Não consegui entender a data. Use o formato DD/MM/AAAA, por exemplo: 08/05/2026."

        evento_id = salvar_evento(evento, data_iso, hora, local)

        if evento_id is None:
            return f"Esse horário já está ocupado em {local}. Tente outro horário ou local."

        criar_evento_google(
            titulo=evento,
            data_iso=data_iso,
            hora=hora,
            local=local
        )

        return f"Evento confirmado! {evento} marcado para {data_br} às {hora}, em {local}. 📅"

    

    elif intencao == "consultar":
        if not data:
            return "Qual dia você quer consultar?"

        eventos = listar_eventos_do_dia(data_iso)

        if not eventos:
            return f"Não encontrei eventos confirmados para {data}."

        resposta = f"Eventos confirmados para {data}:\n"

        for e in eventos:
            data_evento_br = iso_para_br(e["data"])
            resposta += f"- {e['hora']} | {e['evento']} | {e['local']}\n"

        return resposta.strip()

    elif intencao == "cancelar":
        if not data or not hora:
            return "Para cancelar, preciso saber a data e o horário do evento."

        if not data_iso:
            return "Não consegui entender a data. Use o formato DD/MM/AAAA, por exemplo: 08/05/2026."

        cancelado = cancelar_evento(data_iso, hora, local)

        if cancelado:
            return f"Evento de {data} às {hora} cancelado com sucesso."

        return "Não encontrei nenhum evento confirmado com essas informações."

    elif intencao == "incompleto":
        return dados.get("mensagem") or "Faltam algumas informações. Me diga evento, data, hora e local."

    else:
        return "Não entendi muito bem. Você quer marcar, consultar ou cancelar um evento?"

def enviar_telegram(chat_id: str, texto: str):
    """Envia a resposta de volta ao Telegram."""
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_BOT_TOKEN não configurado. Pulando envio.")
        return

    url = f"{TELEGRAM_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"Resposta enviada para {chat_id}")
    except Exception as e:
        print(f"Erro ao enviar para Telegram: {e}")

# ─── Modelos Pydantic ───────────────────────────────────────────────────────────

class MensagemEntrada(BaseModel):
    mensagem: str
    telefone: str = "desconhecido"   # número do remetente (ex: 5511999999999)


# ─── Rotas ──────────────────────────────────────────────────────────────────────

@app.post("/mensagem")
async def receber_mensagem(body: MensagemEntrada):
    """
    Rota principal chamada pelo webhook Flask.
    Fluxo: recebe texto → busca histórico → chama Groq → salva → envia Telegram.
    """
    print(f"📨 [{body.telefone}] {body.mensagem}")

    try:
        # 1. Busca histórico do usuário
        historico = buscar_historico(body.telefone)

        # 2. Gera resposta com IA
        dados = chamar_groq(historico, body.mensagem)
        resposta_texto = montar_resposta(dados)

        # 3. Salva no banco
        salvar_mensagem(body.telefone, "user", body.mensagem)
        salvar_mensagem(body.telefone, "assistant", resposta_texto)

        # 4. Envia de volta ao WhatsApp
        enviar_telegram(body.telefone, resposta_texto)

        return {
            "status": "ok",
            "dados_interpretados": dados,
            "resposta": resposta_texto
        }

    except Exception as e:
        print(f"Erro interno: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historico/{telefone}")
async def ver_historico(telefone: str):
    """Rota auxiliar para consultar o histórico de um usuário (útil para debug)."""
    return {"telefone": telefone, "mensagens": buscar_historico(telefone, limite=50)}


@app.get("/health")
async def health():
    """Verificação de saúde da API."""
    return {"status": "online"}


# ─── Inicialização ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
