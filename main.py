from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# Lista de IPs bloqueados
blocked_ips = {}

def carregar_dados():
    try:
        with open("votacao.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"opcoes": {"Deuses Gregos": [], "Animes": []}, "votos_por_ip": {}}

def salvar_dados(dados):
    with open("votacao.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def bloquear_ip(ip_usuario):
    if ip_usuario in blocked_ips:
        raise HTTPException(status_code=403, detail="Acesso negado.")

@app.get("/", response_class=HTMLResponse)
def formulario_votacao(request: Request):
    bloquear_ip(request.client.host)  # Verifica se o IP está bloqueado
    dados = carregar_dados()
    html = """
    <html>
        <head>
            <meta charset='utf-8'>
            <title>Votação</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }
                h1 { color: #333; }
                form { background: white; padding: 20px; display: inline-block; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
                label, input { display: block; margin: 10px auto; }
                input[type='text'] { width: 80%; padding: 8px; border: 1px solid #ccc; border-radius: 5px; }
                input[type='submit'] { background: #28a745; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; }
                input[type='submit']:hover { background: #218838; }
                ul { list-style: none; padding: 0; }
                li { background: white; margin: 5px auto; padding: 10px; border-radius: 5px; width: 50%; box-shadow: 0 0 5px rgba(0, 0, 0, 0.1); }
            </style>
        </head>
        <body>
            <h1>Vote em uma opção</h1>
            <form action="/votar" method="post">
                <label>Nome: <input type="text" name="nome" required></label>
                <label>Escolha uma opção existente:</label>
    """
    for opcao in dados["opcoes"].keys():
        html += f"<input type='radio' name='opcao' value='{opcao}'> {opcao}<br>"
    
    html += """
                <label>Ou adicione uma nova opção: <input type="text" name="nova_opcao"></label>
                <input type="submit" value="Votar">
            </form>
            <h2>Resultados:</h2>
            <ul>
    """
    for opcao, votos in dados["opcoes"].items():
        html += f"<li>{opcao} - {len(votos)} votos</li>"
    html += "</ul>"
    
    html += "<h2>Votantes:</h2><ul>"
    for opcao, votos in dados["opcoes"].items():
        for votante in votos:
            html += f"<li>{votante} votou em {opcao}</li>"
    html += "</ul>"
    
    html += """
        </body>
    </html>
    """
    return html

@app.post("/votar")
def votar(request: Request, nome: str = Form(...), opcao: str = Form(None), nova_opcao: str = Form(None)):
    bloquear_ip(request.client.host)  # Verifica se o IP está bloqueado
    dados = carregar_dados()
    ip_usuario = request.client.host
    
    if ip_usuario in dados.get("votos_por_ip", {}):
        return HTMLResponse("""<script>alert('Você já votou! Apenas um voto por IP é permitido.');window.location.href='/';</script>""")
    
    if nova_opcao:
        if nova_opcao in dados["opcoes"]:
            return HTMLResponse("""<script>alert('Essa opção já existe!');window.location.href='/';</script>""")
        else:
            dados["opcoes"][nova_opcao] = [nome]
            dados["votos_por_ip"][ip_usuario] = nova_opcao
    else:
        if opcao:
            dados["opcoes"].setdefault(opcao, []).append(nome)
            dados["votos_por_ip"][ip_usuario] = opcao
    
    salvar_dados(dados)
    return HTMLResponse("""<script>window.location.href='/';</script>""")
