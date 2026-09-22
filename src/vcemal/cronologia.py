"""Cronologia de entrada das plataformas por municipio: regras da codificacao (F3).

E o tratamento do V2 e o caminho critico do projeto. O protocolo humano esta em
`docs/protocolo-cronologia-entrada.md`; este modulo carrega o que dele e regra
verificavel -- o esquema da planilha, o que cada codificador pode escrever, como
duas planilhas sao comparadas e como a divergencia e resolvida -- para que a
regra exista num lugar so e seja testavel sem dado. Sem pandas, sem rede.

**O evento e a frota propria, nao o aplicativo** (D-020). A guarda mais
importante daqui e a data-piso por plataforma: uma "entrada" do iFood antes de
janeiro/2018 e marketplace e a validacao recusa a linha em vez de deixar dois
codificadores concordarem sobre o evento errado.

**Desempate e regra, nao conversa** (D-033). `consolidar` aplica as regras na
ordem declarada e devolve o que sobrou para adjudicacao, com o motivo. Nada e
resolvido tirando a media de duas datas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# --- plataformas -----------------------------------------------------------


@dataclass(frozen=True)
class Plataforma:
    codigo: str
    nome: str
    #: Primeiro mes em que a plataforma operou frota propria em qualquer
    #: municipio do Brasil. Entrada codificada antes disso e erro (D-020).
    frota_propria_desde: str
    #: Mes do encerramento nacional, se houve. Vale como saida por padrao em
    #: todo municipio com entrada, salvo evidencia local de saida anterior.
    saida_nacional: str | None = None
    nota: str = ""


PLATAFORMAS: dict[str, Plataforma] = {
    p.codigo: p
    for p in (
        Plataforma(
            "ifood",
            "iFood",
            "2018-01",
            None,
            "marketplace de 2011 a 2017; frota propria a partir de 2018 (D-020)",
        ),
        Plataforma("rappi", "Rappi", "2017-07", None, "frota propria desde a chegada (Sao Paulo)"),
        Plataforma(
            "uber_eats", "Uber Eats", "2016-12", "2022-03", "encerrou a entrega de restaurantes"
        ),
        Plataforma(
            "99food",
            "99Food",
            "2019-11",
            None,
            "estreia em Belo Horizonte; saiu em 2023 (mes a codificar) e voltou em agosto/2025",
        ),
        Plataforma("keeta", "Keeta", "2025-12", None, "Meituan"),
    )
}

EVENTOS = ("entrada", "saida")

#: Graus de confianca. A ordem importa: e a precedencia no desempate.
CONFIANCA = ("A", "B", "C", "D", "N")
ORDEM_CONFIANCA = {g: i for i, g in enumerate(CONFIANCA)}
#: Largura maxima do intervalo `[data_min, data_max]`, em meses, por grau.
LARGURA_MAXIMA = {"A": 0, "B": 0, "C": 6, "D": None}
#: Graus que decidem sozinhos um desempate contra "nao encontrado".
FORTES = ("A", "B")

TIPOS_EVIDENCIA = {
    0: "nenhuma (busca sem resultado)",
    1: "declaracao da plataforma com data (release, blog, pagina de cobertura)",
    2: "imprensa com data e mencao explicita a entregadores da plataforma",
    3: "snapshots (Wayback) ou inferencia por intervalo",
    4: "rede social da plataforma ou grupo de entregadores, com data do post",
    5: "registro administrativo (prefeitura, junta comercial, CNPJ de filial)",
}

COLUNAS = (
    "municipio_ibge",
    "uf",
    "municipio",
    "plataforma",
    "evento",
    "data_min",
    "data_max",
    "tipo_evidencia",
    "confianca",
    "fonte",
    "url",
    "data_acesso",
    "trecho",
    "buscas",
    "observacao",
    "codificador",
)

COLUNAS_DESEMPATE = (
    "municipio_ibge",
    "plataforma",
    "evento",
    "escolha",  # a | b | nenhum | propria
    "data_min",
    "data_max",
    "confianca",
    "justificativa",
    "adjudicador",
)

#: Universo a codificar: municipios com esta populacao ou mais no Censo 2022
#: (1.710 municipios; o iFood atendia 1.638 cidades em marco/2026, D-032).
POPULACAO_MINIMA_UNIVERSO = 20_000

#: Divergencia de data tolerada como concordancia, em meses.
TOLERANCIA_MESES = 1

# --- datas -------------------------------------------------------------------


def mes_indice(aaaa_mm: str) -> int:
    """`AAAA-MM` -> inteiro de meses, para aritmetica. Formato errado e ValueError."""
    s = str(aaaa_mm).strip()
    if len(s) != 7 or s[4] != "-" or not (s[:4] + s[5:]).isdigit():
        raise ValueError(f"data fora do formato AAAA-MM: {aaaa_mm!r}")
    ano, mes = int(s[:4]), int(s[5:])
    if not 1 <= mes <= 12:
        raise ValueError(f"mes invalido: {aaaa_mm!r}")
    return ano * 12 + (mes - 1)


def indice_mes(i: int) -> str:
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def _vazio(v: Any) -> bool:
    return v is None or (isinstance(v, float) and v != v) or str(v).strip() in ("", "nan")


# --- validacao ----------------------------------------------------------------


def validar(linhas: list[dict]) -> None:
    """Regras que uma planilha de codificador precisa obedecer. Erro na primeira linha ruim."""
    if not linhas:
        raise ValueError("planilha vazia")
    chaves: set[tuple] = set()
    for i, r in enumerate(linhas, start=2):
        faltando = [c for c in COLUNAS if c not in r]
        if faltando:
            raise ValueError(f"linha {i}: sem as colunas {faltando}")
        onde = f"linha {i} ({r.get('municipio')}, {r.get('plataforma')})"

        cod = str(r["municipio_ibge"]).strip()
        if not (cod.isdigit() and len(cod) == 7):
            raise ValueError(f"{onde}: municipio_ibge deve ter 7 digitos, veio {cod!r}")
        plat = str(r["plataforma"]).strip()
        if plat not in PLATAFORMAS:
            raise ValueError(f"{onde}: plataforma desconhecida {plat!r}")
        evento = str(r["evento"]).strip()
        if evento not in EVENTOS:
            raise ValueError(f"{onde}: evento deve ser {EVENTOS}, veio {evento!r}")
        grau = str(r["confianca"]).strip()
        if grau not in CONFIANCA:
            raise ValueError(f"{onde}: confianca deve ser {CONFIANCA}, veio {grau!r}")
        if _vazio(r["codificador"]):
            raise ValueError(f"{onde}: sem codificador")

        if grau == "N":
            if evento != "entrada":
                raise ValueError(f"{onde}: 'N' so vale para entrada nao encontrada")
            if not (_vazio(r["data_min"]) and _vazio(r["data_max"])):
                raise ValueError(f"{onde}: 'N' nao pode ter data")
            if _vazio(r["buscas"]):
                raise ValueError(f"{onde}: 'N' exige o registro das buscas feitas")
            if str(r["tipo_evidencia"]).strip() not in ("0", "0.0"):
                raise ValueError(f"{onde}: 'N' exige tipo_evidencia 0")
            chave = (cod, plat, evento, "")
        else:
            for campo in ("fonte", "url", "data_acesso"):
                if _vazio(r[campo]):
                    raise ValueError(f"{onde}: sem {campo}")
            tipo = int(float(r["tipo_evidencia"]))
            if tipo not in TIPOS_EVIDENCIA or tipo == 0:
                raise ValueError(f"{onde}: tipo_evidencia deve ser 1 a 5, veio {tipo}")
            a, b = mes_indice(r["data_min"]), mes_indice(r["data_max"])
            if a > b:
                raise ValueError(f"{onde}: data_min depois de data_max")
            largura = LARGURA_MAXIMA[grau]
            if largura is not None and b - a > largura:
                raise ValueError(
                    f"{onde}: confianca {grau} admite intervalo de ate {largura} meses, "
                    f"veio {b - a}"
                )
            piso = PLATAFORMAS[plat].frota_propria_desde
            if evento == "entrada" and a < mes_indice(piso):
                raise ValueError(
                    f"{onde}: entrada em {r['data_min']} antes da frota propria da "
                    f"{PLATAFORMAS[plat].nome} ({piso}) -- e marketplace, nao tratamento (D-020)"
                )
            chave = (cod, plat, evento, str(r["data_min"]).strip())
        if chave in chaves:
            raise ValueError(f"{onde}: {evento} repetida para a mesma data")
        chaves.add(chave)


# --- comparacao ---------------------------------------------------------------


def _chave(r: dict) -> tuple[str, str, str]:
    return (str(r["municipio_ibge"]).strip(), str(r["plataforma"]).strip(), str(r["evento"]))


def _por_chave(linhas: list[dict]) -> dict[tuple, dict]:
    """Uma linha por (municipio, plataforma, evento): a de data_min mais antiga."""
    saida: dict[tuple, dict] = {}
    for r in linhas:
        k = _chave(r)
        if k not in saida or (
            not _vazio(r["data_min"])
            and (_vazio(saida[k]["data_min"]) or r["data_min"] < saida[k]["data_min"])
        ):
            saida[k] = r
    return saida


def _encontrado(r: dict) -> bool:
    return str(r["confianca"]).strip() != "N"


def _meio(r: dict) -> float:
    return (mes_indice(r["data_min"]) + mes_indice(r["data_max"])) / 2


def concordam(a: dict, b: dict) -> bool:
    """Mesma data a menos de `TOLERANCIA_MESES`, ou intervalos que se cruzam."""
    if _encontrado(a) != _encontrado(b):
        return False
    if not _encontrado(a):
        return True
    a0, a1 = mes_indice(a["data_min"]), mes_indice(a["data_max"])
    b0, b1 = mes_indice(b["data_min"]), mes_indice(b["data_max"])
    if a0 <= b1 and b0 <= a1:
        return True
    return abs(_meio(a) - _meio(b)) <= TOLERANCIA_MESES


def kappa(pares: list[tuple[bool, bool]]) -> float | None:
    """Kappa de Cohen para duas classificacoes binarias. None se nao ha pares."""
    n = len(pares)
    if n == 0:
        return None
    po = sum(1 for x, y in pares if x == y) / n
    pa = sum(1 for x, _ in pares if x) / n
    pb = sum(1 for _, y in pares if y) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def comparar(a: list[dict], b: list[dict]) -> dict:
    """Concordancia entre dois codificadores sobre o mesmo universo.

    Devolve `n_pares`, `kappa_existencia` (encontrou / nao encontrou),
    `pct_data_concordante` (entre os pares em que os dois encontraram) e a lista
    `discordancias`, cada uma com o motivo. Universo diferente e erro: cada
    codificador precisa ter uma linha (ainda que 'N') por municipio x plataforma.
    """
    ka, kb = _por_chave(a), _por_chave(b)
    pares_mp_a = {(k[0], k[1]) for k in ka}
    pares_mp_b = {(k[0], k[1]) for k in kb}
    if pares_mp_a != pares_mp_b:
        so_a = sorted(pares_mp_a - pares_mp_b)[:5]
        so_b = sorted(pares_mp_b - pares_mp_a)[:5]
        raise ValueError(f"universos diferentes: so em A {so_a}; so em B {so_b}")

    existencia: list[tuple[bool, bool]] = []
    datas_ok = datas_total = 0
    discordancias = []
    for k in sorted(set(ka) | set(kb)):
        ra, rb = ka.get(k), kb.get(k)
        if ra is None or rb is None:
            # evento que so um codificou (ex.: saida local): conta como existencia
            existencia.append((ra is not None, rb is not None))
            discordancias.append({"chave": k, "motivo": "evento so em " + ("A" if ra else "B")})
            continue
        ea, eb = _encontrado(ra), _encontrado(rb)
        if k[2] == "entrada":
            existencia.append((ea, eb))
        if ea and eb:
            datas_total += 1
            if concordam(ra, rb):
                datas_ok += 1
            else:
                discordancias.append(
                    {
                        "chave": k,
                        "motivo": "data",
                        "a": f"{ra['data_min']}..{ra['data_max']} ({ra['confianca']})",
                        "b": f"{rb['data_min']}..{rb['data_max']} ({rb['confianca']})",
                    }
                )
        elif ea != eb:
            achou = ra if ea else rb
            discordancias.append(
                {
                    "chave": k,
                    "motivo": "existencia",
                    "encontrou": "A" if ea else "B",
                    "confianca": achou["confianca"],
                }
            )
    return {
        "n_pares": len(existencia),
        "kappa_existencia": kappa(existencia),
        "n_datas": datas_total,
        "pct_data_concordante": (datas_ok / datas_total) if datas_total else None,
        "discordancias": discordancias,
    }


# --- consolidacao -----------------------------------------------------------------


def _melhor(ra: dict, rb: dict) -> dict:
    """Entre dois registros concordantes, o de maior confianca; empate, o de data mais antiga."""
    ga, gb = ORDEM_CONFIANCA[ra["confianca"]], ORDEM_CONFIANCA[rb["confianca"]]
    if ga != gb:
        return ra if ga < gb else rb
    return ra if mes_indice(ra["data_min"]) <= mes_indice(rb["data_min"]) else rb


def _uniao(ra: dict, rb: dict) -> dict:
    r = dict(ra)
    r["data_min"] = indice_mes(min(mes_indice(ra["data_min"]), mes_indice(rb["data_min"])))
    r["data_max"] = indice_mes(max(mes_indice(ra["data_max"]), mes_indice(rb["data_max"])))
    r["confianca"] = "D"
    r["fonte"] = f"A: {ra['fonte']} | B: {rb['fonte']}"
    r["url"] = f"{ra['url']} | {rb['url']}"
    return r


def consolidar(
    a: list[dict], b: list[dict], desempates: list[dict] | None = None
) -> tuple[list[dict], list[dict]]:
    """Aplica as regras de desempate, na ordem, e separa o que exige adjudicacao.

    Devolve `(consolidada, pendentes)`. Cada linha consolidada carrega `regra`;
    cada pendente carrega `motivo` e os dois registros. Regras (D-033):

    R1  os dois encontraram e concordam -> o registro de maior confianca.
    R2  um encontrou, o outro nao -> vale o achado se for A ou B; senao, adjudica.
    R3  os dois encontraram e discordam -> maior confianca vence; empate em A/B
        adjudica; empate em C/D vira a uniao dos intervalos, confianca D.
    R0  adjudicacao registrada em `desempates` vence qualquer regra acima.
    """
    ka, kb = _por_chave(a), _por_chave(b)
    adj = {
        (str(d["municipio_ibge"]), str(d["plataforma"]), str(d["evento"])): d
        for d in desempates or []
    }
    consolidada: list[dict] = []
    pendentes: list[dict] = []

    for k in sorted(set(ka) | set(kb)):
        ra, rb = ka.get(k), kb.get(k)
        if k in adj:
            d = adj[k]
            escolha = str(d["escolha"]).strip()
            if escolha == "nenhum":
                continue
            base = {"a": ra, "b": rb}.get(escolha) or ra or rb
            r = dict(base)
            if escolha == "propria":
                r.update(data_min=d["data_min"], data_max=d["data_max"], confianca=d["confianca"])
            r["regra"] = f"R0-adjudicado:{escolha}"
            r["justificativa"] = d.get("justificativa", "")
            consolidada.append(r)
            continue

        if ra is None or rb is None:
            so = ra or rb
            if _encontrado(so) and so["confianca"] in FORTES:
                consolidada.append({**so, "regra": "R2-so-um-codificou-forte"})
            else:
                pendentes.append(
                    {"chave": k, "motivo": "evento so em um codificador", "a": ra, "b": rb}
                )
            continue

        ea, eb = _encontrado(ra), _encontrado(rb)
        if not ea and not eb:
            consolidada.append({**ra, "regra": "R1-ambos-nao-encontraram"})
        elif ea and eb:
            if concordam(ra, rb):
                consolidada.append({**_melhor(ra, rb), "regra": "R1-concordantes"})
            else:
                ga, gb = ORDEM_CONFIANCA[ra["confianca"]], ORDEM_CONFIANCA[rb["confianca"]]
                if ga != gb:
                    consolidada.append({**(ra if ga < gb else rb), "regra": "R3-maior-confianca"})
                elif ra["confianca"] in FORTES:
                    pendentes.append(
                        {"chave": k, "motivo": "datas fortes discordantes", "a": ra, "b": rb}
                    )
                else:
                    consolidada.append({**_uniao(ra, rb), "regra": "R3-uniao-dos-intervalos"})
        else:
            achou = ra if ea else rb
            if achou["confianca"] in FORTES:
                consolidada.append({**achou, "regra": "R2-evidencia-forte"})
            else:
                pendentes.append(
                    {"chave": k, "motivo": "existencia com evidencia fraca", "a": ra, "b": rb}
                )
    return consolidada, pendentes


# --- tratamento -------------------------------------------------------------------


def tratamento(consolidada: list[dict]) -> list[dict]:
    """Cronologia consolidada -> uma linha por municipio, o tratamento do V2.

    `mes_tratamento` e o `data_max` da entrada mais antiga de qualquer plataforma:
    o primeiro mes em que se tem certeza de frota propria operando. A largura do
    intervalo vai em `incerteza_meses`, para a analise poder excluir os
    municipios mal datados como robustez. `mes_saida_total` e o mes em que a
    ultima plataforma presente saiu, se todas sairam (tratamento reverso).
    """
    por_mun: dict[str, list[dict]] = {}
    for r in consolidada:
        por_mun.setdefault(str(r["municipio_ibge"]), []).append(r)

    saida = []
    for cod, regs in sorted(por_mun.items()):
        entradas = [r for r in regs if r["evento"] == "entrada" and _encontrado(r)]
        saidas = [r for r in regs if r["evento"] == "saida" and _encontrado(r)]
        linha = {
            "municipio_ibge": cod,
            "uf": regs[0]["uf"],
            "municipio": regs[0]["municipio"],
            "tratado": bool(entradas),
            "mes_tratamento": None,
            "incerteza_meses": None,
            "confianca": None,
            "plataformas": "",
            "mes_saida_total": None,
        }
        if entradas:
            primeira = min(
                entradas, key=lambda r: (mes_indice(r["data_max"]), mes_indice(r["data_min"]))
            )
            linha["mes_tratamento"] = primeira["data_max"]
            linha["incerteza_meses"] = mes_indice(primeira["data_max"]) - mes_indice(
                primeira["data_min"]
            )
            linha["confianca"] = primeira["confianca"]
            linha["plataformas"] = "|".join(sorted({r["plataforma"] for r in entradas}))
            presentes = {r["plataforma"] for r in entradas}
            sairam = {r["plataforma"] for r in saidas}
            if presentes and presentes <= sairam:
                linha["mes_saida_total"] = max(
                    r["data_max"] for r in saidas if r["plataforma"] in presentes
                )
        saida.append(linha)
    return saida
