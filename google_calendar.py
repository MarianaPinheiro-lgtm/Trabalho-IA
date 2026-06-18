import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "America/Sao_Paulo"


def autenticar():
    """Autentica e retorna o serviço do Google Calendar."""
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)


def criar_evento_google(
    titulo: str,
    data_iso: str,
    hora: str,
    local: str,
    descricao: str = ""
):
    """
    Cria um evento no Google Calendar.
    data_iso: formato YYYY-MM-DD
    hora: formato HH:MM
    """
    try:
        service = autenticar()

        inicio = datetime.strptime(f"{data_iso} {hora}", "%Y-%m-%d %H:%M")
        fim = inicio + timedelta(hours=1)

        evento = {
            "summary": titulo,
            "location": local,
            "description": descricao or "Evento criado pelo bot Telegram",
            "start": {
                "dateTime": inicio.isoformat(),
                "timeZone": TIMEZONE,
            },
            "end": {
                "dateTime": fim.isoformat(),
                "timeZone": TIMEZONE,
            },
        }

        resultado = service.events().insert(
            calendarId="primary",
            body=evento
        ).execute()

        print(f"Evento criado no Google Calendar: {resultado.get('htmlLink')}")
        return resultado.get("id")

    except Exception as e:
        print(f"Erro ao criar evento no Google Calendar: {e}")
        return None
