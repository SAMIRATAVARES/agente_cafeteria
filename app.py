import os
import sqlite3
from typing import Dict, Union, List
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI(title="Cafeteria Gourmet - Cardápio Online")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DB_NAME = "cafeteria.db"


def init_db() -> None:
    """Cria a tabela e insere os produtos iniciais no banco SQLite."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cardapio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL,
                    quantidade_disponivel INTEGER NOT NULL
                );
            """)
            cursor.execute("SELECT COUNT(*) FROM cardapio;")
            if cursor.fetchone()[0] == 0:
                itens_iniciais = [
                    ("Café Espresso", 6.50, 50),
                    ("Cappuccino Italiano", 12.00, 30),
                    ("Croissant de Almêndoas", 14.50, 15),
                    ("Pão de Queijo Gourmet", 8.00, 40)
                ]
                cursor.executemany(
                    "INSERT INTO cardapio (nome, preco, quantidade_disponivel) VALUES (?, ?, ?);",
                    itens_iniciais
                )
                conn.commit()
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")


init_db()


def obter_todos_itens() -> List[Dict]:
    """Busca todos os itens do cardápio para exibir na interface do usuário."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, preco, quantidade_disponivel FROM cardapio;")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error:
        return []


def executar_reserva(item_id: int, quantidade: int) -> Dict[str, Union[str, int]]:
    """Função interna de reserva acionada pelo usuário."""
    if quantidade <= 0:
        return {"status": "erro", "mensagem": "Informe uma quantidade válida (maior que zero)."}

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantidade_disponivel FROM cardapio WHERE id = ?;", (item_id,))
            row = cursor.fetchone()

            if not row:
                return {"status": "erro", "mensagem": f"Produto ID {item_id} não encontrado."}

            estoque_atual = row[0]
            if estoque_atual < quantidade:
                return {"status": "erro", "mensagem": f"Estoque insuficiente. Disponível no momento: {estoque_atual}"}

            nova_qtd = estoque_atual - quantidade
            cursor.execute("UPDATE cardapio SET quantidade_disponivel = ? WHERE id = ?;", (nova_qtd, item_id))
            conn.commit()

            return {
                "status": "sucesso",
                "mensagem": f"Reserva de {quantidade} unidade(s) confirmada com sucesso!",
                "quantidade_restante": nova_qtd
            }
    except sqlite3.Error as e:
        return {"status": "erro", "mensagem": f"Erro ao processar reserva: {str(e)}"}


@app.get("/", response_class=HTMLResponse)
def interface_usuario(mensagem_reserva: str = ""):
    """Renderiza a aplicação visual para o cliente final consultar e reservar."""
    itens = obter_todos_itens()

    # Monta os cartões dos produtos
    cards_html = ""
    for item in itens:
        status_estoque = f"{item['quantidade_disponivel']} em estoque" if item['quantidade_disponivel'] > 0 else "Esgotado"
        cor_estoque = "#2e7d32" if item['quantidade_disponivel'] > 0 else "#c62828"

        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <span class="item-id">ID #{item['id']}</span>
                <span class="badge" style="background-color: {cor_estoque};">{status_estoque}</span>
            </div>
            <h3>{item['nome']}</h3>
            <p class="preco">R$ {item['preco']:.2f}</p>
            
            <form action="/fazer-reserva" method="post" class="form-reserva">
                <input type="hidden" name="item_id" value="{item['id']}">
                <div class="input-group">
                    <label for="qtd-{item['id']}">Qtd:</label>
                    <input type="number" id="qtd-{item['id']}" name="quantidade" value="1" min="1" max="{item['quantidade_disponivel']}" {"disabled" if item['quantidade_disponivel'] == 0 else ""}>
                </div>
                <button type="submit" class="btn" {"disabled" if item['quantidade_disponivel'] == 0 else ""}>Fazer Reserva</button>
            </form>
        </div>
        """

    alerta_html = f'<div class="alerta">{mensagem_reserva}</div>' if mensagem_reserva else ''

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cafeteria Gourmet - Cardápio & Reservas</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f7f3ef; color: #3e2723; margin: 0; padding: 0; }}
            header {{ background-color: #4e342e; color: #fff; text-align: center; padding: 2.5rem 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.15); }}
            h1 {{ margin: 0; font-size: 2.4rem; }}
            p.sub {{ margin-top: 0.5rem; opacity: 0.9; font-size: 1.1rem; }}
            .container {{ max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
            .alerta {{ background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-weight: bold; text-align: center; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; }}
            .card {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.06); display: flex; flex-direction: column; justify-content: space-between; border: 1px solid #efebe9; }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }}
            .item-id {{ font-size: 0.8rem; color: #8d6e63; font-weight: bold; }}
            .badge {{ color: white; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: bold; }}
            .card h3 {{ margin: 0 0 0.5rem 0; color: #3e2723; font-size: 1.3rem; }}
            .preco {{ font-size: 1.5rem; font-weight: bold; color: #d84315; margin: 0 0 1.2rem 0; }}
            .form-reserva {{ margin-top: auto; }}
            .input-group {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem; }}
            .input-group label {{ font-size: 0.9rem; font-weight: bold; color: #5d4037; }}
            .input-group input {{ width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; }}
            .btn {{ width: 100%; background-color: #6d4c41; color: white; border: none; padding: 0.7rem; border-radius: 6px; font-weight: bold; font-size: 1rem; cursor: pointer; transition: background 0.2s; }}
            .btn:hover {{ background-color: #4e342e; }}
            .btn:disabled {{ background-color: #ccc; cursor: not-allowed; }}
            footer {{ text-align: center; padding: 2.5rem 1rem; color: #8d6e63; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <header>
            <h1>☕ Cafeteria Gourmet</h1>
            <p class="sub">Consulte nosso cardápio e faça sua reserva online</p>
        </header>

        <div class="container">
            {alerta_html}

            <h2 style="color: #4e342e; border-bottom: 2px solid #d7ccc8; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">Cardápio do Dia</h2>

            <div class="grid">
                {cards_html}
            </div>
        </div>

        <footer>
            Cafeteria Gourmet • Sistema de Reservas Integrado ao Banco SQLite
        </footer>
    </body>
    </html>
    """
    return html_content


@app.post("/fazer-reserva", response_class=HTMLResponse)
def processar_reserva_formulario(item_id: int = Form(...), quantidade: int = Form(...)):
    """Recebe o clique do botão 'Fazer Reserva' da tela e atualiza o banco."""
    resultado = executar_reserva(item_id, quantidade)
    mensagem = resultado["mensagem"]
    return interface_usuario(mensagem_reserva=mensagem)
