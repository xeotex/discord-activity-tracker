# Discord Activity Tracker

Ein Discord-Bot, der Voice-Channel-Aktivität trackt. 
Derzeit im Ausbau zu einem vollständigen Backend-System mit REST-API und asynchroner 
Datenverarbeitung.

## Aktueller Stand

- Discord-Bot, der erfasst, wer wie lange in welchem Voice-Channel war
- Persistente Speicherung in PostgreSQL (läuft lokal via Docker)
- Archivierungslogik für alte Sessions, inklusive Gesamtzeit und Überschneidungsauswertung pro User

## Geplante Erweiterungen

- REST-API mit FastAPI (JWT abgesichert)
- Asynchrone Verarbeitung über Message Queue + Worker
- Dockerisiertes Deployment (Bot, API, Worker, DB gemeinsam)

## Setup

Voraussetzungen: Python 3.14, Docker Desktop
```bash
docker run --name discord-postgres -e POSTGRES_PASSWORD=devpassword -e POSTGRES_DB=discord_tracker -p 5432:5432 -d postgres

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

cd bot
python bot.py
```

Kopiere `.env.example` zu `.env` und trage deine eigenen Werte ein (Discord-Token, DB-Zugangsdaten).




