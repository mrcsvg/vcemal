"""Reparte o que falta de um lote em pedacos de ate N municipios (regra de falha do D-067).
Refaz o par (municipio x plataforma) quando a linha entrada esta vazia ou quando `buscas`
nao cumpre o piso do adendo: >=1 consulta nomeando o municipio; iFood >=3 consultas.
uso: python3 repartir.py A 4 [N=3]  -> A/lote_4_r1, ... com as linhas desses pares em branco."""
import csv, sys, os, unicodedata, re
def norm(t):
    t = unicodedata.normalize("NFKD", t); t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^0-9a-z]+", " ", t).strip()
def piso_ok(r):
    qs = [q for q in r["buscas"].split(";") if q.strip()]
    m = norm(r["municipio"])
    nomeia = any(f" {m} " in f" {norm(q)} " for q in qs)
    return nomeia and (len(qs) >= 3 if r["plataforma"] == "ifood" else True)
def pendentes(rows):
    ent = [r for r in rows if r["evento"] == "entrada"]
    pares = {}
    for r in ent:
        p = (r["municipio_ibge"], r["plataforma"])
        ok = bool(r["confianca"].strip()) and piso_ok(r)
        pares[p] = pares.get(p, False) or ok
    return [p for p, ok in pares.items() if not ok]
if __name__ == "__main__":
    X, k = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    base = os.path.dirname(os.path.abspath(__file__)); d = f"{base}/{X}/lote_{k}"
    rows = list(csv.DictReader(open(f"{d}/planilha.csv"))); hdr = list(rows[0].keys())
    pend = pendentes(rows)
    ordem = list(dict.fromkeys(p[0] for p in pend))
    vistos = set(); novas = []
    for r in rows:
        p = (r["municipio_ibge"], r["plataforma"])
        if p in pend and r["evento"] == "entrada" and p not in vistos:
            vistos.add(p); b = {h: "" for h in hdr}
            for h in ("municipio_ibge", "uf", "municipio", "plataforma", "evento"): b[h] = r[h]
            b["codificador"] = X; novas.append(b)
    wb = list(csv.DictReader(open(f"{d}/wayback.csv"))); whdr = list(wb[0].keys()) if wb else []
    for i in range(0, len(ordem), N):
        parte = set(ordem[i:i+N]); o = f"{base}/{X}/lote_{k}_r{i//N+1}"; os.makedirs(o)
        with open(f"{o}/planilha.csv", "w", newline="") as f:
            w = csv.DictWriter(f, hdr); w.writeheader(); w.writerows([r for r in novas if r["municipio_ibge"] in parte])
        with open(f"{o}/wayback.csv", "w", newline="") as f:
            w = csv.DictWriter(f, whdr); w.writeheader(); w.writerows([r for r in wb if r["municipio_ibge"] in parte])
        os.system(f"cp '{d}/protocolo.md' '{o}/'")
        print(o, len(parte), "mun", sum(r["municipio_ibge"] in parte for r in novas), "pares")
    print("pendentes", len(pend), "de", len({(r['municipio_ibge'], r['plataforma']) for r in rows if r['evento']=='entrada'}))
