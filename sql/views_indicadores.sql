CREATE OR REPLACE VIEW consolidado.vw_processos_por_municipio AS
SELECT municipio,
       date_trunc('month', dt_abertura)::date AS mes,
       count(*)                                AS abertos,
       count(*) FILTER (WHERE dt_conclusao IS NOT NULL) AS concluidos
FROM consolidado.processo
GROUP BY municipio, date_trunc('month', dt_abertura);

CREATE OR REPLACE VIEW consolidado.vw_tempo_medio_tramitacao AS
SELECT municipio,
       tipo_processo,
       round(avg(extract(epoch FROM dt_conclusao - dt_abertura) / 86400)::numeric, 1) AS dias_medios
FROM consolidado.processo
WHERE dt_conclusao IS NOT NULL
GROUP BY municipio, tipo_processo;

-- Premissa ilustrativa: 1 documento nato-digital = 3 folhas A4 evitadas
CREATE OR REPLACE VIEW consolidado.vw_documentos_digitais AS
SELECT municipio,
       count(*) FILTER (WHERE origem = 'NATO_DIGITAL') AS nato_digitais,
       count(*) FILTER (WHERE origem = 'DIGITALIZADO') AS digitalizados,
       count(*) FILTER (WHERE origem = 'NATO_DIGITAL') * 3 AS folhas_evitadas_estimadas
FROM consolidado.documento
GROUP BY municipio;
