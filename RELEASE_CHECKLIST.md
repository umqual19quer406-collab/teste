# Release Checklist

## Publicacao Recomendada

- Nome: `Mini Protheus`
- Tag sugerida: `v1.0.0-beta.1`
- Posicionamento: `mini ERP operacional em desenvolvimento, inspirado em fluxos de backoffice Protheus`

## Antes de Publicar

- revisar `README.md`
- revisar `CHANGELOG.md`
- revisar screenshots em `docs/screenshots/`
- garantir que `.env.example` esteja coerente
- validar subida local de backend e frontend
- executar `pytest -q`
- executar `cd frontend && npm run lint`

## Comunicacao Recomendada

- destacar modulos ja operacionais
- declarar limitacoes atuais
- tratar roadmap como evolucao planejada, nao como escopo concluido
- nao posicionar o produto como equivalente tecnico ao TOTVS Protheus

## Bugs Conhecidos Aceitaveis para a Publicacao

- profundidade fiscal parcial
- ausencia de modulo formal de compras
- governanca de permissao ainda basica
- estoque avancado ainda incompleto
