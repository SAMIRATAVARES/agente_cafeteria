import os
import sqlite3
from typing import Dict, Union
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Cafeteria AI - Atendimento")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DB_NAME = "cafeteria.db"


def init_db() -> None:
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
        print(f"Erro no banco: {e}")


init_db()


@app.get("/", response_class=HTMLResponse)
def home():
    """Retorna uma página visual bonita para a cafeteria."""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cafeteria Gourmet - Agente de IA</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f7f3ef; color: #3e2723; margin: 0; padding: 0; }
            header { background-color: #4e342e; color: #fff; text-align: center; padding: 2rem 1rem; }
            h1 { margin: 0; font-size: 2.2rem; }
            p.sub { margin-top: 0.5rem; opacity: 0.9; }
            .container { max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
            .badge { display: inline-block; background-color: #2e7d32; color: white; padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.85rem; margin-top: 1rem; }
            .card { background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
            .card h2 { margin-top: 0; color: #4e342e; font-size: 1.4rem; }
            .btn { display: inline-block; background-color: #d84315; color: white; text-decoration: none; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: bold; margin-top: 0.5rem; }
            .btn:hover { background-color: #bf360c; }
            footer { text-align: center; padding: 2rem; color: #795548; font-size: 0.9rem; }
        </style>
    </head>
    <body>
        <header>
            <h1>☕ Cafeteria Gourmet AI</h1>
            <p class="sub">Sistema de Atendimento Automático e Agente de IA</p>
            <div class="badge">● Sistema Online e Banco SQLite Conectado</div>
        </header>
        <div class="container">
            <div class="card">
                <h2>📋 Painel de Ferramentas Mapeadas</h2>
                <p>As funções da aplicação estão ativas e prontas para consumo pelo Agente de IA:</p>
                <ul>
                    <li><strong>consultar_cardapio(item_id)</strong>: Faz consultas direto no banco SQLite.</li>
                    <li><strong>reservar_mesa_item(item_id, quantidade)</strong>: Atualiza o estoque em tempo real.</li>
                </ul>
            </div>
            <div class="card">
                <h2>🧪 Testar a API Interativa</h2>
                <p>Acesse o painel para testar as buscas de itens e fazer reservas na prática:</p>
                <a href="/docs" class="btn" target="_blank">Abrir Documentação Interativa (/docs)</a>
            </div>
        </div>
        <footer>
            Projeto de Agente de IA • Produção via Render
        </footer>
    </body>
    </html>
    """
    return html_content


@app.get("/cardapio/{item_id}")
def consultar_cardapio(item_id: int) -> Dict[str, Union[str, int, float]]:
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, preco, quantidade_disponivel FROM cardapio WHERE id = ?;",
                (item_id,)
            )
            row = cursor.fetchone()

            if row:
                return {
                    "status": "sucesso",
                    "id": row["id"],
                    "nome": row["nome"],
                    "preco": row["preco"],
                    "quantidade_disponivel": row["quantidade_disponivel"]
                }
            return {"status": "erro", "mensagem": f"Item com ID {item_id} não encontrado."}
    except sqlite3.Error as e:
        return {"status": "erro", "mensagem": str(e)}


@app.post("/reservar/{item_id}")
def reservar_mesa_item(item_id: int, quantidade: int) -> Dict[str, Union[str, int]]:
    if quantidade <= 0:
        return {"status": "erro", "mensagem": "Quantidade deve ser maior que zero."}

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantidade_disponivel FROM cardapio WHERE id = ?;", (item_id,))
            row = cursor.fetchone()

            if not row:
                return {"status": "erro", "mensagem": f"Item {item_id} não encontrado."}

            estoque_atual = row[0]
            if estoque_atual < quantidade:
                return {"status": "erro", "mensagem": f"Estoque insuficiente. Disponível: {estoque_atual}"}

            nova_qtd = estoque_atual - quantidade
            cursor.execute("UPDATE cardapio SET quantidade_disponivel = ? WHERE id = ?;", (nova_qtd, item_id))
            conn.commit()

            return {
                "status": "sucesso",
                "mensagem": f"Reserva de {quantidade} unidade(s) concluída.",
                "quantidade_restante": nova_qtd
            }
    except sqlite3.Error as e:
        return {"status": "erro", "mensagem": str(e)}
