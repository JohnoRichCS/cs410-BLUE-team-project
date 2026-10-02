# Faíct

Faíct is an AI-assisted fact-checking application being developed for
ODU CS 411W.

## Current Prototype

The current skeleton supports:

- Text claim submission
- Flask backend processing
- Placeholder AI analysis
- Placeholder evidence retrieval
- Verdict, confidence, explanation, and source display
- SQLite database storage
- Flask-SQLAlchemy ORM

## Technology Stack

- Python
- Flask
- HTML
- Jinja
- Tailwind CSS
- JavaScript
- Flask-SQLAlchemy
- SQLite during development
- PostgreSQL planned if needed
- OpenAI API
- External fact-check/search APIs
- PyTest
- Git/GitHub

## Setup

Create a virtual environment:

python -m venv .venv

Activate it on Windows PowerShell:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\.venv\Scripts\Activate.ps1

Install dependencies:

python -m pip install -r requirements.txt

Run the application:

python app.py

Open:

http://127.0.0.1:5000

## Current Architecture

User Input
→ Flask Route
→ Evidence Retrieval
→ AI Analysis
→ Database
→ Results Page

## Development Status

The AI and evidence retrieval services currently use placeholder data.

These components will be replaced with real API integrations during
development.