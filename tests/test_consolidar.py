import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from consolidar import Tabela, carregar_config, marcar_origem, montar_select, montar_upsert  # noqa: E402

T = Tabela(nome="processo", chave="id_processo", colunas=["situacao", "dt_abertura"])


def test_select_incremental():
    sql = montar_select(T)
    assert sql.startswith("SELECT id_processo, situacao, dt_abertura, atualizado_em FROM processo")
    assert "WHERE atualizado_em > %s" in sql


def test_upsert_idempotente():
    sql = montar_upsert(T)
    assert "ON CONFLICT (municipio, id_origem) DO UPDATE" in sql
    assert sql.count("%s") == 5  # municipio, id_origem, 2 colunas, atualizado_em


def test_marcar_origem():
    assert marcar_origem("A", [(1, "x"), (2, "y")]) == [("A", 1, "x"), ("A", 2, "y")]


def test_config_ignora_fontes_inativas(monkeypatch):
    monkeypatch.setenv("SENHA_A", "s")
    _, fontes, tabelas = carregar_config(str(ROOT / "config" / "fontes.example.yaml"))
    assert [f.municipio for f in fontes] == ["MUNICIPIO_A", "MUNICIPIO_B"]
    assert {t.nome for t in tabelas} == {"processo", "documento"}
    assert "leitura:s@" in fontes[0].dsn
