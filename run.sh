#!/bin/bash

# Расшифровка секретов. Создаст на сервере файл .env из расшифрованного secrets.txt.gpg
gpg --decrypt --quiet --batch --yes --output .env .env.gpg

# Запуск приложения
python bot3.py

# Очистка после запуска (опционально)
rm -f .env
