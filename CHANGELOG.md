# Changelog

## v1.0.0-beta.1 - 2026-03-24

Primeira versao organizada para publicacao do projeto como portfolio tecnico e ERP operacional em evolucao.

### Adicionado

- shell visual mais proximo de ERP corporativo no frontend
- dashboard operacional com atalhos e imagens por modulo
- modulo operacional de custo por fornecedor
- fluxo de formacao de custo com atualizacao de `B1_CM`
- geracao de `AP` a partir de entrada com fornecedor
- listagem e manutencao de tabelas de preco no frontend
- alertas de negocio no backend com CTA no frontend
- navegacao contextual entre AR/AP, categorias e caixa
- auditoria consultavel no frontend
- campo de `CMV unit` por item de pedido
- screenshots e documentacao de portfolio

### Alterado

- backend consolidado como API pura sem camada web/Jinja
- bootstrap protegido por ambiente e estado persistido no banco
- payload de erro padronizado
- limpeza de shims, imports antigos e codigo residual
- frontend com tema unificado e heroes por modulo

### Corrigido

- falha de build no frontend em `parceiros`
- warnings de hooks no frontend
- problemas de encoding/mojibake no codigo e no exportador PDF
- erro de ambiguidade `D_E_L_E_T_` em consultas com joins
- problemas de compatibilidade de coluna `ID` em bases reais
- leitura de auditoria que retornava lista vazia
- geracao de `F1_NUM` para `SF1_AP` quando `SX6_SEQ` estava defasada

### Conhecido

- compras ainda nao existem como modulo completo
- estoque avancado ainda nao cobre lote, validade e armazem
- fiscal e governanca ainda estao em aprofundamento
