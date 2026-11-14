"""Junta lote original + repeticoes (lote_k_rN) e escreve a planilha do codificador.
Para cada par (municipio x plataforma) presente numa repeticao, TODAS as linhas do par no
lote original (entrada e saida) saem e entram as da repeticao.
uso: python3 juntar.py A destino.csv   (falha se sobrar par pendente)"""
import csv, sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repartir import pendentes
X, destino = sys.argv[1], sys.argv[2]
base = os.path.dirname(os.path.abspath(__file__))
saida = []; hdr = None; problemas = []
for k in range(1, 6):
    d = f"{base}/{X}/lote_{k}"
    rows = list(csv.DictReader(open(f"{d}/planilha.csv"))); hdr = hdr or list(rows[0].keys())
    reps = sorted(glob.glob(f"{d}_r*/planilha.csv"))
    for rp in reps:
        rr = list(csv.DictReader(open(rp)))
        pares = {(r["municipio_ibge"], r["plataforma"]) for r in rr}
        rows = [r for r in rows if (r["municipio_ibge"], r["plataforma"]) not in pares] + rr
    pend = pendentes(rows)
    if pend: problemas.append((k, len(pend), pend[:5]))
    saida += [{h: r.get(h, "") for h in hdr} for r in rows]
if problemas:
    for p in problemas: print("PENDENTE lote", *p)
    sys.exit(1)
with open(destino, "w", newline="") as f:
    w = csv.DictWriter(f, hdr); w.writeheader(); w.writerows(saida)
print(X, len(saida), "linhas ->", destino)
