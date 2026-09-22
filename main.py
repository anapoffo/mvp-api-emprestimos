"""
API Principal - Empréstimo de Caixas de Documentos

Gerencia o cadastro de caixas-arquivo e o controle de empréstimos dessas
caixas a setores solicitantes. Integra-se a dois outros componentes:

- ViaCEP (serviço externo): valida e completa o endereço do setor
  solicitante a partir do CEP informado.
- API secundária de Temporalidade (serviço interno): calcula, para uma
  caixa, os prazos de guarda e a destinação final com base em seu
  código de classificação.
"""

from datetime import date

from fastapi import FastAPI, HTTPException

from database import get_db, init_db
from models import Caixa, CaixaCreate, CaixaUpdate, Emprestimo, EmprestimoCreate
from clients import (
    CepInvalido,
    ServicoExternoIndisponivel,
    consultar_endereco_por_cep,
    consultar_temporalidade,
    formatar_endereco,
)

app = FastAPI(
    title="API Principal - Empréstimo de Caixas de Documentos",
    description=(
        "Gerencia caixas-arquivo e seus empréstimos, integrando-se ao "
        "ViaCEP (endereço do solicitante) e à API secundária de "
        "Temporalidade (prazos de guarda documental)."
    ),
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------------------
# Caixas
# ---------------------------------------------------------------------

@app.post("/caixas", response_model=Caixa, status_code=201, tags=["Caixas"])
def criar_caixa(caixa: CaixaCreate):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO caixas (codigo_classificacao, descricao, localizacao, data_criacao)
               VALUES (?, ?, ?, ?)""",
            (caixa.codigo_classificacao, caixa.descricao, caixa.localizacao, str(caixa.data_criacao)),
        )
        caixa_id = cursor.lastrowid
    return {**caixa.model_dump(), "id": caixa_id}


@app.get("/caixas", response_model=list[Caixa], tags=["Caixas"])
def listar_caixas():
    with get_db() as conn:
        linhas = conn.execute("SELECT * FROM caixas").fetchall()
    return [dict(linha) for linha in linhas]


@app.get("/caixas/{caixa_id}", response_model=Caixa, tags=["Caixas"])
def obter_caixa(caixa_id: int):
    with get_db() as conn:
        linha = conn.execute("SELECT * FROM caixas WHERE id = ?", (caixa_id,)).fetchone()
    if not linha:
        raise HTTPException(status_code=404, detail="Caixa não encontrada")
    return dict(linha)


@app.put("/caixas/{caixa_id}", response_model=Caixa, tags=["Caixas"])
def atualizar_caixa(caixa_id: int, atualizacao: CaixaUpdate):
    with get_db() as conn:
        atual = conn.execute("SELECT * FROM caixas WHERE id = ?", (caixa_id,)).fetchone()
        if not atual:
            raise HTTPException(status_code=404, detail="Caixa não encontrada")

        dados = dict(atual)
        novos_dados = atualizacao.model_dump(exclude_unset=True)
        for campo, valor in novos_dados.items():
            dados[campo] = str(valor) if isinstance(valor, date) else valor

        conn.execute(
            """UPDATE caixas SET codigo_classificacao = ?, descricao = ?,
               localizacao = ?, data_criacao = ? WHERE id = ?""",
            (dados["codigo_classificacao"], dados["descricao"], dados["localizacao"],
             dados["data_criacao"], caixa_id),
        )
    return dados


@app.delete("/caixas/{caixa_id}", status_code=204, tags=["Caixas"])
def remover_caixa(caixa_id: int):
    with get_db() as conn:
        atual = conn.execute("SELECT * FROM caixas WHERE id = ?", (caixa_id,)).fetchone()
        if not atual:
            raise HTTPException(status_code=404, detail="Caixa não encontrada")
        conn.execute("DELETE FROM caixas WHERE id = ?", (caixa_id,))
    return None


@app.get("/caixas/{caixa_id}/temporalidade", tags=["Caixas"])
def temporalidade_da_caixa(caixa_id: int):
    """Consulta a API secundária para saber os prazos de guarda desta caixa."""
    with get_db() as conn:
        caixa = conn.execute("SELECT * FROM caixas WHERE id = ?", (caixa_id,)).fetchone()
    if not caixa:
        raise HTTPException(status_code=404, detail="Caixa não encontrada")

    try:
        resultado = consultar_temporalidade(caixa["codigo_classificacao"], caixa["data_criacao"])
    except ServicoExternoIndisponivel as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return resultado


# ---------------------------------------------------------------------
# Empréstimos
# ---------------------------------------------------------------------

@app.post("/emprestimos", response_model=Emprestimo, status_code=201, tags=["Empréstimos"])
def criar_emprestimo(emprestimo: EmprestimoCreate):
    with get_db() as conn:
        caixa = conn.execute("SELECT * FROM caixas WHERE id = ?", (emprestimo.caixa_id,)).fetchone()
        if not caixa:
            raise HTTPException(status_code=404, detail="Caixa não encontrada")

        try:
            dados_endereco = consultar_endereco_por_cep(emprestimo.cep_solicitante)
            endereco = formatar_endereco(dados_endereco)
        except CepInvalido as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except ServicoExternoIndisponivel as exc:
            raise HTTPException(status_code=502, detail=str(exc))

        cursor = conn.execute(
            """INSERT INTO emprestimos
               (caixa_id, solicitante, cep_solicitante, endereco_solicitante,
                data_emprestimo, data_devolucao_prevista, data_devolucao_real)
               VALUES (?, ?, ?, ?, ?, ?, NULL)""",
            (emprestimo.caixa_id, emprestimo.solicitante, emprestimo.cep_solicitante,
             endereco, str(emprestimo.data_emprestimo), str(emprestimo.data_devolucao_prevista)),
        )
        emprestimo_id = cursor.lastrowid

    return {
        **emprestimo.model_dump(),
        "id": emprestimo_id,
        "endereco_solicitante": endereco,
        "data_devolucao_real": None,
    }


@app.get("/emprestimos", response_model=list[Emprestimo], tags=["Empréstimos"])
def listar_emprestimos():
    with get_db() as conn:
        linhas = conn.execute("SELECT * FROM emprestimos").fetchall()
    return [dict(linha) for linha in linhas]


@app.get("/emprestimos/{emprestimo_id}", response_model=Emprestimo, tags=["Empréstimos"])
def obter_emprestimo(emprestimo_id: int):
    with get_db() as conn:
        linha = conn.execute("SELECT * FROM emprestimos WHERE id = ?", (emprestimo_id,)).fetchone()
    if not linha:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return dict(linha)


@app.put("/emprestimos/{emprestimo_id}/devolver", response_model=Emprestimo, tags=["Empréstimos"])
def devolver_emprestimo(emprestimo_id: int):
    with get_db() as conn:
        atual = conn.execute("SELECT * FROM emprestimos WHERE id = ?", (emprestimo_id,)).fetchone()
        if not atual:
            raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
        if atual["data_devolucao_real"]:
            raise HTTPException(status_code=409, detail="Empréstimo já foi devolvido")

        hoje = str(date.today())
        conn.execute(
            "UPDATE emprestimos SET data_devolucao_real = ? WHERE id = ?",
            (hoje, emprestimo_id),
        )
        dados = dict(atual)
        dados["data_devolucao_real"] = hoje
    return dados


@app.delete("/emprestimos/{emprestimo_id}", status_code=204, tags=["Empréstimos"])
def cancelar_emprestimo(emprestimo_id: int):
    with get_db() as conn:
        atual = conn.execute("SELECT * FROM emprestimos WHERE id = ?", (emprestimo_id,)).fetchone()
        if not atual:
            raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
        conn.execute("DELETE FROM emprestimos WHERE id = ?", (emprestimo_id,))
    return None
