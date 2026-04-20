function criarColunaImpressora(nomeImpressora) {
    return `
        <div class="printer-column">
            <div class="card printer">
                <div class="printer-image">
                    <img src="/static/OKI_CALLCENTER.jpeg" alt="Impressora OKI">
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h2>Impressora <span id="nome_${nomeImpressora}"></span></h2>
                    <div class="status offline" id="status_${nomeImpressora}">OFFLINE</div>
                </div>
            </div>

            <div class="card">
                <h3>Informacoes</h3>
                <div class="info">
                    <p><strong>IP:</strong> <span id="ip_${nomeImpressora}"></span></p>
                    <p><strong>MAC:</strong> <span id="mac_${nomeImpressora}"></span></p>
                    <p><strong>N Serie:</strong> <span id="serial_${nomeImpressora}"></span></p>
                    <p><strong>Modelo:</strong> <span id="modelo_${nomeImpressora}"></span></p>
                    <p><strong>Asset Number:</strong> <span id="asset_number_${nomeImpressora}"></span></p>
                    <p><strong>Uptime:</strong> <span id="uptime_${nomeImpressora}"></span></p>
                </div>
            </div>

            <div class="card">
                <h3>Recursos</h3>
                <div class="info">
                    <p><strong>Impressoes Total:</strong> <span id="impressoes_${nomeImpressora}"></span></p>
                    <p><strong>Impressoes Hoje:</strong> <span id="impressoes_dia_${nomeImpressora}"></span></p>
                    <p><strong>Toner:</strong> <span id="toner_${nomeImpressora}"></span></p>
                    <p><strong>Scanner:</strong> <span id="scanner_${nomeImpressora}"></span></p>
                </div>
            </div>
        </div>
    `;
}

function atualizarStatus(statusEl, online) {
    if (!statusEl) {
        return;
    }

    statusEl.innerText = online ? "ONLINE" : "OFFLINE";
    statusEl.className = online ? "status online" : "status offline";
}

function preencherCampos(nomeImpressora, dataImpressora) {
    const elements = {
        nome: document.getElementById(`nome_${nomeImpressora}`),
        ip: document.getElementById(`ip_${nomeImpressora}`),
        mac: document.getElementById(`mac_${nomeImpressora}`),
        serial: document.getElementById(`serial_${nomeImpressora}`),
        modelo: document.getElementById(`modelo_${nomeImpressora}`),
        asset_number: document.getElementById(`asset_number_${nomeImpressora}`),
        uptime: document.getElementById(`uptime_${nomeImpressora}`),
        impressoes: document.getElementById(`impressoes_${nomeImpressora}`),
        impressoes_dia: document.getElementById(`impressoes_dia_${nomeImpressora}`),
        toner: document.getElementById(`toner_${nomeImpressora}`),
        scanner: document.getElementById(`scanner_${nomeImpressora}`),
    };

    if (elements.nome) elements.nome.innerText = dataImpressora.nome || "N/A";
    if (elements.ip) elements.ip.innerText = dataImpressora.ip || "N/A";
    if (elements.mac) elements.mac.innerText = dataImpressora.mac || "N/A";
    if (elements.serial) elements.serial.innerText = dataImpressora.num_serie || "N/A";
    if (elements.modelo) elements.modelo.innerText = dataImpressora.modelo || "N/A";
    if (elements.asset_number) elements.asset_number.innerText = dataImpressora.asset_number || "N/A";
    if (elements.uptime) elements.uptime.innerText = dataImpressora.uptime || "N/A";
    if (elements.impressoes) elements.impressoes.innerText = dataImpressora.impressoes ?? "N/A";
    if (elements.impressoes_dia) elements.impressoes_dia.innerText = dataImpressora.impressoes_dia ?? "N/A";
    if (elements.toner) elements.toner.innerText = dataImpressora.toner || "N/A";
    if (elements.scanner) elements.scanner.innerText = dataImpressora.scanner || "N/A";
}

function inicializarContainer(container, impressoras) {
    if (container.dataset.initialized) {
        return;
    }

    let html = "";
    for (const nomeImpressora of Object.keys(impressoras)) {
        html += criarColunaImpressora(nomeImpressora);
    }

    container.innerHTML = html;
    container.dataset.initialized = "true";
}

async function atualizar() {
    try {
        const res = await fetch("/api");
        const data = await res.json();
        const impressoras = data.impressoras || {};
        const container = document.getElementById("content-container");

        inicializarContainer(container, impressoras);

        for (const [nomeImpressora, dataImpressora] of Object.entries(impressoras)) {
            const statusEl = document.getElementById(`status_${nomeImpressora}`);
            atualizarStatus(statusEl, dataImpressora.online);
            preencherCampos(nomeImpressora, dataImpressora);
        }
    } catch (error) {
        console.error("Erro ao buscar dados:", error);
    }
}

setInterval(atualizar, 4000);
atualizar();
