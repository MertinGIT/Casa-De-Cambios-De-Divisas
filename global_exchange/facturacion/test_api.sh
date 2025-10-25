#!/bin/bash

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
API_URL="https://apitest.facturasegura.com.py/misife00/v1/esi"
TOKEN="eyJ2ZXIiOiI1IiwidWlkIjoiMWVlOTRiNmI3MDgyNDBhMDhiY2E5YTgwZWExODJhOTgiLCJzaWQiOjAsImV4cCI6MH0.aPfwVQ.tcnm1XzTnrCnhXyVaOKP9ljPxfo"

RUC_EMISOR="80002247"

echo "=================================="
echo "🧪 TEST API FACTURA SEGURA"
echo "=================================="

# Test 1: Verificar conexión
echo -e "\n${YELLOW}📡 Test 1: Verificar conexión...${NC}"

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authentication-Token: $TOKEN" \
  -d '{
    "operation": "get_estado_sifen",
    "params": {
      "CDC": "01800022475001003000003022024041616519033170",
      "dRucEm": "'$RUC_EMISOR'"
    }
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✅ Conexión exitosa! HTTP $http_code${NC}"
    echo -e "${GREEN}✅ Token válido${NC}"
else
    echo -e "${RED}❌ Error: HTTP $http_code${NC}"
    echo "Response: $body"
fi

# Test 2: Consultar CDC de ejemplo (si tienes uno)
echo -e "\n${YELLOW}🔍 Test 2: Consultar estado de CDC...${NC}"

read -p "¿Tienes un CDC para consultar? (s/n): " tiene_cdc

if [ "$tiene_cdc" = "s" ]; then
    read -p "Ingresa el CDC: " cdc_consultar
    
    curl -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -H "Authentication-Token: $TOKEN" \
      -d '{
        "operation": "get_estado_sifen",
        "params": {
          "CDC": "'$cdc_consultar'",
          "dRucEm": "'$RUC_EMISOR'"
        }
      }' | jq '.'
else
    echo "⏭️  Omitiendo prueba de consulta"
fi

echo -e "\n${GREEN}✅ Tests completados${NC}"