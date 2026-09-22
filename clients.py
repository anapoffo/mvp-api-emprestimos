"""
Clientes para os serviços externos consumidos pela API principal:

- ViaCEP: serviço público gratuito para consulta de endereço a partir do CEP.
  Documentação: https://viacep.com.br/
- API secundária (Temporalidade): serviço interno que calcula prazos de
  guarda documental a partir do código de classificação da caixa.
"""

import os

import httpx

VIACEP_BASE_URL = "https://viacep.com.br/ws"
TEMPORALIDADE_API_URL = os.getenv("TEMPORALIDADE_API_URL", "http://localhost:8001")


class ServicoExternoIndisponivel(Exception):
    pass


class CepInvalido(Exception):
    pass


def consultar_endereco_por_cep(cep: str) -> dict:
    """Consulta o ViaCEP e retorna os dados de endereço. Levanta CepInvalido se o CEP não existir."""
    cep_limpo = "".join(filter(str.isdigit, cep))
    if len(cep_limpo) != 8:
        raise CepInvalido(f"CEP '{cep}' deve conter 8 dígitos")

    url = f"{VIACEP_BASE_URL}/{cep_limpo}/json/"
    try:
        resposta = httpx.get(url, timeout=5.0)
        resposta.raise_for_status()
    except httpx.HTTPError as exc:
        raise ServicoExternoIndisponivel(f"Falha ao consultar ViaCEP: {exc}") from exc

    dados = resposta.json()
    if dados.get("erro"):
        raise CepInvalido(f"CEP '{cep}' não encontrado")

    return dados


def formatar_endereco(dados_viacep: dict) -> str:
    """Monta uma string de endereço legível a partir do retorno do ViaCEP."""
    partes = [
        dados_viacep.get("logradouro"),
        dados_viacep.get("bairro"),
        dados_viacep.get("localidade"),
        dados_viacep.get("uf"),
    ]
    return ", ".join(p for p in partes if p)


def consultar_temporalidade(codigo_classificacao: str, data_criacao: str) -> dict:
    """Chama a API secundária para calcular os prazos de guarda de uma caixa."""
    url = f"{TEMPORALIDADE_API_URL}/temporalidade/calcular"
    try:
        resposta = httpx.post(
            url,
            json={"codigo": codigo_classificacao, "data_criacao": data_criacao},
            timeout=5.0,
        )
        resposta.raise_for_status()
    except httpx.HTTPError as exc:
        raise ServicoExternoIndisponivel(f"Falha ao consultar API de temporalidade: {exc}") from exc

    return resposta.json()
