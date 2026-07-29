"""
Gera um flow do Maestro (YAML) a partir de uma descrição em linguagem natural,
usando a API da Anthropic.

Objetivo: mostrar como um QA pode acelerar a criação de casos de teste com
LLMs, sem virar uma "caixa preta" -- o script sempre imprime o flow gerado
para revisão humana antes de salvar, porque teste gerado por IA ainda precisa
de review de alguém que entende o app.

Uso:
    export ANTHROPIC_API_KEY=sk-...
    python generate_flow.py \
        --app-id org.wikipedia \
        --scenario "Abrir o app, pesquisar por 'Test automation' e verificar que o primeiro resultado aparece" \
        --output ../../maestro/mobile/flows/04_generated_search.yaml
"""

import argparse
import os
import sys

import anthropic

SYSTEM_PROMPT = """Você é um engenheiro de QA especialista em Maestro
(https://maestro.mobile.dev). Gere APENAS um flow YAML válido de Maestro,
sem explicações, sem markdown, sem crases. O YAML deve começar com o
cabeçalho "appId: <app_id>" seguido de "---" e depois a lista de comandos.
Use apenas comandos oficiais do Maestro (launchApp, tapOn, inputText,
assertVisible, takeScreenshot, back, scroll, swipe, etc). Prefira seletores
por texto visível em vez de coordenadas fixas, e adicione um comentário
curto acima de cada bloco lógico do teste explicando a intenção."""


def generate_flow(app_id: str, scenario: str) -> str:
    client = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY do ambiente

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"appId: {app_id}\n"
                    f"Cenário de teste em linguagem natural: {scenario}"
                ),
            }
        ],
    )

    return "".join(
        block.text for block in message.content if block.type == "text"
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-id", required=True, help="appId do app mobile ou URL para web")
    parser.add_argument("--scenario", required=True, help="descrição do cenário em linguagem natural")
    parser.add_argument("--output", required=True, help="caminho do arquivo .yaml de saída")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERRO: defina a variável de ambiente ANTHROPIC_API_KEY.", file=sys.stderr)
        return 1

    flow_yaml = generate_flow(args.app_id, args.scenario)

    print("--- Flow gerado (revise antes de commitar!) ---")
    print(flow_yaml)
    print("------------------------------------------------")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(flow_yaml + "\n")

    print(f"\nFlow salvo em: {args.output}")
    print("Lembrete: rode `maestro test <arquivo>` localmente antes de commitar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
