# Utiliser une image Python officielle et légère
FROM python:3.10-slim

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances du frontend
COPY requirements.txt .

# Installer les bibliothèques nécessaires (nicegui, requests, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source du frontend
COPY src/ ./src/

# Exposer le port sur lequel NiceGUI va écouter
EXPOSE 8080

# Lancer l'application NiceGUI
CMD ["python", "src/ui_main.py"]