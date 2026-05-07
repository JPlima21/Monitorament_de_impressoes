(() => {
    function formatarTexto(valor, fallback = "N/A") {
        const texto = String(valor ?? "").trim();
        return texto && texto !== "None" ? texto : fallback;
    }

    function atualizarResumo(switches) {
        const total = switches.length;
        const online = switches.filter((item) => item.online).length;
        const offline = total - online;

        const totalEl = document.getElementById("total-switches");
        const onlineEl = document.getElementById("total-switches-online");
        const offlineEl = document.getElementById("total-switches-offline");

        if (totalEl) totalEl.innerText = total;
        if (onlineEl) onlineEl.innerText = online;
        if (offlineEl) offlineEl.innerText = offline;
    }

    function renderizarListaSwitches(switches) {
        const container = document.getElementById("lista-switches");

        if (!container) {
            return;
        }

        if (!switches.length) {
            container.innerHTML = `<p class="inventory-empty">Nenhum switch cadastrado.</p>`;
            return;
        }

        const cards = [...switches]
            .sort((a, b) => String(a.nome || a.id).localeCompare(String(b.nome || b.id), "pt-BR"))
            .map((switchItem) => `
                <article class="inventory-card">
                    <h3>${formatarTexto(switchItem.nome, switchItem.id)}</h3>
                    <div class="inventory-meta">
                        <span class="inventory-badge ${switchItem.online ? "online" : "offline"}">
                            ${switchItem.online ? "Online" : "Offline"}
                        </span>
                        <span class="inventory-badge">${formatarTexto(switchItem.id)}</span>
                    </div>
                    <div class="inventory-details">
                        <p><strong>IP:</strong> ${formatarTexto(switchItem.ip)}</p>
                        <p><strong>Community:</strong> ${formatarTexto(switchItem.community)}</p>
                        <p><strong>Descricao:</strong> ${formatarTexto(switchItem.descricao)}</p>
                        <p><strong>Localizacao:</strong> ${formatarTexto(switchItem.location)}</p>
                        <p><strong>Contato:</strong> ${formatarTexto(switchItem.contato)}</p>
                        <p><strong>Uptime:</strong> ${formatarTexto(switchItem.uptime)}</p>
                        <p><strong>MAC:</strong> ${formatarTexto(switchItem.mac)}</p>
                        <p><strong>Interfaces:</strong> ${Number(switchItem.interfaces_total || 0)}</p>
                        <p><strong>Porta principal:</strong> ${formatarTexto(switchItem.status_porta_principal)}</p>
                    </div>
                </article>
            `)
            .join("");

        container.innerHTML = cards;
    }

    function definirFeedback(mensagem, tipo = "") {
        const el = document.getElementById("form-feedback-switch");

        if (!el) {
            return;
        }

        el.innerText = mensagem || "";
        el.className = "form-feedback";

        if (tipo) {
            el.classList.add(`is-${tipo}`);
        }
    }

    async function carregarSwitches() {
        const resposta = await fetch("/api/switches");
        const switches = await resposta.json();
        atualizarResumo(switches);
        renderizarListaSwitches(switches);
        return switches;
    }

    async function salvarNovoSwitch(event) {
        event.preventDefault();

        const form = document.getElementById("form-switch");
        const botao = document.getElementById("submit-switch");

        if (!form || !botao) {
            return;
        }

        const formData = new FormData(form);
        const payload = {
            ip: String(formData.get("ip") || "").trim(),
            community: String(formData.get("community") || "").trim(),
            id: String(formData.get("id") || "").trim(),
        };

        definirFeedback("");
        botao.disabled = true;

        try {
            const resposta = await fetch("/api/switches", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });
            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(dados.erro || "Nao foi possivel adicionar o switch.");
            }

            form.reset();
            const communityInput = document.getElementById("switch-community");
            if (communityInput) {
                communityInput.value = "oabce";
            }

            definirFeedback(dados.mensagem || "Switch adicionado com sucesso.", "success");
            await carregarSwitches();
        } catch (error) {
            definirFeedback(error.message || "Erro ao adicionar o switch.", "error");
        } finally {
            botao.disabled = false;
        }
    }

    async function inicializarPaginaSwitches() {
        try {
            await carregarSwitches();
        } catch (error) {
            definirFeedback("Nao foi possivel carregar a lista de switches.", "error");
            renderizarListaSwitches([]);
        }

        const form = document.getElementById("form-switch");
        if (form && !form.dataset.bound) {
            form.addEventListener("submit", salvarNovoSwitch);
            form.dataset.bound = "true";
        }
    }

    inicializarPaginaSwitches();
})();
