# Medidas DAX de exemplo

```dax
Processos Abertos = SUM ( vw_processos_por_municipio[abertos] )

Processos Concluídos = SUM ( vw_processos_por_municipio[concluidos] )

Taxa de Conclusão =
DIVIDE ( [Processos Concluídos], [Processos Abertos] )

% Nato-Digital =
DIVIDE (
    SUM ( vw_documentos_digitais[nato_digitais] ),
    SUM ( vw_documentos_digitais[nato_digitais] ) + SUM ( vw_documentos_digitais[digitalizados] )
)

Abertos Mês Anterior =
CALCULATE ( [Processos Abertos], DATEADD ( Calendario[Data], -1, MONTH ) )

Variação MoM % =
DIVIDE ( [Processos Abertos] - [Abertos Mês Anterior], [Abertos Mês Anterior] )

Ranking Município =
RANKX ( ALL ( vw_processos_por_municipio[municipio] ), [Taxa de Conclusão] )
```

## Boas práticas aplicadas
- Power BI conecta **somente** à base consolidada (uma conexão, um gateway).
- Tabela `Calendario` dedicada, marcada como tabela de datas.
- Views no PostgreSQL concentram a lógica pesada; o DAX fica com o contexto de filtro.
