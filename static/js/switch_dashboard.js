(() => {
    function formatarTexto(valor, fallback = "N/A") {
        const texto = String(valor ?? "").trim();
        return texto && texto !== "None" ? texto : fallback;
    }

    function escaparHtml(valor) {
        return String(valor ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;");
    }

    function formatarNumero(valor) {
        return new Intl.NumberFormat("pt-BR").format(Number(valor || 0));
    }

    function normalizarStatusPorta(valor) {
        const texto = formatarTexto(valor, "N/A");
        return texto.toLowerCase();
    }

    function atualizarResumo(switches) {
        const total = switches.length;
        const online = switches.filter((item) => item.online).length;
        const offline = total - online;
        const interfaces = switches.reduce(
            (acumulado, item) => acumulado + Number(item.interfaces_total || 0),
            0,
        );

        const totalEl = document.getElementById("total-switches");
        const onlineEl = document.getElementById("total-switches-online");
        const offlineEl = document.getElementById("total-switches-offline");
        const interfacesEl = document.getElementById("total-interfaces");

        if (totalEl) totalEl.innerText = total;
        if (onlineEl) onlineEl.innerText = online;
        if (offlineEl) offlineEl.innerText = offline;
        if (interfacesEl) interfacesEl.innerText = formatarNumero(interfaces);
    }

    function ordenarSwitches(switches) {
        return [...switches].sort((a, b) => {
            if (Boolean(a.online) !== Boolean(b.online)) {
                return Number(Boolean(b.online)) - Number(Boolean(a.online));
            }

            return String(a.nome || a.id).localeCompare(String(b.nome || b.id), "pt-BR");
        });
    }

    function obterClasseStatusPorta(valor) {
        const status = normalizarStatusPorta(valor);

        if (status === "up") {
            return "switch-highlight is-up";
        }

        if (status === "down") {
            return "switch-highlight is-down";
        }

        return "switch-highlight";
    }

    function renderizarListaSwitches(switches) {
        const container = document.getElementById("switches-dashboard-grid");

        if (!container) {
            return;
        }

        if (!switches.length) {
            container.innerHTML = `<p class="inventory-empty">Nenhum switch cadastrado para monitoramento.</p>`;
            return;
        }

        const cards = ordenarSwitches(switches)
            .map((switchItem) => `
                <article class="switch-panel-card">
                    <div class="switch-card-header">
                        <div class="switch-card-title-group">
                            <span class="switch-card-kicker">Switch monitorado</span>
                            <h2>${escaparHtml(formatarTexto(switchItem.nome, switchItem.id))}</h2>
                            <p>${escaparHtml(formatarTexto(switchItem.id))}</p>
                        </div>
                        <div class="switch-card-status-group">
                            <span class="status ${switchItem.online ? "online" : "offline"}">
                                ${switchItem.online ? "ONLINE" : "OFFLINE"}
                            </span>
                            <span class="switch-community-badge">
                                SNMP ${escaparHtml(formatarTexto(switchItem.community))}
                            </span>
                        </div>
                    </div>

                    <div class="switch-highlight-grid">
                        <div class="switch-highlight">
                            <span class="switch-highlight-label">Interfaces</span>
                            <strong>${formatarNumero(switchItem.interfaces_total)}</strong>
                        </div>
                        <div class="${obterClasseStatusPorta(switchItem.status_porta_principal)}">
                            <span class="switch-highlight-label">Porta principal</span>
                            <strong>${escaparHtml(formatarTexto(switchItem.status_porta_principal))}</strong>
                        </div>
                    </div>

                    <div class="switch-metadata-grid">
                        <div class="switch-meta-item">
                            <span>IP</span>
                            <strong>${escaparHtml(formatarTexto(switchItem.ip))}</strong>
                        </div>
                        <div class="switch-meta-item">
                            <span>MAC</span>
                            <strong>${escaparHtml(formatarTexto(switchItem.mac))}</strong>
                        </div>
                        <div class="switch-meta-item">
                            <span>Localizacao</span>
                            <strong>${escaparHtml(formatarTexto(switchItem.location))}</strong>
                        </div>
                        <div class="switch-meta-item">
                            <span>Contato</span>
                            <strong>${escaparHtml(formatarTexto(switchItem.contato))}</strong>
                        </div>
                        <div class="switch-meta-item switch-meta-item-wide">
                            <span>Descricao</span>
                            <strong>${escaparHtml(formatarTexto(switchItem.descricao))}</strong>
                        </div>
                        <div class="switch-meta-item switch-meta-item-wide">
                            <span>Uptime</span>
                            <strong>${escaparHtml(formatarTexto(switchItem.uptime))}</strong>
                        </div>
                    </div>
                </article>
            `)
            .join("");

        container.innerHTML = cards;
    }

    async function carregarDashboardSwitches() {
        try {
            const resposta = await fetch("/api/switches");
            const switches = await resposta.json();
            atualizarResumo(switches);
            renderizarListaSwitches(switches);
        } catch (error) {
            console.error("Erro ao carregar dashboard de switches:", error);

            const container = document.getElementById("switches-dashboard-grid");
            if (container) {
                container.innerHTML = `<p class="inventory-empty">Nao foi possivel carregar os switches.</p>`;
            }
        }
    }

    setInterval(carregarDashboardSwitches, 10000);
    carregarDashboardSwitches();
})();
