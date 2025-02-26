from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import psycopg2
from environs import Env

env = Env()
env.read_env()

DB_CONNECTION_STRING = env("DB_CONNECTION_STRING")

app = FastAPI()

def get_connection():
    """
    Retorna uma conexão com o banco de dados PostgreSQL.
    """
    return psycopg2.connect(DB_CONNECTION_STRING)


@app.get("/", response_class=HTMLResponse)
def listar_votacoes():
    """
    Mostra uma lista de todas as votações disponíveis.
    E exibe opção para criar uma nova votação.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name FROM polls ORDER BY id;")
        polls = cur.fetchall()  # lista de tuplas (id, name)

    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Votações</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }
            h1 { color: #333; }
            .poll-list { margin: 20px auto; display: inline-block; text-align: left; }
            .poll-item { background: white; margin: 10px 0; padding: 10px; border-radius: 5px; }
            a.button {
                display: inline-block;
                background-color: #28a745;
                color: #fff;
                padding: 8px 12px;
                margin: 5px;
                text-decoration: none;
                border-radius: 5px;
            }
            a.button:hover { background-color: #218838; }
        </style>
    </head>
    <body>
        <h1>Votações Disponíveis</h1>
        <div class="poll-list">
    """

    for poll_id, poll_name in polls:
        html += f"""
            <div class="poll-item">
                <strong>{poll_name}</strong><br>
                <a class="button" href="/poll/{poll_id}">Ver Votação</a>
            </div>
        """

    html += """
        </div>
        <hr>
        <a class="button" href="/create_poll">Criar Nova Votação</a>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/create_poll", response_class=HTMLResponse)
def form_criar_votacao():
    """
    Exibe um formulário para criar uma nova votação (sem opções iniciais).
    """
    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Criar Votação</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; }
            form {
                background: white; padding: 20px; display: inline-block; border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            label, input { display: block; margin: 10px auto; }
            input[type='text'] {
                width: 80%; padding: 8px; border: 1px solid #ccc; border-radius: 5px;
            }
            input[type='submit'] {
                background: #28a745; color: white; padding: 10px 15px;
                border: none; border-radius: 5px; cursor: pointer;
            }
            input[type='submit']:hover { background: #218838; }
        </style>
    </head>
    <body>
        <h1>Criar Nova Votação</h1>
        <form action="/create_poll" method="post">
            <label>Nome da votação: <input type="text" name="poll_name" required></label>
            <input type="submit" value="Criar">
        </form>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.post("/create_poll")
def criar_votacao(poll_name: str = Form(...)):
    """
    Cria a votação no banco de dados (sem opções iniciais).
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO polls (name) VALUES (%s) RETURNING id;", (poll_name,))
        new_id = cur.fetchone()[0]
        conn.commit()

    # Redireciona para a página da votação recém-criada
    return RedirectResponse(url=f"/poll/{new_id}", status_code=303)


@app.get("/poll/{poll_id}", response_class=HTMLResponse)
def ver_votacao(poll_id: int):
    """
    Exibe os detalhes de uma votação específica:
    - Nome da votação
    - Opções existentes + quantidades de votos
    - Formulário para votar (pede nome do votante)
    - Histórico de votos (Fulano votou em Ciclano)
    """
    with get_connection() as conn, conn.cursor() as cur:
        # Verifica se a votação existe
        cur.execute("SELECT id, name FROM polls WHERE id = %s;", (poll_id,))
        poll_row = cur.fetchone()
        if not poll_row:
            raise HTTPException(status_code=404, detail="Votação não encontrada.")

        poll_name = poll_row[1]

        # Carrega as opções e a contagem de votos
        cur.execute("""
            SELECT po.id, po.name, COUNT(pv.id) as total_votos
            FROM poll_options po
            LEFT JOIN poll_votes pv ON po.id = pv.poll_option_id
            WHERE po.poll_id = %s
            GROUP BY po.id, po.name
            ORDER BY po.id;
        """, (poll_id,))
        options = cur.fetchall()  # [(option_id, option_name, total_votos), ...]

        # Carrega o histórico de votos (quem votou em qual opção)
        cur.execute("""
            SELECT pv.voter_name, po.name
            FROM poll_votes pv
            JOIN poll_options po ON pv.poll_option_id = po.id
            WHERE po.poll_id = %s
            ORDER BY pv.id;
        """, (poll_id,))
        votes_history = cur.fetchall()  # [(voter_name, option_name), ...]

    # Monta HTML
    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Votação - {poll_name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center;
            }}
            h1 {{ color: #333; }}
            .container {{
                background: white; padding: 20px; display: inline-block; border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                margin: 20px auto;
            }}
            label, input, select {{ display: block; margin: 10px auto; }}
            input[type='text'] {{
                width: 80%; padding: 8px; border: 1px solid #ccc; border-radius: 5px;
            }}
            input[type='submit'] {{
                background: #28a745; color: white; padding: 10px 15px;
                border: none; border-radius: 5px; cursor: pointer;
            }}
            input[type='submit']:hover {{ background: #218838; }}
            table {{
                margin: 20px auto; border-collapse: collapse;
            }}
            td, th {{
                padding: 8px 12px; border: 1px solid #ccc;
            }}
            .button-link {{
                display: inline-block; padding: 8px 12px; background: #007bff;
                color: white; text-decoration: none; border-radius: 5px;
            }}
            .button-link:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <h1>Votação: {poll_name}</h1>
        <div class="container">
            <h2>Opções e Votos</h2>
            <table>
                <tr><th>Opção</th><th>Total de Votos</th></tr>
    """

    # Lista as opções
    for opt_id, opt_name, total_votos in options:
        html += f"<tr><td>{opt_name}</td><td>{total_votos}</td></tr>"

    # Formulário para votar
    html += """
            </table>
            <hr>
            <h3>Votar</h3>
            <form action="/poll/""" + str(poll_id) + """/vote" method="post">
                <label>Seu Nome: <input type="text" name="voter_name" required></label>
                <label>Escolha uma opção existente:</label>
    """

    for opt_id, opt_name, _ in options:
        html += f"""<input type="radio" name="option_id" value="{opt_id}"> {opt_name}<br>"""

    html += """
                <label>Ou crie nova opção (texto livre): <input type="text" name="new_option"></label>
                <input type="submit" value="Votar">
            </form>
        </div>
    """

    # Histórico de votos
    html += """
        <div class="container">
            <h2>Histórico de Votos</h2>
            <ul>
    """

    if len(votes_history) == 0:
        html += "<li>Ninguém votou ainda.</li>"
    else:
        for voter_name, option_name in votes_history:
            html += f"<li>{voter_name} votou em {option_name}</li>"

    html += """
            </ul>
        </div>
        <br>
        <a class="button-link" href="/">Voltar à lista de votações</a>
    </body>
    </html>
    """

    return HTMLResponse(html)


@app.post("/poll/{poll_id}/vote")
def votar(poll_id: int, voter_name: str = Form(...), option_id: int = Form(None), new_option: str = Form(None)):
    """
    Recebe o voto de um usuário em uma das opções.
    Também permite criar automaticamente uma nova opção e votar nela.
    """
    with get_connection() as conn, conn.cursor() as cur:
        # Verifica se a votação existe
        cur.execute("SELECT id FROM polls WHERE id = %s;", (poll_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Votação não encontrada.")

        # Se o usuário informou uma nova opção, cria essa opção e registra o voto
        if new_option and new_option.strip():
            # Verifica se já existe essa opção
            cur.execute("""
                SELECT id FROM poll_options
                WHERE poll_id = %s AND name ILIKE %s;
            """, (poll_id, new_option))
            row = cur.fetchone()
            if row:
                # Já existe
                new_option_id = row[0]
            else:
                # Cria a opção
                cur.execute(
                    "INSERT INTO poll_options (poll_id, name) VALUES (%s, %s) RETURNING id;",
                    (poll_id, new_option)
                )
                new_option_id = cur.fetchone()[0]

            # Registra o voto
            cur.execute(
                "INSERT INTO poll_votes (poll_option_id, voter_name) VALUES (%s, %s);",
                (new_option_id, voter_name)
            )
        else:
            # Voto numa opção existente
            if option_id is None:
                return HTMLResponse(
                    f"<script>alert('Nenhuma opção selecionada!');window.location.href='/poll/{poll_id}';</script>"
                )

            # Verifica se a opção pertence a essa votação
            cur.execute("SELECT id FROM poll_options WHERE id = %s AND poll_id = %s;", (option_id, poll_id))
            if not cur.fetchone():
                return HTMLResponse(
                    f"<script>alert('Opção inválida para esta votação!');window.location.href='/poll/{poll_id}';</script>"
                )

            # Registra o voto
            cur.execute(
                "INSERT INTO poll_votes (poll_option_id, voter_name) VALUES (%s, %s);",
                (option_id, voter_name)
            )

        conn.commit()

    return RedirectResponse(url=f"/poll/{poll_id}", status_code=303)
