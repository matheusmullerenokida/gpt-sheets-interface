import os
import json
import gspread
import openai
from flask import Flask, render_template, request, redirect
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configurações
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SERVICE_ACCOUNT_INFO = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)

SPREADSHEET_ID = '1m3IV0MQrqwac4O4B_vmuH4cHlYydQ_rO7IyK7x_mAks'
openai.api_key = os.environ["OPENAI_API_KEY"]

# Autenticação
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nova_pergunta = request.form.get("pergunta")
        if nova_pergunta:
            # Chama o GPT direto com system prompt
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",  # ou "gpt-4o-mini" se quiser economizar
                    messages=[
                        {"role": "system", "content": "Você é um assistente útil e objetivo, que responde com clareza."},
                        {"role": "user", "content": nova_pergunta}
                    ],
                    max_tokens=300
                )
                resposta_gerada = response.choices[0].message.content.strip()
            except Exception as e:
                resposta_gerada = f"[ERRO AO CHAMAR GPT: {e}]"

            # Escreve pergunta e resposta na planilha
            sheet.append_row([nova_pergunta, resposta_gerada])
        return redirect("/")

    # Lê perguntas e respostas
    dados = sheet.get_all_values()
    perguntas_respostas = []
    for linha in dados[1:]:  # Ignora cabeçalho
        pergunta = linha[0] if len(linha) > 0 else ""
        resposta = linha[1] if len(linha) > 1 else ""
        perguntas_respostas.append((pergunta, resposta))

    return render_template("index.html", perguntas_respostas=perguntas_respostas)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
