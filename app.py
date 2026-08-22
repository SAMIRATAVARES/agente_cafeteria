import os
import sqlite3
from typing import Dict, Union
from fastapi import FastAPI

# Inicializa o servidor Web
app = FastAPI(title="Agente Cafeteria API")

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


# Inicializa o banco ao subir a aplicação
init_db()


@app.get("/")
def home():
    return {
        "status": "online",
        "mensagem": "API do Agente da Cafeteria está rodando!",
        "groq_key_configurada": bool(GROQ_API_KEY)
    }


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
