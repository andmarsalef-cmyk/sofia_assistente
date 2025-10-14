from __future__ import print_function
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scope: solo lectura de correos
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    creds = None
    if os.path.exists("token.json"):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Crear servicio de Gmail
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=5, labelIds=["INBOX"]).execute()
    messages = results.get("messages", [])

    if not messages:
        print("✅ No hay correos en tu inbox.")
    else:
        print("📬 Correos encontrados:")
        for m in messages:
            msg = service.users().messages().get(userId="me", id=m["id"]).execute()
            print("-", msg["snippet"][:80], "...")  # muestra primeras palabras

if __name__ == "__main__":
    main()
