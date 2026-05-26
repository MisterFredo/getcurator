# ==============================================================
# 🚀 Ratecard Backend — Dockerfile
# --------------------------------------------------------------
# Version : légère (Python 3.11 slim)
# Objectif : stabilité Render, imports corrects, secret file propre
# ==============================================================

FROM python:3.11-slim

# --------------------------------------------------------------
# 📦 Dépendances système minimale
# --------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------------
# 📁 Répertoire de travail
# --------------------------------------------------------------
WORKDIR /app

# --------------------------------------------------------------
# 📄 Copie du backend (Render enverra uniquement backend/ via rootDir)
# --------------------------------------------------------------
COPY . /app

# --------------------------------------------------------------
# 🐍 Installer dépendances Python
# --------------------------------------------------------------
RUN pip install --upgrade pip
RUN pip install --prefer-binary -r requirements.txt

# --------------------------------------------------------------
# ▶️ Commande de lancement
# --------------------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
