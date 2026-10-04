"""Da lista de cidades nos snapshots ao intervalo de entrada por municipio (F3, tipo 3).

Tres passos, todos sem rede:

1. **Itens.** O HTML vira uma sequencia de itens curtos de texto (um `<li>`, um
   `<option>`, uma celula, um pedaco de paragrafo separado por virgula). Nao se
   supoe o layout da pagina, que muda entre os anos: supoe-se so que cada
   cidade aparece como item proprio, com ou sem a UF ao lado.
2. **Casamento.** Um item casa com um municipio do universo quando o texto
   **inteiro** do item, normalizado, e o nome do municipio -- nunca por
   substring, senao "Serra" casaria em "Serra Talhada" e "Natal" em qualquer
   aviso de feriado. A UF vem do proprio item (`Palmas - TO`, `Palmas/TO`,
   `Palmas (TO)`) ou do ultimo titulo de estado visto antes dele. Nome que
   existe em duas UFs do universo e fica sem UF (31 casos, de Palmas a
   Cascavel) **nao casa**: vai para o relatorio de ambiguos, nunca para o
   municipio errado (a mesma regra de D-014).
3. **Intervalo.** Para cada municipio, o ultimo snapshot legivel sem ele e o
   primeiro com ele dao `[data_min, data_max]`, como a secao 3 do protocolo
   manda. Snapshot que nao traz lista legivel (pagina carregada por
   JavaScript, erro, redesenho) e **excluido**, nao lido como "nenhuma cidade":
   ausencia so conta onde a lista existe.

O que sai e insumo dos codificadores (passo 1 do roteiro de busca, secao 4),
no esquema da planilha e aprovado por `vcemal.cronologia.validar`, com
`codificador = "W"`. Nao e uma terceira codificacao: o intervalo do Wayback e
largo por construcao e a busca municipio a municipio existe para aperta-lo.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser

from vcemal.cronologia import PLATAFORMAS, indice_mes, mes_indice
from vcemal.municipios import normalizar

UFS: dict[str, str] = {
    "AC": "ACRE",
    "AL": "ALAGOAS",
    "AP": "AMAPA",
    "AM": "AMAZONAS",
    "BA": "BAHIA",
    "CE": "CEARA",
    "DF": "DISTRITO FEDERAL",
    "ES": "ESPIRITO SANTO",
    "GO": "GOIAS",
    "MA": "MARANHAO",
    "MT": "MATO GROSSO",
    "MS": "MATO GROSSO DO SUL",
    "MG": "MINAS GERAIS",
    "PA": "PARA",
    "PB": "PARAIBA",
    "PR": "PARANA",
    "PE": "PERNAMBUCO",
    "PI": "PIAUI",
    "RJ": "RIO DE JANEIRO",
    "RN": "RIO GRANDE DO NORTE",
    "RS": "RIO GRANDE DO SUL",
    "RO": "RONDONIA",
    "RR": "RORAIMA",
    "SC": "SANTA CATARINA",
    "SP": "SAO PAULO",
    "SE": "SERGIPE",
    "TO": "TOCANTINS",
}
_UF_POR_NOME = {nome: sigla for sigla, nome in UFS.items()}

#: Snapshot com menos cidades casadas que isto nao tem lista legivel e e
#: excluido do calculo de intervalo. A primeira lista publicada ja passava de
#: 500 cidades (Prosus, FY2019); 20 separa "lista" de "texto solto".
MINIMO_CIDADES = 20

#: Item mais longo que isto e paragrafo, nao nome de cidade.
TAMANHO_MAXIMO_ITEM = 60

CODIFICADOR = "W"
TIPO_EVIDENCIA = 3

_IGNORAR = {"script", "style", "noscript", "template", "head", "title"}
_SUFIXO_UF = re.compile(r"^(?P<nome>.+?)\s*(?:[-–/,]\s*|\()(?P<uf>[A-Za-z]{2})\)?\s*$")
_SEPARADORES = re.compile(r"[,;|•\n]+")
_D_APOSTROFO = re.compile(r"\bD (?=[AEIOU])")

#: Grafia da lista -> grafia do IBGE, ja normalizadas. Revisado a mao, como os
#: `APELIDOS` de `vcemal.municipios`: nada de fuzzy match.
GRAFIAS: dict[str, str] = {
    "ACU": "ASSU",  # RN; a lista de 2019 escreve Acu, o IBGE Assu
}


def _chave(nome: str) -> str:
    """Nome normalizado para casar lista com universo.

    Alem de `normalizar`, cola o "d'" do apostrofo ("D OESTE" -> "DOESTE"), porque
    a lista escreve "Santa Barbara Doeste" e "Dias Davila", e aplica `GRAFIAS`.
    Fica aqui e nao em `normalizar`, que os `APELIDOS` do Senatran usam.
    """
    chave = _D_APOSTROFO.sub("D", normalizar(nome))
    return GRAFIAS.get(chave, chave)


class _Textos(HTMLParser):
    """Nos de texto do HTML, na ordem, fora de script e estilo."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.textos: list[str] = []
        self._ignorando = 0

    def handle_starttag(self, tag, attrs):
        if tag in _IGNORAR:
            self._ignorando += 1

    def handle_endtag(self, tag):
        if tag in _IGNORAR and self._ignorando:
            self._ignorando -= 1

    def handle_data(self, data):
        if not self._ignorando and data.strip():
            self.textos.append(data)


def itens(html: str) -> list[str]:
    """Itens curtos de texto, na ordem da pagina."""
    p = _Textos()
    p.feed(html)
    saida = []
    for texto in p.textos:
        texto = texto.strip()
        # "Sao Paulo, SP" e um item so; "Curitiba, Londrina, Maringa" sao tres.
        if _SUFIXO_UF.match(texto) and texto.count(",") == 1 and "\n" not in texto:
            pedacos = [texto]
        else:
            pedacos = _SEPARADORES.split(texto)
        saida.extend(s for s in (x.strip() for x in pedacos) if s)
    return [s for s in saida if len(s) <= TAMANHO_MAXIMO_ITEM]


def _separar_uf(item: str) -> tuple[str, str | None]:
    """`Palmas - TO` -> (`Palmas`, `TO`). Sem sufixo de UF valido, UF None."""
    m = _SUFIXO_UF.match(item)
    if m and m["uf"].upper() in UFS:
        return m["nome"], m["uf"].upper()
    return item, None


def _uf_do_titulo(item: str) -> str | None:
    """O item e um titulo de estado (`Parana`, `PR`, `Estado de Sao Paulo`)?"""
    limpo = normalizar(item).removeprefix("ESTADO DE ").removeprefix("ESTADO DO ")
    if limpo in UFS:
        return limpo
    return _UF_POR_NOME.get(limpo)


@dataclass
class Leitura:
    """O que um snapshot rendeu: municipios casados, e o que nao casou."""

    municipios: dict[int, str] = field(default_factory=dict)  # codigo -> item literal
    ambiguos: list[str] = field(default_factory=list)
    sem_par: list[str] = field(default_factory=list)

    @property
    def legivel(self) -> bool:
        return len(self.municipios) >= MINIMO_CIDADES


def construir_indice(universo: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Nome normalizado -> [(codigo IBGE, UF)], a partir de `universo.csv`."""
    indice: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for m in universo:
        indice[_chave(m["municipio"])].append((int(m["municipio_ibge"]), m["uf"]))
    return dict(indice)


def ler(html: str, indice: dict[str, list[tuple[int, str]]]) -> Leitura:
    """Casa os itens de um snapshot com o universo."""
    leitura = Leitura()
    uf_corrente: str | None = None
    for item in itens(html):
        nome, uf_item = _separar_uf(item)
        candidatos = indice.get(_chave(nome), [])
        titulo = _uf_do_titulo(item)
        if titulo:
            # "Sao Paulo" e "Rio de Janeiro" sao titulo de estado e capital ao
            # mesmo tempo. O item muda a UF corrente e ainda conta a capital: as
            # duas operam desde o primeiro snapshot, entao o erro possivel e nulo.
            uf_corrente = titulo
        if not candidatos:
            if not titulo:
                leitura.sem_par.append(item)
            continue
        if uf_item is not None:
            # UF escrita no proprio item manda. Se o nome nao existe no universo
            # nessa UF, e homonimo pequeno, fora do universo: reportado, nao forcado.
            escolhidos = [c for c in candidatos if c[1] == uf_item]
        elif len(candidatos) > 1 and uf_corrente is not None:
            # O titulo de estado so desempata homonimo; nunca recusa nome unico,
            # porque a pagina pode nem ser agrupada por estado.
            escolhidos = [c for c in candidatos if c[1] == uf_corrente]
        else:
            escolhidos = candidatos
        if len(escolhidos) == 1:
            leitura.municipios.setdefault(escolhidos[0][0], item)
        elif len(escolhidos) > 1 or uf_item is None:
            leitura.ambiguos.append(item)
        else:
            leitura.sem_par.append(item)
    return leitura


def intervalos(
    plataforma: str,
    linha_do_tempo: list[tuple[str, str, dict[int, str]]],
    universo: dict[int, dict],
    data_acesso: str,
) -> list[dict]:
    """Linhas de entrada no esquema da planilha, uma por municipio que aparece.

    `linha_do_tempo` traz, em ordem de tempo e so com snapshots legiveis,
    `(timestamp, url_para_citar, {codigo: item_literal})`. Varios timestamps
    podem dividir o mesmo conteudo -- e eles que apertam o intervalo.
    """
    piso = mes_indice(PLATAFORMAS[plataforma].frota_propria_desde)
    # Snapshot anterior a frota propria nacional e marketplace por definicao
    # (D-020): nao data entrada nem serve de "ultimo sem".
    linha_do_tempo = [t for t in linha_do_tempo if mes_indice(f"{t[0][:4]}-{t[0][4:6]}") >= piso]
    if not linha_do_tempo:
        return []
    pagina = re.sub(r"^https://web\.archive\.org/web/\d+/", "", linha_do_tempo[0][1])
    linhas = []
    codigos = sorted({c for _, _, presentes in linha_do_tempo for c in presentes})
    for codigo in codigos:
        k = next(i for i, (_, _, p) in enumerate(linha_do_tempo) if codigo in p)
        ts_com, url_com, presentes = linha_do_tempo[k]
        fim = mes_indice(f"{ts_com[:4]}-{ts_com[4:6]}")
        notas = []
        if k == 0:
            inicio = piso
            notas.append(
                f"presente desde o primeiro snapshot legivel ({ts_com[:8]}): "
                "entrada em ou antes dessa data"
            )
            fonte = f"Wayback: {pagina}, presente no primeiro snapshot legivel {ts_com[:8]}"
        else:
            ts_sem = linha_do_tempo[k - 1][0]
            inicio = max(piso, mes_indice(f"{ts_sem[:4]}-{ts_sem[4:6]}"))
            fonte = f"Wayback: {pagina}, snapshots {ts_sem[:8]} e {ts_com[:8]}"
        sumicos = sum(1 for _, _, p in linha_do_tempo[k + 1 :] if codigo not in p)
        if sumicos:
            notas.append(f"ausente em {sumicos} snapshot(s) legivel(is) posterior(es)")
        largura = fim - inicio
        m = universo[codigo]
        linhas.append(
            {
                "municipio_ibge": str(codigo),
                "uf": m["uf"],
                "municipio": m["municipio"],
                "plataforma": plataforma,
                "evento": "entrada",
                "data_min": indice_mes(inicio),
                "data_max": indice_mes(fim),
                "tipo_evidencia": TIPO_EVIDENCIA,
                "confianca": "C" if k > 0 and largura <= 6 else "D",
                "fonte": fonte,
                "url": url_com,
                "data_acesso": data_acesso,
                "trecho": presentes[codigo],
                "buscas": "",
                "observacao": "; ".join(notas),
                "codificador": CODIFICADOR,
            }
        )
    return linhas
