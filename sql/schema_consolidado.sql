CREATE SCHEMA IF NOT EXISTS consolidado;

CREATE TABLE IF NOT EXISTS consolidado.controle_carga (
    municipio           TEXT NOT NULL,
    tabela              TEXT NOT NULL,
    ultima_atualizacao  TIMESTAMP NOT NULL,
    executado_em        TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (municipio, tabela)
);

CREATE TABLE IF NOT EXISTS consolidado.processo (
    municipio         TEXT    NOT NULL,
    id_origem         BIGINT  NOT NULL,
    tipo_processo     TEXT,
    unidade_geradora  TEXT,
    dt_abertura       TIMESTAMP,
    dt_conclusao      TIMESTAMP,
    situacao          TEXT,
    atualizado_em     TIMESTAMP NOT NULL,
    PRIMARY KEY (municipio, id_origem)
);

CREATE TABLE IF NOT EXISTS consolidado.documento (
    municipio       TEXT   NOT NULL,
    id_origem       BIGINT NOT NULL,
    id_processo     BIGINT,
    tipo_documento  TEXT,
    origem          TEXT,          -- 'NATO_DIGITAL' | 'DIGITALIZADO'
    dt_inclusao     TIMESTAMP,
    atualizado_em   TIMESTAMP NOT NULL,
    PRIMARY KEY (municipio, id_origem)
);

CREATE INDEX IF NOT EXISTS ix_processo_abertura ON consolidado.processo (municipio, dt_abertura);
CREATE INDEX IF NOT EXISTS ix_documento_processo ON consolidado.documento (municipio, id_processo);
