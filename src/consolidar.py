"""Consolida tabelas de N bancos PostgreSQL de mesma estrutura num banco único."""
from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from datetime import datetime

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consolidar")


@dataclass
class Fonte:
    municipio: str
    dsn: str


@dataclass
class Tabela:
    nome: str
    chave: str
    colunas: list[str]
    coluna_atualizacao: str = "atualizado_em"


def carregar_config(caminho: str) -> tuple[str, list[Fonte], list[Tabela]]:
    with open(caminho, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    destino = os.path.expandvars(cfg["destino"])
    fontes = [Fonte(f["municipio"], os.path.expandvars(f["dsn"])) for f in cfg["fontes"] if f.get("ativo", True)]
    tabelas = [Tabela(**t) for t in cfg["tabelas"]]
    return destino, fontes, tabelas


def montar_select(t: Tabela) -> str:
    cols = ", ".join([t.chave, *t.colunas, t.coluna_atualizacao])
    return f"SELECT {cols} FROM {t.nome} WHERE {t.coluna_atualizacao} > %s ORDER BY {t.coluna_atualizacao}"


def montar_upsert(t: Tabela) -> str:
    destino_cols = ["municipio", "id_origem", *t.colunas, t.coluna_atualizacao]
    placeholders = ", ".join(["%s"] * len(destino_cols))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in [*t.colunas, t.coluna_atualizacao])
    return (
        f"INSERT INTO consolidado.{t.nome} ({', '.join(destino_cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (municipio, id_origem) DO UPDATE SET {updates}"
    )


def marcar_origem(municipio: str, linhas: list[tuple]) -> list[tuple]:
    return [(municipio, *linha) for linha in linhas]


def obter_marca_dagua(cur, municipio: str, tabela: str) -> datetime:
    cur.execute(
        "SELECT ultima_atualizacao FROM consolidado.controle_carga WHERE municipio = %s AND tabela = %s",
        (municipio, tabela),
    )
    row = cur.fetchone()
    return row[0] if row else datetime(1900, 1, 1)


def salvar_marca_dagua(cur, municipio: str, tabela: str, valor: datetime) -> None:
    cur.execute(
        """INSERT INTO consolidado.controle_carga (municipio, tabela, ultima_atualizacao, executado_em)
           VALUES (%s, %s, %s, now())
           ON CONFLICT (municipio, tabela) DO UPDATE
           SET ultima_atualizacao = EXCLUDED.ultima_atualizacao, executado_em = now()""",
        (municipio, tabela, valor),
    )


def consolidar(destino: str, fontes: list[Fonte], tabelas: list[Tabela], lote: int = 5000) -> dict[str, str]:
    import psycopg

    resultado: dict[str, str] = {}
    with psycopg.connect(destino) as dst:
        for fonte in fontes:
            try:
                with psycopg.connect(fonte.dsn, connect_timeout=15) as src:
                    for t in tabelas:
                        with dst.cursor() as dcur:
                            marca = obter_marca_dagua(dcur, fonte.municipio, t.nome)
                        total, nova_marca = 0, marca
                        with src.cursor() as scur:
                            scur.execute(montar_select(t), (marca,))
                            while linhas := scur.fetchmany(lote):
                                with dst.cursor() as dcur:
                                    dcur.executemany(montar_upsert(t), marcar_origem(fonte.municipio, linhas))
                                total += len(linhas)
                                nova_marca = linhas[-1][-1]
                        with dst.cursor() as dcur:
                            salvar_marca_dagua(dcur, fonte.municipio, t.nome, nova_marca)
                        dst.commit()
                        log.info("%s.%s: %s linhas", fonte.municipio, t.nome, total)
                resultado[fonte.municipio] = "ok"
            except Exception as exc:  # falha isolada por fonte
                dst.rollback()
                log.error("Falha em %s: %s", fonte.municipio, exc)
                resultado[fonte.municipio] = f"erro: {exc}"
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/fontes.yaml")
    args = parser.parse_args()
    destino, fontes, tabelas = carregar_config(args.config)
    resumo = consolidar(destino, fontes, tabelas)
    log.info("Resumo: %s", resumo)


if __name__ == "__main__":
    main()
