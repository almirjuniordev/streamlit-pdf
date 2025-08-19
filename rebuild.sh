#!/bin/bash

# Parar em caso de erro
set -e

# Derrubar os serviços atuais, remover volumes desanexados
echo "Derrubando os serviços atuais..."
docker-compose down --volumes --remove-orphans

# Reconstruir e iniciar os serviços
echo "Reconstruindo e iniciando os serviços..."
docker-compose up --build -d

echo "Serviços reconstruídos e iniciados com sucesso."
echo "Acesse o sistema em: http://localhost:8502"
