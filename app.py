import os
import json
import openai
import gspread
from flask import Flask, request, redirect, render_template
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# 🔐 Configurações da API OpenAI
openai.api_key = os.environ["OPENAI_API_KEY"]

# 🔐 Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.environ["SPREADSHEET_ID"]).worksheet("GPT")


# 🧠 Memória de contexto da conversa
contexto = [
    {"role": "system", "content": "Você é um assistente útil e objetivo."}
]

@app.route("/", methods=["GET", "POST"])
def index():
    global contexto

    if request.method == "POST":
        pergunta = request.form["pergunta"]

        if pergunta.strip().lower() == "resetar":
            contexto = [{"role": "system", "content": "Você é um assistente útil e objetivo."}]
            return redirect("/")

        contexto.append({"role": "user", "content": pergunta})

        try:
            resposta = openai.chat.completions.create(
                model="gpt-4o",
                messages=contexto,
                max_tokens=300
            ).choices[0].message.content.strip()

            contexto.append({"role": "assistant", "content": resposta})
            sheet.append_row([pergunta, resposta])

        except Exception as e:
            resposta = f"[ERRO AO CHAMAR GPT: {e}]"
            contexto.append({"role": "assistant", "content": resposta})

        return redirect("/")

    # Carregar últimas interações da planilha (opcional visual)
    historico = sheet.get_all_values()[1:]  # Ignora cabeçalho

    return render_template("index.html", historico=historico)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
