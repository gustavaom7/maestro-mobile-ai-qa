#!/usr/bin/env bash
# Posta um resumo do run de testes no Slack via Incoming Webhook.
# Uso: slack_notify.sh <nome-da-suite> <status>
# Requer a env var SLACK_WEBHOOK_URL configurada como secret no GitHub Actions.

set -euo pipefail

SUITE_NAME="${1:-QA}"
STATUS="${2:-unknown}"

if [ "$STATUS" = "success" ]; then
  EMOJI="✅"
  COLOR="#2eb886"
else
  EMOJI="❌"
  COLOR="#e01e5a"
fi

if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
  echo "SLACK_WEBHOOK_URL não configurado, pulando notificação."
  exit 0
fi

PAYLOAD=$(cat <<EOF
{
  "attachments": [
    {
      "color": "${COLOR}",
      "blocks": [
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "${EMOJI} *Suite ${SUITE_NAME}*: resultado *${STATUS}*\n<https://github.com/${GITHUB_REPOSITORY:-repo}/actions/runs/${GITHUB_RUN_ID:-0}|Ver detalhes do run>"
          }
        }
      ]
    }
  ]
}
EOF
)

curl -s -X POST -H 'Content-type: application/json' \
  --data "${PAYLOAD}" \
  "${SLACK_WEBHOOK_URL}"
