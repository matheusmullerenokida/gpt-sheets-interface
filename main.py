import gspread
from google.oauth2.service_account import Credentials
import openai
import time

# Configurações
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
import json
SERVICE_ACCOUNT_INFO = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
SPREADSHEET_ID = '1m3IV0MQrqwac4O4B_vmuH4cHlYydQ_rO7IyK7x_mAks'
import os
openai.api_key = os.environ["OPENAI_API_KEY"]

# Autenticação

client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

dados = sheet.get_all_values()
contexto = []

for i in range(1, len(dados)):  # Linha 2 em diante
    linha = dados[i]
    pergunta = linha[0] if len(linha) > 0 else ''
    resposta = linha[1] if len(linha) > 1 else ''

    # Verifica reset
    if pergunta.strip() == '--- RESET ---':
        contexto = []  # Zera o contexto
        print(f"🔁 Contexto resetado na linha {i+1}")
        continue

    # Pula se já tiver resposta ou pergunta vazia
    if not pergunta or resposta:
        continue

    # Cria contexto com a pergunta atual
    contexto_completa = contexto + [{"role": "user", "content": pergunta}]

    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=contexto_completa,
            max_tokens=200
        )
        resposta_gerada = completion.choices[0].message.content.strip()
        sheet.update(f'B{i+1}', [[resposta_gerada]])
        print(f"✅ Linha {i+1}: {resposta_gerada}")

        # Atualiza o histórico
        contexto.append({"role": "user", "content": pergunta})
        contexto.append({"role": "assistant", "content": resposta_gerada})
        time.sleep(1.5)
    except Exception as e:
        print(f"❌ Erro na linha {i+1}: {e}")
