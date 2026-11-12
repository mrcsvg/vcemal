from vcemal import cronologia as cro
from vcemal import verificacao as ver


def _linha(**kw):
    base = dict.fromkeys(cro.COLUNAS, "")
    base.update(
        municipio_ibge="4106902",
        uf="PR",
        municipio="Curitiba",
        plataforma="ifood",
        evento="entrada",
        codificador="A",
    )
    base.update(kw)
    return base


def _achado(**kw):
    base = dict(
        data_min="2018-09",
        data_max="2018-09",
        tipo_evidencia=2,
        confianca="B",
        fonte="Jornal",
        url="https://exemplo.invalido/x",
        data_acesso="2026-11-12",
        trecho="entregadores do iFood começam a operar em Curitiba",
    )
    base.update(kw)
    return _linha(**base)


def test_normalizar_tira_acento_pontuacao_e_caixa():
    assert ver.normalizar("  São  José, da Lapa!  ") == "sao jose da lapa"


def test_texto_da_pagina_ignora_script_e_entidades():
    corpo = "<p>Entregadores do&nbsp;<b>iFood</b> chegam</p><script>var x='nada';</script>"
    assert ver.texto_da_pagina(corpo) == "entregadores do ifood chegam"


def test_fragmentos_respeitam_reticencias_e_minimo():
    frags = ver.fragmentos("o iFood anunciou hoje [...] entregadores parceiros em Londrina … ok")
    assert frags == ["o ifood anunciou hoje", "entregadores parceiros em londrina"]


def test_confere_trecho_e_municipio():
    pagina = ver.texto_da_pagina(
        "<p>Os entregadores do iFood começam a operar em Curitiba nesta semana</p>"
    )
    assert ver.confere(pagina, "entregadores do iFood começam a operar em Curitiba", "Curitiba")
    assert not ver.confere(pagina, "entregadores do iFood começam a operar em Londrina", "Curitiba")
    assert ver.confere(pagina, "", "Curitiba")
    assert not ver.confere(pagina, "", "Ponta Grossa")


def test_aplicar_rebaixa_e_leva_a_saida():
    linhas = [
        _achado(),
        _achado(
            evento="saida", data_min="2022-03", data_max="2022-03", tipo_evidencia=1, confianca="A"
        ),
        _linha(plataforma="rappi", tipo_evidencia=0, confianca="N", buscas="q1"),
    ]
    out = ver.aplicar(linhas, ["trecho_ausente", "confirmado", None])
    assert len(out) == 2
    assert out[0]["confianca"] == "N" and out[0]["data_min"] == ""
    assert "trecho_ausente" in out[0]["buscas"]
    assert out[1]["plataforma"] == "rappi"
    cro.validar(out)


def test_aplicar_mantem_reentrada_que_passou():
    linhas = [
        _achado(plataforma="99food", data_min="2019-12", data_max="2019-12"),
        _achado(plataforma="99food", data_min="2025-09", data_max="2025-09"),
    ]
    out = ver.aplicar(linhas, ["inacessivel", "confirmado"])
    assert [r["data_min"] for r in out] == ["2025-09"]
    sens = ver.aplicar(linhas, ["inacessivel", "confirmado"], aceitos=ver.ACEITOS_SENSIBILIDADE)
    assert len(sens) == 2
