#!/bin/bash

# Parar em caso de erro
set -e

# Construir os serviços especificados no docker-compose.yml
echo "Iniciando a construção dos containers e iniciando os servicos..."
docker-compose build

# Iniciar os serviços após a construção
echo "Iniciando os serviços..."
docker-compose up -d

echo "Serviços construídos e iniciados com sucesso."
echo "Acesse o sistema em: http://localhost:8502"
