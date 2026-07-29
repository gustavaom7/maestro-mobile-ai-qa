# Casos de teste manuais / exploratórios

Exemplo de documentação de teste manual complementando a automação -- a vaga
pede fluência nas duas frentes, não só automação.

## TC-001 - Busca com termo vazio (mobile)

**Pré-condição:** app aberto na tela inicial
**Passos:**
1. Tocar em "Search Wikipedia"
2. Deixar o campo vazio e tocar em voltar/back
**Resultado esperado:** app retorna pra tela inicial sem crash e sem estado
de busca "preso" na próxima abertura da busca.
**Tipo:** funcional / edge case

## TC-002 - Rotação de tela durante busca (mobile)

**Pré-condição:** busca em andamento com resultados na tela
**Passos:**
1. Rotacionar o dispositivo para paisagem
2. Rotacionar de volta para retrato
**Resultado esperado:** resultados da busca continuam visíveis, sem perda de
estado.
**Tipo:** exploratório

## TC-003 - Dropdown com teclado (web)

**Pré-condição:** página `/dropdown` carregada
**Passos:**
1. Focar o dropdown via Tab (teclado, não mouse)
2. Selecionar opção via teclas de seta + Enter
**Resultado esperado:** opção correta é selecionada, comportamento igual ao
uso via mouse.
**Tipo:** acessibilidade / regressão

## Observação sobre priorização

Numa suíte que roda toda semana antes de release, esses casos exploratórios
acima do TC-001 são bons candidatos a virar automação (repetitivos, baixo
julgamento). O TC-002 e TC-003 valem mais como checklist manual periódico,
porque dependem de comportamento de gesto/acessibilidade que é mais caro de
automatizar de forma confiável do que de checar manualmente com frequência
baixa.
