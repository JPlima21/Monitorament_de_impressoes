// Cria a estrutura HTML para uma coluna de impressora, usando o nome da impressora para gerar IDs unicos para os elementos
function criarColunaImpressora(nomeImpressora) {
    return `
        <div class="printer-column" data-printer-id="${nomeImpressora}">
            <div class="card printer-header-card">
                <div class="card-header">
                    <h2>Impressora <span id="nome_${nomeImpressora}"></span></h2>
                    <div class="status offline" id="status_${nomeImpressora}">OFFLINE</div>
                </div>
            </div>

            <div class="printer-details-row">
                <div class="card printer printer-image-card">
                    <div class="printer-image-layout">
                        <div class="printer-image">
                            <img id="imagem_${nomeImpressora}" src="/static/OKI_CALLCENTER.jpeg" alt="Impressora">
                        </div>
                        <div class="printer-image-info">
                            <h3>Informacoes</h3>
                            <div class="info">
                                <p><strong>IP:</strong> <span id="ip_${nomeImpressora}"></span></p>
                                <p><strong>MAC:</strong> <span id="mac_${nomeImpressora}"></span></p>
                                <p><strong>N Serie:</strong> <span id="serial_${nomeImpressora}"></span></p>
                                <p><strong>Modelo:</strong> <span id="modelo_${nomeImpressora}"></span></p>
                                <p><strong>Asset Number:</strong> <span id="asset_number_${nomeImpressora}"></span></p>
                                <p><strong>Localizacao:</strong> <span id="location_${nomeImpressora}"></span></p>
                                <p><strong>Uptime:</strong> <span id="uptime_${nomeImpressora}"></span></p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="printer-info-stack">
                    <div class="card card-recursos">
                        <h3>Recursos</h3>
                        <div class="info recursos-layout">
                            <div class="recursos-grid">
                                <div class="recursos-coluna recursos-principais">
                                    <p class="recurso-item"><strong>Impressoes</strong> <span id="impressoes_${nomeImpressora}"></span></p>
                                    <p class="recurso-item"><strong>Copias</strong> <span id="copias_${nomeImpressora}"></span></p>
                                    <p class="recurso-item"><strong>Scanner</strong> <span id="scanner_${nomeImpressora}"></span></p>
                                    <p class="recurso-item"><strong>Total</strong> <span id="total_impressoes_${nomeImpressora}"></span></p>
                                </div>
                                <div class="recursos-coluna recursos-indices">
                                    <div class="indice-card indice-hoje">
                                        <span class="indice-label">Hoje</span>
                                        <strong class="indice-valor" id="impressoes_dia_${nomeImpressora}"></strong>
                                    </div>
                                    <div class="indice-card indice-mes">
                                        <span class="indice-label">Mes</span>
                                        <strong class="indice-valor" id="impressoes_mes_${nomeImpressora}"></strong>
                                    </div>
                                    <div class="indice-card indice-toner">
                                        <span class="indice-label">Toner</span>
                                        <strong class="indice-valor" id="toner_${nomeImpressora}"></strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function obterImagemPorModelo(modelo) {
    const modeloNormalizado = String(modelo || "").toLowerCase();

    if (modeloNormalizado.includes("epson")) {
        return {
            src: "/static/Epson.JPG",
            alt: "Impressora Epson",
        };
    }

    if (modeloNormalizado.includes("oki")) {
        return {
            src: "/static/OKI_CALLCENTER.jpeg",
            alt: "Impressora OKI",
        };
    }

    return {
        src: "/static/OKI_CALLCENTER.jpeg",
        alt: "Impressora",
    };
}

// Atualiza o status de uma impressora (online/offline) e ajusta a classe CSS para refletir a cor correta
function atualizarStatus(statusEl, online) {
    if (!statusEl) {
        return;
    }

    statusEl.innerText = online ? "ONLINE" : "OFFLINE";
    statusEl.className = online ? "status online" : "status offline";
}

function formatarNumeroPainel(valor) {
    if (valor === null || valor === undefined || valor === "") {
        return "N/A";
    }

    if (typeof valor === "number") {
        return new Intl.NumberFormat("pt-BR").format(valor);
    }

    const numero = Number(valor);
    if (!Number.isNaN(numero) && String(valor).trim() !== "") {
        return new Intl.NumberFormat("pt-BR").format(numero);
    }

    return valor;
}

// Preenche os campos de uma impressora especifica, usando "N/A" como fallback para dados ausentes
function preencherCampos(nomeImpressora, dataImpressora) {
    const elements = {
        imagem: document.getElementById(`imagem_${nomeImpressora}`),
        nome: document.getElementById(`nome_${nomeImpressora}`),
        ip: document.getElementById(`ip_${nomeImpressora}`),
        mac: document.getElementById(`mac_${nomeImpressora}`),
        serial: document.getElementById(`serial_${nomeImpressora}`),
        modelo: document.getElementById(`modelo_${nomeImpressora}`),
        asset_number: document.getElementById(`asset_number_${nomeImpressora}`),
        location: document.getElementById(`location_${nomeImpressora}`),
        uptime: document.getElementById(`uptime_${nomeImpressora}`),
        total_impressoes: document.getElementById(`total_impressoes_${nomeImpressora}`),
        impressoes: document.getElementById(`impressoes_${nomeImpressora}`),
        copias: document.getElementById(`copias_${nomeImpressora}`),
        impressoes_dia: document.getElementById(`impressoes_dia_${nomeImpressora}`),
        impressoes_mes: document.getElementById(`impressoes_mes_${nomeImpressora}`),
        toner: document.getElementById(`toner_${nomeImpressora}`),
        scanner: document.getElementById(`scanner_${nomeImpressora}`),
    };

    if (elements.nome) elements.nome.innerText = dataImpressora.nome || "N/A";
    if (elements.imagem) {
        const imagem = obterImagemPorModelo(dataImpressora.modelo);
        elements.imagem.src = imagem.src;
        elements.imagem.alt = imagem.alt;
    }
    if (elements.ip) elements.ip.innerText = dataImpressora.ip || "N/A";
    if (elements.mac) elements.mac.innerText = dataImpressora.mac || "N/A";
    if (elements.serial) elements.serial.innerText = dataImpressora.num_serie || "N/A";
    if (elements.modelo) elements.modelo.innerText = dataImpressora.modelo || "N/A";
    if (elements.asset_number) elements.asset_number.innerText = dataImpressora.asset_number || "N/A";
    if (elements.location) elements.location.innerText = dataImpressora.location || "N/A";
    if (elements.uptime) elements.uptime.innerText = dataImpressora.uptime || "N/A";
    if (elements.total_impressoes) elements.total_impressoes.innerText = formatarNumeroPainel(dataImpressora.total_impressoes);
    if (elements.impressoes) elements.impressoes.innerText = formatarNumeroPainel(dataImpressora.impressoes);
    if (elements.copias) elements.copias.innerText = formatarNumeroPainel(dataImpressora.copias);
    if (elements.impressoes_dia) elements.impressoes_dia.innerText = formatarNumeroPainel(dataImpressora.impressoes_dia);
    if (elements.impressoes_mes) elements.impressoes_mes.innerText = formatarNumeroPainel(dataImpressora.impressoes_mes);
    if (elements.toner) elements.toner.innerText = dataImpressora.toner || "N/A";
    if (elements.scanner) elements.scanner.innerText = dataImpressora.scanner || "N/A";
}

function atualizarResumo(impressoras) {
    const listaImpressoras = Object.values(impressoras);
    const total = listaImpressoras.length;
    const online = listaImpressoras.filter((dados) => Boolean(dados.online)).length;
    const offline = total - online;

    const totalEl = document.getElementById("total-impressoras");
    const onlineEl = document.getElementById("total-online");
    const offlineEl = document.getElementById("total-offline");

    if (totalEl) totalEl.innerText = total;
    if (onlineEl) onlineEl.innerText = online;
    if (offlineEl) offlineEl.innerText = offline;
}

function ordenarImpressoras(impressoras) {
    return Object.entries(impressoras)
        .sort(([, dadosA], [, dadosB]) => Number(Boolean(dadosB.online)) - Number(Boolean(dadosA.online)))
        .map(([nomeImpressora]) => nomeImpressora);
}

// Mantem o container sincronizado com as impressoras e coloca as online primeiro
function sincronizarContainer(container, impressoras) {
    if (!container.dataset.initialized) {
        container.innerHTML = "";
        container.dataset.initialized = "true";
    }

    const nomesOrdenados = ordenarImpressoras(impressoras);
    const nomesAtuais = new Set(Object.keys(impressoras));

    for (const coluna of container.querySelectorAll(".printer-column")) {
        if (!nomesAtuais.has(coluna.dataset.printerId)) {
            coluna.remove();
        }
    }

    for (const nomeImpressora of nomesOrdenados) {
        let coluna = container.querySelector(`[data-printer-id="${nomeImpressora}"]`);

        if (!coluna) {
            container.insertAdjacentHTML("beforeend", criarColunaImpressora(nomeImpressora));
            coluna = container.querySelector(`[data-printer-id="${nomeImpressora}"]`);
        }

        container.appendChild(coluna);
    }
}

// Funcao principal para atualizar os dados das impressoras
async function atualizar() {
    try {
        const res = await fetch("/api");
        const data = await res.json();
        const impressoras = data.impressoras || {};
        const container = document.getElementById("content-container");

        atualizarResumo(impressoras);
        sincronizarContainer(container, impressoras);

        for (const [nomeImpressora, dataImpressora] of Object.entries(impressoras)) {
            const statusEl = document.getElementById(`status_${nomeImpressora}`);
            atualizarStatus(statusEl, dataImpressora.online);
            preencherCampos(nomeImpressora, dataImpressora);
        }
    } catch (error) {
        console.error("Erro ao buscar dados:", error);
    }
}

// Atualiza a cada 10 segundos
setInterval(atualizar, 10000);
atualizar();
