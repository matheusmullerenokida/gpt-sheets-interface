from flask import Flask, request, render_template_string, redirect
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)

# GPT client (novo estilo openai 1.30+)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Config planilha
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
spreadsheet_id = os.getenv("SPREADSHEET_ID")

# Conexão com Google Sheets
import json
creds = Credentials.from_service_account_info(json.loads(credentials_json), scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(spreadsheet_id).sheet1

# System prompt e histórico
system_prompt = os.getenv("SYSTEM_PROMPT", "Você é um assistente útil.")
historico = [{"role": "system", "content": system_prompt}]

@app.route("/", methods=["GET", "POST"])
def index():
    global historico

    if request.method == "POST":
        pergunta = request.form["pergunta"]

        if pergunta.strip().lower() == "resetar":
            historico = [{"role": "system", "content": system_prompt}]
            return redirect("/")

        historico.append({"role": "user", "content": pergunta})
        try:
            resposta = client.chat.completions.create(
                model="gpt-4o",
                messages=historico,
                max_tokens=300
            ).choices[0].message.content

            historico.append({"role": "assistant", "content": resposta})

            sheet.append_row([datetime.now().isoformat(), pergunta, resposta])

        except Exception as e:
            resposta = f"[ERRO AO CHAMAR GPT: {str(e)}]"

    else:
        resposta = None

    historico_ui = [x for x in historico if x["role"] in ["user", "assistant"]]

    return render_template_string("""
        <h2>GPT + Planilha</h2>
        <form method="post">
            <textarea name="pergunta" rows="3" cols="80" placeholder="Escreva sua pergunta aqui"></textarea><br>
            <button type="submit">Enviar</button>
        </form>
        <form method="post">
            <input type="hidden" name="pergunta" value="resetar" />
            <button type="submit">🔁 Resetar contexto</button>
        </form>
        <hr>
        {% for i in range(0, historico|length, 2) %}
            <b>Você:</b> {{ historico[i].content }}<br>
            <b>GPT:</b> {{ historico[i+1].content if i+1 < historico|length else "" }}<br><hr>
        {% endfor %}
    """, historico=historico_ui, resposta=resposta)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
