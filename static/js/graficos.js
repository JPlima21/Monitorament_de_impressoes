const SVG_NS = "http://www.w3.org/2000/svg";
const chartColorPalette = [
    "#38bdf8",
    "#34d399",
    "#f59e0b",
    "#f87171",
    "#a78bfa",
    "#fb7185",
    "#22c55e",
    "#60a5fa",
    "#f97316",
    "#14b8a6",
];
const graficosState = {
    impressoras: [],
    historico: [],
    historicoDiario: new Map(),
    historicoDiarioCompleto: new Map(),
    historicoMensal: new Map(),
    abaAtiva: "painel-grafico-dia",
};
let resizeTimeoutId = null;

function formatarNumero(valor) {
    return new Intl.NumberFormat("pt-BR").format(Number(valor || 0));
}

function obterDataAtualIso() {
    const agora = new Date();
    const ano = String(agora.getFullYear());
    const mes = String(agora.getMonth() + 1).padStart(2, "0");
    const dia = String(agora.getDate()).padStart(2, "0");
    return `${ano}-${mes}-${dia}`;
}

function obterMesAtualIso() {
    return obterDataAtualIso().slice(0, 7);
}

function formatarDataIso(valor) {
    const [ano, mes, dia] = String(valor || "").split("-");

    if (!ano || !mes || !dia) {
        return String(valor || "");
    }

    return `${dia}/${mes}/${ano}`;
}

function formatarMesIso(valor) {
    const [ano, mes] = String(valor || "").split("-");

    if (!ano || !mes) {
        return String(valor || "");
    }

    return new Intl.DateTimeFormat("pt-BR", {
        month: "long",
        year: "numeric",
    }).format(new Date(Number(ano), Number(mes) - 1, 1));
}

function escaparHtml(valor) {
    return String(valor ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
}

function atualizarResumo(impressoras) {
    const total = impressoras.length;
    const online = impressoras.filter((item) => item.online).length;
    const offline = total - online;

    const totalEl = document.getElementById("total-impressoras");
    const onlineEl = document.getElementById("total-online");
    const offlineEl = document.getElementById("total-offline");

    if (totalEl) totalEl.innerText = total;
    if (onlineEl) onlineEl.innerText = online;
    if (offlineEl) offlineEl.innerText = offline;
}

function ordenarImpressoras(impressoras) {
    return [...impressoras].sort((a, b) => {
        if (a.online !== b.online) {
            return Number(b.online) - Number(a.online);
        }

        return String(a.nome || a.id).localeCompare(String(b.nome || b.id), "pt-BR");
    });
}

function abreviarRotulo(texto, limite = 14) {
    const textoNormalizado = String(texto || "").trim();
    return textoNormalizado.length > limite
        ? `${textoNormalizado.slice(0, limite - 3)}...`
        : textoNormalizado;
}

function criarSvgBase(host, alturaMinima = 360) {
    host.innerHTML = "";
    const largura = Math.max(host.clientWidth || 720, 720);
    const altura = alturaMinima;
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${largura} ${altura}`);
    svg.setAttribute("class", "svg-chart");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    host.appendChild(svg);
    return { svg, largura, altura };
}

function adicionarTextoSvg(svg, x, y, texto, className, anchor = "middle") {
    const el = document.createElementNS(SVG_NS, "text");
    el.setAttribute("x", x);
    el.setAttribute("y", y);
    el.setAttribute("text-anchor", anchor);
    el.setAttribute("class", className);
    el.textContent = texto;
    svg.appendChild(el);
    return el;
}

function adicionarTituloTooltip(elemento, texto) {
    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = texto;
    elemento.appendChild(title);
}

function desenharGradeY(svg, area, maxValue, steps = 5) {
    const safeMax = Math.max(maxValue, 1);

    for (let i = 0; i <= steps; i += 1) {
        const ratio = i / steps;
        const y = area.y + area.height - ratio * area.height;
        const valor = Math.round(safeMax * ratio);

        const linha = document.createElementNS(SVG_NS, "line");
        linha.setAttribute("x1", area.x);
        linha.setAttribute("x2", area.x + area.width);
        linha.setAttribute("y1", y);
        linha.setAttribute("y2", y);
        linha.setAttribute("class", "svg-grid-line");
        svg.appendChild(linha);

        adicionarTextoSvg(svg, area.x - 10, y + 4, formatarNumero(valor), "svg-axis-label", "end");
    }
}

function renderizarGraficoColunas(hostId, tituloVazio, itens, campoValor, corPrimaria) {
    const host = document.getElementById(hostId);

    if (!host) {
        return;
    }

    if (!itens.length) {
        host.innerHTML = `<p class="chart-loading">${tituloVazio}</p>`;
        return;
    }

    const dados = ordenarImpressoras(itens);
    const { svg, largura, altura } = criarSvgBase(host, 380);
    const area = { x: 72, y: 24, width: largura - 96, height: 250 };
    const maxValue = Math.max(...dados.map((item) => Number(item[campoValor] || 0)), 0);
    const passo = area.width / dados.length;
    const larguraBarra = Math.min(42, passo * 0.55);

    desenharGradeY(svg, area, maxValue, 5);

    const eixoX = document.createElementNS(SVG_NS, "line");
    eixoX.setAttribute("x1", area.x);
    eixoX.setAttribute("x2", area.x + area.width);
    eixoX.setAttribute("y1", area.y + area.height);
    eixoX.setAttribute("y2", area.y + area.height);
    eixoX.setAttribute("class", "svg-axis-line");
    svg.appendChild(eixoX);

    dados.forEach((item, index) => {
        const valor = Number(item[campoValor] || 0);
        const xCentro = area.x + passo * index + passo / 2;
        const alturaBarra = maxValue > 0 ? (valor / maxValue) * area.height : 0;
        const yBarra = area.y + area.height - alturaBarra;
        const fill = item.online === false ? "#64748b" : corPrimaria;

        const rect = document.createElementNS(SVG_NS, "rect");
        rect.setAttribute("x", xCentro - larguraBarra / 2);
        rect.setAttribute("y", yBarra);
        rect.setAttribute("width", larguraBarra);
        rect.setAttribute("height", Math.max(alturaBarra, 2));
        rect.setAttribute("rx", "10");
        rect.setAttribute("class", "svg-bar");
        rect.setAttribute("fill", fill);
        adicionarTituloTooltip(rect, `${item.nome}: ${formatarNumero(valor)}`);
        svg.appendChild(rect);

        adicionarTextoSvg(
            svg,
            xCentro,
            Math.max(yBarra - 8, 16),
            formatarNumero(valor),
            "svg-value-label",
        );

        adicionarTextoSvg(
            svg,
            xCentro,
            area.y + area.height + 22,
            abreviarRotulo(item.nome),
            "svg-axis-label svg-axis-label-x",
        );
    });
}

function construirMapaHistoricoDiario(registros) {
    const mapa = new Map();

    registros.forEach((registro) => {
        const data = String(registro.data || "").slice(0, 10);
        const impressora = String(registro.impressora || "").trim();
        const valor = Number(registro.impressoes_total_dia || 0);

        if (!data || !impressora) {
            return;
        }

        if (!mapa.has(data)) {
            mapa.set(data, new Map());
        }

        const valorAtual = mapa.get(data).get(impressora) ?? 0;
        mapa.get(data).set(impressora, Math.max(valorAtual, valor));
    });

    return mapa;
}

function construirMapaHistoricoDiarioCompleto(mapaHistoricoDiario, impressoras) {
    const mapaCompleto = new Map(mapaHistoricoDiario);
    const dataAtual = obterDataAtualIso();
    const valoresHoje = new Map(mapaCompleto.get(dataAtual) || []);

    impressoras.forEach((item) => {
        const nome = String(item.nome || item.id || "").trim();

        if (!nome) {
            return;
        }

        valoresHoje.set(nome, Number(item.impressoes_dia || 0));
    });

    if (valoresHoje.size) {
        mapaCompleto.set(dataAtual, valoresHoje);
    }

    return mapaCompleto;
}

function construirMapaHistoricoMensal(mapaHistoricoDiario) {
    const mapaMensal = new Map();

    [...mapaHistoricoDiario.entries()].forEach(([data, valoresDia]) => {
        const mes = String(data).slice(0, 7);

        if (!mes) {
            return;
        }

        if (!mapaMensal.has(mes)) {
            mapaMensal.set(mes, new Map());
        }

        [...valoresDia.entries()].forEach(([impressora, valor]) => {
            const acumulado = mapaMensal.get(mes).get(impressora) ?? 0;
            mapaMensal.get(mes).set(impressora, acumulado + Number(valor || 0));
        });
    });

    return mapaMensal;
}

function agruparMapaPorData(mapaDatas) {
    const mapaImpressoras = new Map();
    const datasOrdenadas = [...mapaDatas.keys()].sort();

    datasOrdenadas.forEach((data) => {
        const valoresDia = mapaDatas.get(data) || new Map();

        [...valoresDia.keys()].forEach((impressora) => {
            if (!mapaImpressoras.has(impressora)) {
                mapaImpressoras.set(
                    impressora,
                    chartColorPalette[mapaImpressoras.size % chartColorPalette.length],
                );
            }
        });
    });

    const impressoras = [...mapaImpressoras.keys()].sort((a, b) => a.localeCompare(b, "pt-BR"));
    return {
        datas: datasOrdenadas,
        impressoras: impressoras.map((nome) => ({ nome, cor: mapaImpressoras.get(nome) })),
        valores: mapaDatas,
    };
}

function renderizarGraficoLinhaHistorico(hostId, mapaHistoricoDiario) {
    const host = document.getElementById(hostId);

    if (!host) {
        return;
    }

    if (!mapaHistoricoDiario.size) {
        host.innerHTML = `<p class="chart-loading">Nenhum registro historico disponivel.</p>`;
        return;
    }

    const agrupado = agruparMapaPorData(mapaHistoricoDiario);

    if (!agrupado.datas.length || !agrupado.impressoras.length) {
        host.innerHTML = `<p class="chart-loading">Nenhum registro historico disponivel.</p>`;
        return;
    }

    const { svg, largura, altura } = criarSvgBase(host, 420);
    const area = { x: 72, y: 24, width: largura - 96, height: 240 };
    const todosValores = [];

    agrupado.datas.forEach((data) => {
        agrupado.impressoras.forEach(({ nome }) => {
            todosValores.push(agrupado.valores.get(data).get(nome) ?? 0);
        });
    });

    const maxValue = Math.max(...todosValores, 0);
    desenharGradeY(svg, area, maxValue, 5);

    const eixoX = document.createElementNS(SVG_NS, "line");
    eixoX.setAttribute("x1", area.x);
    eixoX.setAttribute("x2", area.x + area.width);
    eixoX.setAttribute("y1", area.y + area.height);
    eixoX.setAttribute("y2", area.y + area.height);
    eixoX.setAttribute("class", "svg-axis-line");
    svg.appendChild(eixoX);

    const passoX = agrupado.datas.length > 1 ? area.width / (agrupado.datas.length - 1) : 0;

    agrupado.impressoras.forEach(({ nome, cor }) => {
        const pontos = agrupado.datas.map((data, indice) => {
            const valor = agrupado.valores.get(data).get(nome) ?? 0;
            const x = area.x + passoX * indice;
            const y = area.y + area.height - ((maxValue > 0 ? valor / maxValue : 0) * area.height);
            return { x, y, valor, data };
        });

        const path = document.createElementNS(SVG_NS, "path");
        const d = pontos
            .map((ponto, indice) => `${indice === 0 ? "M" : "L"} ${ponto.x} ${ponto.y}`)
            .join(" ");
        path.setAttribute("d", d);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", cor);
        path.setAttribute("stroke-width", "3");
        path.setAttribute("stroke-linejoin", "round");
        path.setAttribute("stroke-linecap", "round");
        svg.appendChild(path);
        adicionarTituloTooltip(path, nome);

        pontos.forEach((ponto) => {
            const circle = document.createElementNS(SVG_NS, "circle");
            circle.setAttribute("cx", ponto.x);
            circle.setAttribute("cy", ponto.y);
            circle.setAttribute("r", "4");
            circle.setAttribute("fill", cor);
            circle.setAttribute("class", "svg-point");
            adicionarTituloTooltip(circle, `${nome} | ${ponto.data}: ${formatarNumero(ponto.valor)}`);
            svg.appendChild(circle);
        });
    });

    agrupado.datas.forEach((data, indice) => {
        const x = area.x + passoX * indice;
        adicionarTextoSvg(svg, x, area.y + area.height + 22, data, "svg-axis-label svg-axis-label-x");
    });

    const legendX = area.x;
    const legendY = area.y + area.height + 48;
    agrupado.impressoras.forEach(({ nome, cor }, indice) => {
        const itemX = legendX + (indice % 3) * 220;
        const itemY = legendY + Math.floor(indice / 3) * 24;

        const marcador = document.createElementNS(SVG_NS, "rect");
        marcador.setAttribute("x", itemX);
        marcador.setAttribute("y", itemY - 10);
        marcador.setAttribute("width", "14");
        marcador.setAttribute("height", "14");
        marcador.setAttribute("rx", "4");
        marcador.setAttribute("fill", cor);
        svg.appendChild(marcador);

        adicionarTextoSvg(svg, itemX + 22, itemY + 1, nome, "svg-legend-label", "start");
    });
}

function popularFiltroPeriodo(selectId, valores, formatador, valorPadrao) {
    const select = document.getElementById(selectId);

    if (!select) {
        return "";
    }

    const valorAtual = select.value;
    const valorSelecionado = valores.includes(valorAtual)
        ? valorAtual
        : (valores.includes(valorPadrao) ? valorPadrao : (valores[0] || ""));

    select.innerHTML = valores
        .map((valor) => `<option value="${escaparHtml(valor)}">${escaparHtml(formatador(valor))}</option>`)
        .join("");

    select.value = valorSelecionado;
    select.disabled = valores.length <= 1;
    return valorSelecionado;
}

function obterItensHistoricos(mapaValores, campoValor) {
    return [...mapaValores.entries()].map(([nome, valor]) => ({
        id: nome,
        nome,
        [campoValor]: Number(valor || 0),
    }));
}

function atualizarSubtitulo(hostId, texto) {
    const el = document.getElementById(hostId);

    if (el) {
        el.innerText = texto;
    }
}

function obterPainelGraficoAtivo() {
    return document.getElementById(graficosState.abaAtiva);
}

function alternarAbaGraficos(tabId) {
    graficosState.abaAtiva = tabId;

    document.querySelectorAll(".chart-tab-button").forEach((botao) => {
        const ativo = botao.dataset.tabTarget === tabId;
        botao.classList.toggle("active", ativo);
        botao.setAttribute("aria-selected", ativo ? "true" : "false");
    });

    document.querySelectorAll(".chart-tab-panel").forEach((painel) => {
        const ativo = painel.id === tabId;
        painel.classList.toggle("active", ativo);
        painel.hidden = !ativo;
    });
}

function inicializarAbasGraficos() {
    const botoes = document.querySelectorAll(".chart-tab-button");

    botoes.forEach((botao) => {
        if (botao.dataset.bound) {
            return;
        }

        botao.addEventListener("click", () => {
            alternarAbaGraficos(botao.dataset.tabTarget);
            renderizarGraficosPorPeriodo();
        });
        botao.dataset.bound = "true";
    });
}

function renderizarGraficosPorPeriodo() {
    const dataSelecionada = document.getElementById("filtro-data-dia")?.value || "";
    const mesSelecionado = document.getElementById("filtro-data-mes")?.value || "";
    const dataAtual = obterDataAtualIso();
    const mesAtual = obterMesAtualIso();
    const valoresDia = graficosState.historicoDiarioCompleto.get(dataSelecionada) || new Map();
    const valoresMes = mesSelecionado === mesAtual
        ? null
        : (graficosState.historicoMensal.get(mesSelecionado) || new Map());

    const itensDia = dataSelecionada === dataAtual
        ? graficosState.impressoras
        : obterItensHistoricos(valoresDia, "impressoes_dia");
    const itensMes = mesSelecionado === mesAtual
        ? graficosState.impressoras
        : obterItensHistoricos(valoresMes, "impressoes_mes");

    atualizarSubtitulo(
        "subtitulo-grafico-dia",
        `Periodo: ${formatarDataIso(dataSelecionada)} | eixo X: impressoras | eixo Y: impressoes_dia`,
    );
    atualizarSubtitulo(
        "subtitulo-grafico-mes",
        `Periodo: ${formatarMesIso(mesSelecionado)} | eixo X: impressoras | eixo Y: impressoes_mes`,
    );

    if (graficosState.abaAtiva === "painel-grafico-dia") {
        renderizarGraficoColunas(
            "grafico-colunas-dia",
            "Nenhum dado diario disponivel para o periodo selecionado.",
            itensDia,
            "impressoes_dia",
            "#38bdf8",
        );
    }

    if (graficosState.abaAtiva === "painel-grafico-mes") {
        renderizarGraficoColunas(
            "grafico-colunas-mes",
            "Nenhum dado mensal disponivel para o periodo selecionado.",
            itensMes,
            "impressoes_mes",
            "#34d399",
        );
    }

    renderizarGraficoLinhaHistorico("grafico-linha-historico", graficosState.historicoDiarioCompleto);
}

function inicializarFiltrosPeriodo() {
    const datasDisponiveis = [...graficosState.historicoDiarioCompleto.keys()].sort().reverse();
    const mesesDisponiveis = new Set([
        obterMesAtualIso(),
        ...[...graficosState.historicoMensal.keys()],
    ]);
    const mesesOrdenados = [...mesesDisponiveis].sort().reverse();

    popularFiltroPeriodo("filtro-data-dia", datasDisponiveis, formatarDataIso, obterDataAtualIso());
    popularFiltroPeriodo("filtro-data-mes", mesesOrdenados, formatarMesIso, obterMesAtualIso());

    const filtroDia = document.getElementById("filtro-data-dia");
    const filtroMes = document.getElementById("filtro-data-mes");

    if (filtroDia && !filtroDia.dataset.bound) {
        filtroDia.addEventListener("change", renderizarGraficosPorPeriodo);
        filtroDia.dataset.bound = "true";
    }

    if (filtroMes && !filtroMes.dataset.bound) {
        filtroMes.addEventListener("change", renderizarGraficosPorPeriodo);
        filtroMes.dataset.bound = "true";
    }
}

function preencherTabelaHistorico(registros) {
    const tbody = document.getElementById("tabela-historico-body");

    if (!tbody) {
        return;
    }

    if (!registros.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="chart-loading">Nenhum registro historico disponivel.</td>
            </tr>
        `;
        return;
    }

    const linhas = [...registros]
        .sort((a, b) => String(b.timestamp_salvo || "").localeCompare(String(a.timestamp_salvo || "")))
        .slice(0, 100)
        .map((registro) => `
            <tr>
                <td>${escaparHtml(registro.data)}</td>
                <td>${escaparHtml(registro.impressora)}</td>
                <td>${formatarNumero(registro.impressoes_total_dia)}</td>
                <td>${escaparHtml(registro.motivo)}</td>
                <td>${escaparHtml(registro.timestamp_salvo)}</td>
            </tr>
        `)
        .join("");

    tbody.innerHTML = linhas;
}

async function carregarGraficos() {
    try {
        const [resImpressoras, resHistorico] = await Promise.all([
            fetch("/api/powerbi/impressoras"),
            fetch("/api/powerbi/historico"),
        ]);
        const [impressoras, historico] = await Promise.all([
            resImpressoras.json(),
            resHistorico.json(),
        ]);
        const historicoDiario = construirMapaHistoricoDiario(historico);

        graficosState.impressoras = impressoras;
        graficosState.historico = historico;
        graficosState.historicoDiario = historicoDiario;
        graficosState.historicoDiarioCompleto = construirMapaHistoricoDiarioCompleto(
            historicoDiario,
            impressoras,
        );
        graficosState.historicoMensal = construirMapaHistoricoMensal(historicoDiario);

        atualizarResumo(impressoras);
        inicializarAbasGraficos();
        inicializarFiltrosPeriodo();
        alternarAbaGraficos(graficosState.abaAtiva);
        renderizarGraficosPorPeriodo();
        preencherTabelaHistorico(historico);
    } catch (error) {
        console.error("Erro ao carregar graficos:", error);
        const mensagens = [
            "grafico-colunas-dia",
            "grafico-colunas-mes",
            "grafico-linha-historico",
        ];

        mensagens.forEach((id) => {
            const host = document.getElementById(id);
            if (host) {
                host.innerHTML = `<p class="chart-loading">Nao foi possivel carregar os dados.</p>`;
            }
        });

        preencherTabelaHistorico([]);
    }
}

window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimeoutId);
    resizeTimeoutId = window.setTimeout(renderizarGraficosPorPeriodo, 120);
});

carregarGraficos();
