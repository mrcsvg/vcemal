"""Desempate de linhas com mesma data_min no mesmo par e evento, DEPOIS da verificacao:
fica a que passou (wayback_script/confirmado), depois melhor grau, depois intervalo mais estreito.
uso (da raiz do repo): python scripts/... -> python3 desempatar.py bruto.csv destino.csv"""
import sys, csv, logging
sys.path.insert(0, "/Users/mrcsvg/Projects/vcemal/scripts"); sys.path.insert(0, "/Users/mrcsvg/Projects/vcemal/src")
import auditoria_verificar as av
import pandas as pd
from vcemal import verificacao as ver
logging.basicConfig(level=logging.WARNING)
bruto, destino = sys.argv[1], sys.argv[2]
rows = pd.read_csv(bruto, dtype=str).fillna("").to_dict("records")
wb = pd.read_csv(av.WAYBACK, dtype=str).fillna("")
scripts = {ver.chave_wayback(r) for r in wb.to_dict("records")}
GRAU = {"A": 0, "B": 1, "C": 2, "D": 3}
def mi(s): a, m = s.split("-"); return int(a) * 12 + int(m)
grupos = {}
for i, r in enumerate(rows):
    if r["confianca"].strip() != "N":
        grupos.setdefault((r["municipio_ibge"], r["plataforma"], r["evento"], r["data_min"].strip()), []).append(i)
fora = set()
for ch, idx in grupos.items():
    if len(idx) < 2: continue
    def rank(i):
        r = rows[i]; s, _ = av._status(r, scripts)
        return (s not in ver.ACEITOS, GRAU[r["confianca"].strip()], mi(r["data_max"]) - mi(r["data_min"]))
    ordem = sorted(idx, key=rank)
    for i in ordem[1:]:
        fora.add(i); print("DESCARTADA:", rows[i]["municipio"], ch[1:], rows[i]["confianca"], rank(i), rows[i]["url"][:70], "| fica", rank(ordem[0]))
out = [r for i, r in enumerate(rows) if i not in fora]
pd.DataFrame(out, columns=list(rows[0].keys())).to_csv(destino, index=False)
print(len(out), "linhas ->", destino)
