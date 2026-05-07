function inicializarAbasConfiguracoes() {
    const botoes = Array.from(document.querySelectorAll("[data-tab-target]"));

    if (!botoes.length) {
        return;
    }

    const ativarAba = (botaoAtivo) => {
        botoes.forEach((botao) => {
            const panelId = botao.dataset.tabTarget;
            const painel = panelId ? document.getElementById(panelId) : null;
            const ativo = botao === botaoAtivo;

            botao.classList.toggle("active", ativo);
            botao.setAttribute("aria-selected", ativo ? "true" : "false");

            if (painel) {
                painel.classList.toggle("active", ativo);
                painel.hidden = !ativo;
            }
        });
    };

    botoes.forEach((botao) => {
        if (botao.dataset.bound === "true") {
            return;
        }

        botao.addEventListener("click", () => ativarAba(botao));
        botao.dataset.bound = "true";
    });

    const botaoInicial = botoes.find((botao) => botao.classList.contains("active")) || botoes[0];
    ativarAba(botaoInicial);
}

inicializarAbasConfiguracoes();
