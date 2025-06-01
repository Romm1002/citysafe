#!/bin/bash

# Attendre que MySQL soit prêt (max 30 sec)
echo "⏳ Attente que MySQL soit prêt..."
for i in {1..30}; do
  if mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent; then
    echo "✅ MySQL est prêt !"
    break
  fi
  sleep 1
done

# Si MySQL ne répond pas après 30s, on quitte
if ! mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent; then
  echo "❌ Échec de la connexion à MySQL. Abandon."
  exit 1
fi

# Vérifier s'il y a au moins une table (hors ligne d’en-tête)
echo "🔍 Vérification des tables existantes..."
if ! mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" -D"$DB_NAME" -e "SHOW TABLES;" | grep -qv "Tables_in"; then
  echo "📦 Initialisation de la base (aucune table détectée)..."
  python db_init.py
  
  echo "🌱 Insertion des données de seed..."
  python seed_db.py
else
  echo "🆗 Base déjà initialisée, rien à faire."
fi

# 👇 Lancer le serveur backend à la fin
echo "🚀 Lancement du serveur Flask"
exec python app.py
