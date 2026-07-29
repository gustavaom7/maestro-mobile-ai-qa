# Fallback: testes web sem depender do suporte beta do Maestro

O suporte a web do Maestro ainda está evoluindo e a sintaxe de configuração
(`url:` vs `webUrl:` vs flag de CLI) pode variar entre versões. Documentei
isso aqui de propósito, porque é exatamente o tipo de decisão real que um QA
precisa tomar: usar uma feature nova e assumir o risco, ou usar algo maduro.

Se o time preferir estabilidade em vez de feature nova, a mesma suíte lógica
(`homepage_load`, `dropdown_and_dynamic_content`) pode ser reescrita em
Playwright ou Selenium sem perder a cobertura, mantendo o Maestro só para
mobile. Ambas abordagens rodam nos mesmos jobs de CI, só troca a ferramenta
no step de execução.

Isso também é um bom gancho de conversa na entrevista: mostra que dá pra
escolher a ferramenta certa pra cada contexto em vez de forçar uma única
tecnologia em tudo.
