# API Principal - Empréstimo de Caixas de Documentos

API REST que gerencia o cadastro de caixas-arquivo e o controle de empréstimos dessas caixas a setores solicitantes, dentro de um sistema de gestão documental arquivística.

O problema que resolve: no ambiente de arquivo físico, não há hoje um sistema digital que registre quem pegou emprestada uma caixa, quando deve devolver, e qual o prazo de guarda documental daquela caixa segundo a legislação arquivística vigente.

Este componente é a API principal de uma arquitetura de 3 serviços independentes:

```mermaid
graph LR
    A[API Principal<br/>Empréstimos] -->|POST /temporalidade/calcular| B[API Secundária<br/>Temporalidade]
    A -->|GET /ws/cep/json| C[ViaCEP<br/>serviço externo]
    A --> D[(SQLite)]
```

- **API Principal** (este repositório): gerencia caixas e empréstimos, persiste em SQLite
- **[API Secundária](https://github.com/anapoffo/mvp-api-temporalidade)**: calcula prazos de guarda documental
- **ViaCEP**: serviço externo público que valida e completa o endereço do solicitante a partir do CEP

## Tecnologias

- Python 3.12 + FastAPI
- SQLite (persistência)
- httpx (comunicação com a API secundária e com o ViaCEP)
- Docker

## API Externa: ViaCEP

- **Link:** https://viacep.com.br
- **Licença/cadastro:** serviço público gratuito, sem necessidade de cadastro ou chave de API
- **Rota utilizada:** `GET https://viacep.com.br/ws/{cep}/json/`
- **Uso:** ao registrar um empréstimo, a API consulta o CEP informado e preenche automaticamente o endereço do setor solicitante, tratando o retorno internamente (não há redirecionamento para outra aplicação)

## Instalação e execução local

```bash
git clone https://github.com/anapoffo/mvp-api-emprestimos.git
cd mvp-api-emprestimos
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Acesse a documentação interativa em `http://localhost:8000/docs`.

> **Importante:** esta API depende da API secundária de temporalidade rodando na porta 8001. Consulte o repositório [mvp-api-temporalidade](https://github.com/anapoffo/mvp-api-temporalidade) para instruções.

## Execução via Docker

```bash
docker compose up --build
```

Sobe a API principal (porta 8000) e a API secundária (porta 8001) juntas, conectadas pela rede interna do Docker.

## Rotas principais

| Método | Rota | Descrição |
|---|---|---|
| POST | `/caixas` | Cadastra uma caixa |
| GET | `/caixas` | Lista todas as caixas |
| GET | `/caixas/{id}` | Consulta uma caixa |
| PUT | `/caixas/{id}` | Atualiza uma caixa |
| DELETE | `/caixas/{id}` | Remove uma caixa |
| GET | `/caixas/{id}/temporalidade` | Consulta prazos de guarda (via API secundária) |
| POST | `/emprestimos` | Registra um empréstimo (consulta ViaCEP) |
| GET | `/emprestimos` | Lista empréstimos |
| GET | `/emprestimos/{id}` | Consulta um empréstimo |
| PUT | `/emprestimos/{id}/devolver` | Marca devolução |
| DELETE | `/emprestimos/{id}` | Cancela um empréstimo |

## Autora

Ana Poffo — Pós-graduação em Engenharia de Software, PUC-Rio
