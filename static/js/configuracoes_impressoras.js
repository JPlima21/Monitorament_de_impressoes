(() => {
    function formatarTexto(valor, fallback = "N/A") {
        const texto = String(valor ?? "").trim();
        return texto || fallback;
    }

    function formatarMoedaCentavos(valorCentavos) {
        const valor = Number(valorCentavos || 0) / 100;
        return new Intl.NumberFormat("pt-BR", {
            style: "currency",
            currency: "BRL",
        }).format(valor);
    }

    function atualizarResumo(impressoras) {
        const total = impressoras.length;
        const online = impressoras.filter((item) => item.online).length;
        const offline = total - online;

        const totalEl = document.getElementById("total-impressoras");
        const onlineEl = document.getElementById("total-impressoras-online");
        const offlineEl = document.getElementById("total-impressoras-offline");

        if (totalEl) totalEl.innerText = total;
        if (onlineEl) onlineEl.innerText = online;
        if (offlineEl) offlineEl.innerText = offline;
    }

    function renderizarListaImpressoras(impressoras) {
        const container = document.getElementById("lista-impressoras");

        if (!container) {
            return;
        }

        if (!impressoras.length) {
            container.innerHTML = `<p class="inventory-empty">Nenhuma impressora cadastrada.</p>`;
            return;
        }

        const cards = [...impressoras]
            .sort((a, b) => String(a.nome || a.id).localeCompare(String(b.nome || b.id), "pt-BR"))
            .map((impressora) => `
                <article class="inventory-card">
                    <h3>${formatarTexto(impressora.nome, impressora.id)}</h3>
                    <div class="inventory-meta">
                        <span class="inventory-badge ${impressora.online ? "online" : "offline"}">
                            ${impressora.online ? "Online" : "Offline"}
                        </span>
                        <span class="inventory-badge">${formatarTexto(impressora.id)}</span>
                    </div>
                    <div class="inventory-details">
                        <p><strong>IP:</strong> ${formatarTexto(impressora.ip)}</p>
                        <p><strong>Community:</strong> ${formatarTexto(impressora.community)}</p>
                        <p><strong>Token:</strong> ${formatarTexto(impressora.token_valor_formatado)}</p>
                        <p><strong>Modelo:</strong> ${formatarTexto(impressora.modelo)}</p>
                        <p><strong>Localizacao:</strong> ${formatarTexto(impressora.location)}</p>
                        <p><strong>Custo dia:</strong> ${formatarMoedaCentavos(impressora.custo_estimado_dia_centavos)}</p>
                        <p><strong>Custo mes:</strong> ${formatarMoedaCentavos(impressora.custo_estimado_mes_centavos)}</p>
                    </div>
                </article>
            `)
            .join("");

        container.innerHTML = cards;
    }

    function definirFeedback(mensagem, tipo = "") {
        const el = document.getElementById("form-feedback");

        if (!el) {
            return;
        }

        el.innerText = mensagem || "";
        el.className = "form-feedback";

        if (tipo) {
            el.classList.add(`is-${tipo}`);
        }
    }

    async function carregarImpressoras() {
        const resposta = await fetch("/api/impressoras");
        const impressoras = await resposta.json();
        atualizarResumo(impressoras);
        renderizarListaImpressoras(impressoras);
        return impressoras;
    }

    async function salvarNovaImpressora(event) {
        event.preventDefault();

        const form = document.getElementById("form-impressora");
        const botao = document.getElementById("submit-impressora");

        if (!form || !botao) {
            return;
        }

        const formData = new FormData(form);
        const payload = {
            ip: String(formData.get("ip") || "").trim(),
            community: String(formData.get("community") || "").trim(),
            id: String(formData.get("id") || "").trim(),
            token_valor_centavos: String(formData.get("token_valor_centavos") || "").trim(),
        };

        definirFeedback("");
        botao.disabled = true;

        try {
            const resposta = await fetch("/api/impressoras", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });
            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(dados.erro || "Nao foi possivel adicionar a impressora.");
            }

            form.reset();
            const communityInput = document.getElementById("printer-community");
            const tokenInput = document.getElementById("printer-token");
            if (communityInput) {
                communityInput.value = "oabce";
            }
            if (tokenInput) {
                tokenInput.value = "4";
            }

            definirFeedback(dados.mensagem || "Impressora adicionada com sucesso.", "success");
            await carregarImpressoras();
        } catch (error) {
            definirFeedback(error.message || "Erro ao adicionar a impressora.", "error");
        } finally {
            botao.disabled = false;
        }
    }

    async function inicializarPaginaImpressoras() {
        try {
            await carregarImpressoras();
        } catch (error) {
            definirFeedback("Nao foi possivel carregar a lista de impressoras.", "error");
            renderizarListaImpressoras([]);
        }

        const form = document.getElementById("form-impressora");
        if (form && !form.dataset.bound) {
            form.addEventListener("submit", salvarNovaImpressora);
            form.dataset.bound = "true";
        }
    }

    inicializarPaginaImpressoras();
})();
