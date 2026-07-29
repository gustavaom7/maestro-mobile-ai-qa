# AI-powered test generation

Script simples que converte uma descrição em linguagem natural de um cenário
de teste em um flow `.yaml` do Maestro, usando a API da Anthropic (Claude).

## Por quê

A vaga menciona explicitamente "intelligent test case generation" como parte
da cultura AI-first. Esse script é a versão mínima e honesta disso: não
promete gerar suítes inteiras sozinho, mas acelera o primeiro rascunho de um
flow -- o QA ainda revisa, ajusta seletores e roda localmente antes de
commitar.

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## Exemplo de uso

```bash
python generate_flow.py \
  --app-id org.wikipedia \
  --scenario "Abrir o app, ir em configurações e alternar o modo escuro, depois confirmar que a tela ficou escura" \
  --output ../../maestro/mobile/flows/05_dark_mode_toggle.yaml
```

## Ideia para evoluir (auto-healing)

Um passo natural depois disso: quando um flow falhar por causa de um
seletor quebrado (ex: texto do botão mudou), reenviar pro LLM o YAML antigo
+ a árvore de UI atual (`maestro hierarchy`) e pedir um seletor corrigido,
gerando um PR automático em vez de só reportar a falha no Slack.
