"""
Camada de acesso ao banco de dados (SQLite) da API principal.

Duas tabelas:
- caixas: unidades físicas de arquivamento (caixas-arquivo)
- emprestimos: registros de empréstimo de uma caixa a um solicitante
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "emprestimos.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS caixas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_classificacao TEXT NOT NULL,
                descricao TEXT NOT NULL,
                localizacao TEXT NOT NULL,
                data_criacao TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caixa_id INTEGER NOT NULL,
                solicitante TEXT NOT NULL,
                cep_solicitante TEXT NOT NULL,
                endereco_solicitante TEXT,
                data_emprestimo TEXT NOT NULL,
                data_devolucao_prevista TEXT NOT NULL,
                data_devolucao_real TEXT,
                FOREIGN KEY (caixa_id) REFERENCES caixas (id)
            )
        """)
