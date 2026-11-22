"""O estimador em R contra um DGP sintetico com efeito conhecido (tests/did_sintetico.R).

Pula sem `Rscript` ou sem o pacote `did`; leva ~20 s.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

AQUI = Path(__file__).parent


def _tem_did() -> bool:
    if shutil.which("Rscript") is None:
        return False
    r = subprocess.run(
        ["Rscript", "-e", "quit(status = !requireNamespace('did', quietly = TRUE))"],
        capture_output=True,
    )
    return r.returncode == 0


@pytest.mark.skipif(not _tem_did(), reason="sem Rscript ou sem o pacote did")
def test_estimador_recupera_efeito_conhecido():
    r = subprocess.run(
        ["Rscript", str(AQUI / "did_sintetico.R")], capture_output=True, text=True, timeout=600
    )
    linhas = [s for s in r.stdout.splitlines() if s.startswith(("ok", "FALHA"))]
    assert r.returncode == 0, "\n".join(linhas) + r.stderr[-2000:]
    assert not any(s.startswith("FALHA") for s in linhas)
