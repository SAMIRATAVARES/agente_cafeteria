import os
import sqlite3
from typing import Dict, Union

# Busca a chave do Groq que você cadastrou no Render.
# Se estiver rodando no computador sem chave, não dará erro de execução.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DB_NAME = "cafeteria.db"


def init_db() -> None:
    """Inicializa o banco de dados e insere dados de teste se a tabela estiver vazia."""
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
                print("Banco de dados inicializado com sucesso.")
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")


def consultar_cardapio(item_id: int) -> Dict[str, Union[str, int, float]]:
    """Consulta a disponibilidade de um item do cardápio pelo ID."""
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


def reservar_mesa_item(item_id: int, quantidade: int) -> Dict[str, Union[str, int]]:
    """Reserva uma quantidade de um item do cardápio."""
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


if __name__ == "__main__":
    # Inicializa o banco ao rodar o script
    init_db()

    # Confirmação técnica no console
    if GROQ_API_KEY:
        print("Chave do Groq carregada com sucesso!")
    else:
        print("Aviso: Chave GROQ_API_KEY não encontrada nas variáveis de ambiente.")

    # Testes locais das funções
    print(consultar_cardapio(1))
    print(reservar_mesa_item(1, 2))
