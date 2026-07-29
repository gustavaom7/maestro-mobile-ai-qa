# Arquitetura e encaixe no SDLC

## Fluxo do dia a dia (hipotético, alinhado à vaga)

1. Dev abre um PR -> `mobile-tests.yml` e `web-tests.yml` rodam automaticamente
2. Toda madrugada, o cron roda a suíte completa contra o build mais recente
3. Falhas geram: (a) artifact com relatório JUnit, (b) mensagem no Slack com
   link direto pro run
4. QA (ou dev) revisa o relatório, abre bug no Jira/Linear se for regressão real
5. Novos cenários entram via `ai_test_generator`, sempre com revisão humana
   antes do commit

## Decisões e trade-offs

- **Maestro em vez de Appium/Selenium puro:** sintaxe declarativa em YAML,
  mais rápido de manter e mais fácil de revisar em code review do que
  código de automação tradicional -- importante pra um time que quer que
  QA e devs consigam ler os testes uns dos outros.
- **Emulador no CI em vez de dispositivo físico:** mais barato e reprodutível
  para rodar diariamente; dispositivo físico fica reservado pra testes de
  performance/bateria que não fazem parte deste repo.
- **Web em beta:** documentado como risco conhecido (`docs/web-fallback-playwright.md`),
  não escondido.
