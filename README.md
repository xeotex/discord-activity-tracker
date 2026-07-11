# Discord Activity Tracker

Ein Discord-Bot, der Voice-Channel-Aktivität trackt. 
Derzeit im Ausbau zu einem vollständigen Backend-System mit REST-API und asynchroner 
Datenverarbeitung.

## Aktueller Stand

- Discord-Bot, der erfasst, wer wie lange in welchem Voice-Channel war
- Speicherung in SQLite

## Geplante Erweiterungen

- Migration zu PostgreSQL
- REST-API mit FastAPI (JWT-abgesichert)
- Asynchrone Verarbeitung über Message Queue + Worker
- Dockerisiertes Deployment

## Setup

```bash
cd bot
pip install -r requirements.txt 
python bot.py
```

Erfordert eine `.env`-Datei mit `DISCORD_TOKEN=dein_token`.