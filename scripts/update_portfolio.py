#!/usr/bin/env python3
"""Atualiza a seção de projetos do README a partir do tópico 'portfolio'."""

import html
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

OWNER = "Erisclecio"
START = "<!-- PORTFOLIO:START -->"
END = "<!-- PORTFOLIO:END -->"
README = Path(__file__).resolve().parents[1] / "README.md"
CAPAS = {
    "ModelagemBarbearia_NAVOR_": (
        "./assets/projeto-modelagem.svg",
        "NAVØR: projeto acadêmico de modelagem de banco de dados",
    ),
    "FrontEnd_NAVOR": (
        "./assets/projeto-web.svg",
        "NAVØR: projeto acadêmico de desenvolvimento web",
    ),
}


def api_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Erisclecio-README-Portfolio",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def obter_repositorios():
    encontrados = []
    pagina = 1
    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&per_page=100&page={pagina}"
        )
        dados = api_json(url)
        if not isinstance(dados, list):
            raise RuntimeError("Resposta inesperada da API do GitHub.")
        for repo in dados:
            nome = repo.get("name", "")
            if (
                repo.get("private")
                or repo.get("owner", {}).get("login", "").lower() != OWNER.lower()
                or nome.lower() == OWNER.lower()
            ):
                continue
            topicos = repo.get("topics")
            if topicos is None:
                url_topicos = f"https://api.github.com/repos/{OWNER}/{quote(nome)}/topics"
                topicos = api_json(url_topicos).get("names", [])
            if "portfolio" in {str(t).lower() for t in topicos}:
                encontrados.append(repo)
        if len(dados) < 100:
            break
        pagina += 1
    prioridades = {"ModelagemBarbearia_NAVOR_": 0, "FrontEnd_NAVOR": 1}
    encontrados.sort(
        key=lambda r: (
            0 if r["name"] in prioridades else 1,
            prioridades.get(r["name"], 0),
            r["name"].lower(),
        )
    )
    return encontrados


def cartao(repo):
    nome = repo["name"]
    url = html.escape(f"https://github.com/{OWNER}/{quote(nome)}", quote=True)
    capa, alt = CAPAS.get(
        nome, ("./assets/projeto-repositorio.svg", "Projeto do portfólio no GitHub")
    )
    imagem = (
        f'<a href="{url}"><img src="{capa}" '
        f'alt="{html.escape(alt, quote=True)}" width="100%" /></a>'
    )
    detalhes = ""
    if nome not in CAPAS:
        descricao = html.escape((repo.get("description") or "Projeto no GitHub").strip())
        linguagem = html.escape(repo.get("language") or "")
        titulo = html.escape(nome)
        detalhes = (
            f'\n      <p><strong><a href="{url}">{titulo}</a></strong></p>'
            f"\n      <p>{descricao}</p>"
        )
        if linguagem:
            detalhes += f"\n      <p><sub>Linguagem principal: {linguagem}</sub></p>"
    return (
        '    <td width="50%" align="center" valign="top">\n'
        f"      {imagem}{detalhes}\n"
        "    </td>"
    )


def renderizar(repos):
    if not repos:
        return (
            "Os projetos públicos selecionados aparecerão aqui quando "
            "receberem o tópico `portfolio` no GitHub."
        )
    linhas = ["<table>"]
    for i in range(0, len(repos), 2):
        linhas.extend(["  <tr>", cartao(repos[i])])
        linhas.append(
            cartao(repos[i + 1]) if i + 1 < len(repos)
            else '    <td width="50%"></td>'
        )
        linhas.append("  </tr>")
    linhas.append("</table>")

    nomes = {r["name"] for r in repos}
    notas = []
    if "ModelagemBarbearia_NAVOR_" in nomes:
        notas.append(
            "**NAVØR — Modelagem de Dados:** trabalho acadêmico em equipe "
            "de análise e documentação de um banco de dados para um futuro ERP."
        )
    if "FrontEnd_NAVOR" in nomes:
        notas.append(
            "**NAVØR — Desenvolvimento Web:** projeto acadêmico em equipe; "
            "minha participação esteve ligada à arquitetura da informação."
        )
        notas.append(
            "**[Visualizar o site](https://erisclecio.github.io/"
            "FrontEnd_NAVOR/html/index.html)**"
        )
    if notas:
        linhas.extend(["", "\n\n".join(notas)])
    return "\n".join(linhas)


def main():
    original = README.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1:
        raise RuntimeError("Marcadores do portfólio ausentes ou duplicados.")
    antes, resto = original.split(START, 1)
    _, depois = resto.split(END, 1)
    atualizado = f"{antes}{START}\n{renderizar(obter_repositorios())}\n{END}{depois}"
    if atualizado == original:
        print("README já está atualizado.")
    else:
        README.write_text(atualizado, encoding="utf-8")
        print("README atualizado.")


if __name__ == "__main__":
    main()
