"use strict";
// Pascal — interface. Fala com o app.py por /api/...

const $ = (id) => document.getElementById(id);
const TOKEN = window.TOKEN;
// Textos na tela: o app escreve em português e o i18n.js troca para inglês (botão PT/EN). Só caixas de alerta/confirmação precisam de T().
const T = (s) => (window.I18N ? window.I18N.tr(s) : s);

async function api(route, body) {
  const opt = { headers: { "X-Token": TOKEN } };
  if (body !== undefined) {
    opt.method = "POST";
    opt.headers["Content-Type"] = "application/json";
    opt.body = JSON.stringify(body);
  }
  let r;
  try { r = await fetch(route, opt); }
  catch (e) { throw new Error("O Pascal parou de responder (foi fechado). Feche esta janela e abra o Iniciar_Pascal.bat de novo."); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok || data.error) throw new Error(data.error || ("Erro " + r.status));
  return data;
}

// ------------------------------------------------------------------ controles das abas
const TABS = [
  { id: "chroma", titulo: "Recorte e fundo", ctl: [
    { k: "bg_mode", t: "select", label: "Modo de saída do fundo", opts: [
      ["studio_mp4", "Fundo Preto de Estúdio (.MP4)"],
      ["alpha_prores", "Fundo Transparente para Premiere (.MOV ProRes 4444)"],
      ["alpha_qtrle", "Fundo Transparente Leve (.MOV QTRLE)"]],
      help: "ProRes 4444 é o melhor para o Premiere; QTRLE gera arquivo menor." },
    { k: "bg_style", t: "select", label: "Estilo do fundo de estúdio (modo MP4)", opts: [
      ["preto", "Preto de estúdio liso (natural, recomendado)"], ["feixe", "Preto com feixe de luz diagonal (estilo do alvo)"], ["halo", "Preto com brilho suave atrás da pessoa (pode parecer auréola)"]],
      help: "Só vale quando a saída é MP4 com fundo de estúdio." },
    { k: "matte_engine", t: "select", label: "Motor de recorte", opts: [
      ["rvm", "Recorte avançado — cabelo natural, fio a fio (mais lento)"], ["chroma", "Recorte clássico (rápido)"]],
      help: "Reconhece a pessoa quadro a quadro e recorta o cabelo fio a fio, sem depender da cor do fundo. Leva de 0,2 a 1 segundo por quadro. Se este recurso não estiver completo nesta cópia, o Pascal usa o recorte clássico e avisa." },
    { k: "matte_style", t: "select", label: "Estilo da borda do cabelo", opts: [
      ["simples", "Simples (novo): contorno limpo e cabelo escuro sem buracos"], ["partes", "Por partes do corpo (versão anterior)"]],
      help: "Troque e compare no quadro ao vivo (leva 1 a 2 segundos). Nos dois estilos o vídeo final segura as piscadas claras do cabelo." },
    { k: "matte_mix", t: "range", label: "Recorte: cor original na borda do cabelo", min: 0, max: 1, step: 0.05, help: "0 = cor estimada pelo recorte (fios mais marcados, risco de tom oliva); 1 = cor do vídeo (contorno mais liso). Padrão 0,3." },
    { k: "matte_spill", t: "range", label: "Recorte: força do tira-verde", min: 0, max: 1, step: 0.05, help: "Tira o verde que sobra nas pontas do cabelo e em sombras. Não mexe em pele nem em roupa clara." },
    { k: "chroma_color", t: "color", label: "Cor do verde (chroma)", help: "Automático mede o verde de cada vídeo (recomendado). Desmarque para escolher uma cor." },
    { k: "similarity", t: "range", label: "Similaridade", min: 0.01, max: 0.40, step: 0.01, help: "Quanto some. Sobe se sobrar verde no fundo; desce se o sujeito ficar furado ou transparente." },
    { k: "blend", t: "range", label: "Suavidade da borda", min: 0, max: 0.20, step: 0.01, help: "Transição suave entre o que some e o que fica." },
    { k: "despill", t: "range", label: "Remoção de reflexo verde", min: 0, max: 1, step: 0.05, help: "Age só na faixa estreita da borda. O rosto e a roupa não são tocados." },
    { k: "hair_despill", t: "range", label: "Tirar verde do cabelo e das sombras verdes", min: 0, max: 1, step: 0.05, help: "Neutraliza o tom esverdeado do cabelo (reflexo do fundo). A pele e a roupa clara/oliva não são tocadas. 0 desliga." },
    { k: "edge_shade", t: "range", label: "Sombra na borda do cabelo", min: 0, max: 1, step: 0.05, help: "Escurece em degradê só o contorno (cabelo e ombros): some a bordinha clara. 0 desliga." },
    { k: "edge_soft", t: "range", label: "Suavidade do contorno", min: 0, max: 3, step: 0.1, unit: " px", help: "Degradê de transparência na ponta do cabelo: menos \"recortado\". 0 = bem definido." },
    { k: "hair_speckle", t: "range", label: "Apagar pontinhos claros no cabelo", min: 0, max: 1, step: 0.05, help: "Escurece pixels claros soltos no meio do cabelo (entregam o chroma key). 0 desliga." },
    { k: "edge_width", t: "range", label: "Largura da faixa de borda", min: 1, max: 12, step: 1, unit: " px", help: "Quão larga é a faixa onde o reflexo verde é corrigido (cabelo fino pede mais)." },
    { k: "choke", t: "range", label: "Encolher / limpar borda (choke)", min: 0, max: 5, step: 1, unit: " px", help: "Remove a linha verde fina ao redor de ombros e cabelo." },
    { k: "isolate", t: "check", label: "Apagar o que estiver ligado às bordas do quadro (parede, caixa, rebatedor, suporte)", help: "Só apaga o que encosta nas laterais ou no topo. A pessoa não é tocada." },
    { k: "clean", t: "range", label: "Descartar itens isolados (microfone, suporte)", min: 0, max: 20, step: 1, unit: " px", help: "Apaga objetos finos soltos no quadro. Se sumirem dedos ou fios de cabelo, diminua. 0 desliga." },
    { k: "trim", t: "range", label: "Descartar cantos do quadro", min: 0, max: 10, step: 0.5, unit: " %", help: "Apaga uma faixa nas laterais e no topo (onde costumam aparecer suportes). A parte de baixo não é tocada." },
  ]},
  { id: "luz", titulo: "Luz e cor", ctl: [
    { k: "auto_exposure", t: "check", label: "Exposição automática (mede o rosto e ajusta o brilho)" },
    { k: "light", t: "range", label: "Luz de estúdio no sujeito", min: 0, max: 1, step: 0.05, help: "Dá volume: um lado do corpo e a parte de baixo ficam mais escuros, o rosto fica em destaque. 0 desliga." },
    { k: "light_dir", t: "select", label: "Lado de onde vem a luz principal", opts: [["left", "Esquerda (sombra à direita)"], ["right", "Direita (sombra à esquerda)"]] },
    { k: "rim", t: "range", label: "Luz de recorte (contorno)", min: 0, max: 1, step: 0.05, help: "Brilho fino no contorno do lado oposto à luz. Se parecer artificial, deixe em 0." },
    { k: "warmth", t: "range", label: "Temperatura / aquecimento", min: 0, max: 40, step: 1, unit: " %", help: "Tira o aspecto branco/azulado de escritório." },
    { k: "contrast", t: "range", label: "Contraste de estúdio", min: 0.8, max: 1.6, step: 0.01 },
    { k: "gamma", t: "range", label: "Sombras (gamma)", min: 0.7, max: 1.3, step: 0.01, help: "Ajuste fino somado à exposição automática. Abaixo de 1 escurece." },
    { k: "brightness", t: "range", label: "Brilho geral", min: -0.2, max: 0.2, step: 0.01 },
    { k: "saturation", t: "range", label: "Saturação de pele", min: 0.5, max: 1.6, step: 0.01 },
    { k: "highlights", t: "range", label: "Brilho superior / highlights", min: 0, max: 1, step: 0.05, help: "Ganho leve nos tons altos, sem estourar." },
    { k: "black_point", t: "range", label: "Densidade do preto (anti-lavado)", min: 0, max: 0.06, step: 0.005, help: "Ancora o preto: cabelo e sombras ficam densos. Só escurece o preto; não clareia nada. 0 desliga." },
    { k: "black_lift", t: "range", label: "Preto menos preto (níveis)", min: 0, max: 0.08, step: 0.005, help: "Levanta o preto do sujeito (cabelo) sem clarear o fundo. Como o \"níveis de saída\" do Photoshop." },
    { k: "white_soft", t: "range", label: "Branco menos branco (níveis)", min: 0, max: 0.08, step: 0.005, help: "Abaixa o branco do sujeito." },
    { k: "grain", t: "range", label: "Grão fino de cinema", min: 0, max: 6, step: 0.5, help: "Evita faixas no fundo escuro. 0 desliga." },
  ]},
  { id: "nitidez", titulo: "Nitidez e tamanho", ctl: [
    { k: "resolution", t: "select", label: "Resolução final", opts: [
      ["1080p", "1080p Full HD (vertical ou horizontal)"], ["original", "Manter o tamanho original"]],
      help: "O sistema trabalha sempre em 1080p: o lado menor fica com 1080 px (1920x1080 na horizontal, 1080x1920 na vertical). Não existe 4K." },
    { k: "upscale_engine", t: "select", label: "Motor de upscaling", opts: [
      ["ffmpeg", "Rápido FFmpeg (lanczos + CAS + micro-nitidez)"], ["realesrgan", "Ampliação avançada — qualidade máxima, MUITO lenta"]],
      help: "A ampliação avançada só vale para saída MP4 (fundo de estúdio). Se este recurso não estiver completo nesta cópia, o Pascal usa o modo Rápido e avisa." },
    { k: "ai_model", t: "select", label: "Estilo da ampliação avançada", opts: [
      ["realesr-animevideov3", "Rápido (tende a alisar a pele — use a mistura)"],
      ["realesrgan-x4plus", "Natural (foto real, mais fiel, bem mais lento)"]] },
    { k: "ai_blend", t: "range", label: "Mistura da ampliação avançada", min: 0, max: 1, step: 0.05, help: "Quanto da ampliação avançada entra no resultado; o resto é o original ampliado pelo modo Rápido. 60% devolve fios de cabelo, cílios e tecido sem a cara de plástico." },
    { k: "clarity", t: "range", label: "Pegada / contraste local", min: 0, max: 1, step: 0.05, help: "Realça textura e volume (tecido, cabelo, pele). Alto demais cria halos." },
    { k: "sharp_method", t: "select", label: "Tipo de nitidez", opts: [["cas", "CAS (adaptativa)"], ["unsharp", "Unsharp (clássica)"]] },
    { k: "sharpen", t: "range", label: "Nitidez", min: 0, max: 1, step: 0.05, help: "0,45 melhora a definição sem ficar artificial." },
    { k: "denoise", t: "select", label: "Redução de ruído de imagem", opts: [["off", "Desligada"], ["leve", "Leve"], ["medio", "Média"], ["forte", "Forte"]],
      help: "Roda antes do recorte: deixa a borda do recorte estável." },
  ]},
  { id: "audio", titulo: "Áudio", ctl: [
    { k: "a_nr", t: "range", label: "Redução de ruído de fundo", min: 0, max: 100, step: 5, unit: " %", help: "Tira o chiado e o ruído constante da sala (filtro de wavelets). 0 desliga." },
    { k: "a_gate", t: "check", label: "Reduzir eco / cauda de sala entre as palavras" },
    { k: "a_room", t: "range", label: "Intensidade da redução de eco", min: 0, max: 100, step: 5, unit: " %", help: "Quanto mais alto, mais o som fraco entre as palavras (onde fica o eco) é abafado." },
    { k: "a_highpass", t: "range", label: "Corte de graves (rumble)", min: 20, max: 200, step: 5, unit: " Hz" },
    { k: "a_lowpass", t: "range", label: "Corte de agudos (chiado)", min: 8000, max: 20000, step: 500, unit: " Hz" },
    { k: "a_body", t: "range", label: "Corpo da voz (180 Hz)", min: -6, max: 8, step: 0.5, unit: " dB" },
    { k: "a_boxy", t: "range", label: "Tirar som de sala pequena (380 Hz)", min: -8, max: 4, step: 0.5, unit: " dB" },
    { k: "a_presence", t: "range", label: "Presença e clareza (3,5 kHz)", min: -6, max: 8, step: 0.5, unit: " dB" },
    { k: "a_air", t: "range", label: "Brilho / ar (9 kHz)", min: -6, max: 6, step: 0.5, unit: " dB" },
    { k: "a_comp", t: "check", label: "Compressor dinâmico (nivela a voz)" },
    { k: "a_loudnorm", t: "check", label: "Normalizar volume (padrão broadcast)" },
    { k: "a_lufs", t: "range", label: "Volume final (LUFS)", min: -23, max: -10, step: 1, help: "-14 é o padrão de internet; -16 é mais suave." },
  ]},
];

// Aba "Essencial": os ajustes que mais mudam o resultado, reaproveitando as definições das outras abas.
const ESSENCIAL = ["light", "warmth", "contrast", "saturation", "gamma", "sharpen", "clarity", "edge_soft", "hair_despill", "matte_mix", "despill", "a_lufs"];
(function addEssencial() {
  const all = {};
  TABS.forEach((t) => t.ctl.forEach((c) => { all[c.k] = c; }));
  TABS.unshift({ id: "essencial", titulo: "⭐ Essencial", ctl: ESSENCIAL.filter((k) => all[k]).map((k) => all[k]) });
})();

const SLOW_KEYS = new Set(["matte_mix", "matte_spill", "matte_engine", "resolution", "mod_upscale", "chroma_color"]);

let settings = {};
let defaults = {};
let currentPath = "";
let currentInfo = null;
let activeJob = null;
let pollTimer = null;
const controls = {};   // k -> [setters]  (um ajuste pode aparecer em mais de uma aba)

function buildTabs() {
  const tabs = $("tabs"), panels = $("panels");
  TABS.forEach((tab, i) => {
    const b = document.createElement("button");
    b.textContent = tab.titulo;
    b.onclick = () => showTab(tab.id);
    b.dataset.tab = tab.id;
    tabs.appendChild(b);
    const p = document.createElement("div");
    p.className = "panel";
    p.id = "panel_" + tab.id;
    tab.ctl.forEach((c) => p.appendChild(buildControl(c)));
    panels.appendChild(p);
    if (i === 0) showTab(tab.id);
  });
}

function showTab(id) {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === id));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("on", p.id === "panel_" + id));
}

function fmt(v, c) {
  const step = c.step || 1;
  const dec = step < 0.1 ? 2 : step < 1 ? 1 : 0;
  return Number(v).toFixed(dec).replace(".", ",") + (c.unit || "");
}

function syncAll(k) { (controls[k] || []).forEach((f) => f(settings[k])); }

function buildControl(c) {
  const wrap = document.createElement("div");
  wrap.className = "ctl";
  const top = document.createElement("div");
  top.className = "top";
  const lab = document.createElement("label");
  lab.textContent = c.label;
  top.appendChild(lab);
  const val = document.createElement("span");
  val.className = "val";
  top.appendChild(val);
  wrap.appendChild(top);
  let setter;

  if (c.t === "range") {
    const r = document.createElement("input");
    r.type = "range"; r.min = c.min; r.max = c.max; r.step = c.step;
    r.oninput = () => { settings[c.k] = parseFloat(r.value); syncAll(c.k); touch(c.k); };
    r.ondblclick = () => { if (c.k in defaults) { settings[c.k] = defaults[c.k]; syncAll(c.k); touch(c.k); } };
    r.title = "Dê dois cliques para voltar ao valor padrão";
    wrap.appendChild(r);
    setter = (v) => { r.value = v; val.textContent = fmt(v, c); };
  } else if (c.t === "select") {
    const s = document.createElement("select");
    c.opts.forEach(([v, t]) => { const o = document.createElement("option"); o.value = v; o.textContent = t; s.appendChild(o); });
    s.onchange = () => { settings[c.k] = s.value; if (c.k === "bg_mode") syncTransp(); touch(c.k); };
    s.style.width = "100%"; s.style.marginTop = "6px";
    wrap.appendChild(s);
    setter = (v) => { s.value = v; };
  } else if (c.t === "check") {
    const l = lab; l.textContent = "";
    const i = document.createElement("input");
    i.type = "checkbox";
    i.onchange = () => { settings[c.k] = i.checked; syncAll(c.k); touch(c.k); };
    l.appendChild(i); l.appendChild(document.createTextNode(" " + c.label));
    setter = (v) => { i.checked = !!v; };
  } else if (c.t === "color") {
    const box = document.createElement("div");
    box.className = "inl";
    const autoBox = document.createElement("label");
    autoBox.style.cssText = "display:flex;gap:6px;align-items:center";
    const autoChk = document.createElement("input"); autoChk.type = "checkbox";
    autoBox.append(autoChk, document.createTextNode("Automático"));
    const col = document.createElement("input"); col.type = "color";
    const hex = document.createElement("input"); hex.type = "text"; hex.style.maxWidth = "110px";
    const auto = document.createElement("button"); auto.textContent = "Medir agora";
    const refresh = () => { col.disabled = hex.disabled = autoChk.checked; };
    autoChk.onchange = () => {
      settings[c.k] = autoChk.checked ? "auto" : (/^#[0-9a-f]{6}$/i.test(hex.value) ? hex.value.toLowerCase() : "#95e591");
      if (!autoChk.checked) { hex.value = settings[c.k]; col.value = settings[c.k]; }
      refresh(); touch(c.k);
    };
    col.oninput = () => { settings[c.k] = col.value; hex.value = col.value; touch(c.k); };
    hex.onchange = () => { if (/^#[0-9a-fA-F]{6}$/.test(hex.value)) { settings[c.k] = hex.value.toLowerCase(); col.value = hex.value; touch(c.k); } };
    auto.onclick = async () => {
      if (!currentPath) { alert(T("Escolha o vídeo primeiro.")); return; }
      try {
        const r = await api("/api/autodetect", { path: currentPath, at: live.at });
        settings[c.k] = r.color; col.value = r.color; hex.value = r.color; autoChk.checked = false; refresh(); touch(c.k);
      } catch (e) { alert(T(e.message)); }
    };
    box.append(autoBox, col, hex, auto);
    wrap.appendChild(box);
    setter = (v) => {
      autoChk.checked = (v === "auto");
      if (v !== "auto") { col.value = v; hex.value = v; }
      refresh();
    };
  }
  if (c.help) {
    const h = document.createElement("div");
    h.className = "help"; h.textContent = c.help;
    wrap.appendChild(h);
  }
  (controls[c.k] = controls[c.k] || []).push(setter);
  return wrap;
}

// ------------------------------------------------------------------ estado <-> tela
const MODS = ["mod_chroma", "mod_grade", "mod_upscale", "mod_audio"];

function applySettings(s) {
  settings = Object.assign({}, defaults, s);
  for (const k in controls) if (k in settings) syncAll(k);
  MODS.forEach((k) => { $(k).checked = !!settings[k]; });
  syncTransp();
  touch("*");
}

function syncTransp() {
  $("transp").checked = settings.bg_mode !== "studio_mp4";
  $("transp").disabled = !settings.mod_chroma;
}

MODS.forEach((k) => {
  $(k).onchange = () => { settings[k] = $(k).checked; syncTransp(); touch(k); };
});
$("transp").onchange = () => {
  settings.bg_mode = $("transp").checked
    ? (settings.bg_mode === "alpha_qtrle" ? "alpha_qtrle" : "alpha_prores") : "studio_mp4";
  syncAll("bg_mode");
  touch("bg_mode");
};

// ------------------------------------------------------------------ vídeo
function mmss(t) { const m = Math.floor(t / 60), s = Math.floor(t % 60); return `${m}:${String(s).padStart(2, "0")}`; }

async function loadVideo(path) {
  try {
    const info = await api("/api/probe", { path });
    currentPath = info.path; currentInfo = info;
    $("path").value = info.path;
    if (info.out_dir) showOutDir(info.out_dir);
    const d = info.duration, m = Math.floor(d / 60), s = Math.round(d % 60);
    $("info").textContent = `${info.width}×${info.height} · ${info.fps.toFixed(2).replace(".", ",")} fps · ${m}min${String(s).padStart(2, "0")}s · ${info.has_audio ? "com áudio" : "sem áudio"}`;
    const sl = $("atSlider");
    sl.max = Math.max(1, Math.floor(d - 1));
    live.at = Math.min(live.at, parseFloat(sl.max));
    if (live.at < 1 && d > 12) live.at = 10;
    sl.value = live.at; $("atLabel").textContent = mmss(live.at);
    settings.preview_start = live.at;
    live.origKey = ""; live.first = true;
    $("liveMsg").textContent = "Preparando o quadro…";
    $("liveMsg").hidden = false;
    touch("*", true);
  } catch (e) {
    currentPath = ""; currentInfo = null;
    $("info").textContent = e.message;
  }
}

$("btnBrowse").onclick = async () => {
  $("btnBrowse").disabled = true;
  try {
    const r = await api("/api/browse", {});
    if (r.path) await loadVideo(r.path);
  } catch (e) { alert(T("Não consegui abrir a janela de escolha. Cole o caminho do vídeo no campo ao lado.") + "\n" + T(e.message)); }
  $("btnBrowse").disabled = false;
};
$("path").onchange = () => { if ($("path").value.trim()) loadVideo($("path").value.trim()); };
$("inputList").onchange = () => { if ($("inputList").value) loadVideo($("inputList").value); };

// ------------------------------------------------------------------ pasta de saída
function showOutDir(d) { $("outDir").textContent = d; $("outDir").title = d; $("outDirText").value = d; }
$("btnFolder").onclick = async () => {
  $("btnFolder").disabled = true;
  try { showOutDir((await api("/api/browse-folder", {})).dir); }
  catch (e) { alert(T("Não consegui abrir a janela de escolha. Digite o caminho em 'Digitar o caminho da pasta'.") + "\n" + T(e.message)); }
  $("btnFolder").disabled = false;
};
$("btnSetFolder").onclick = async () => {
  try { showOutDir((await api("/api/set-folder", { dir: $("outDirText").value.trim() })).dir); }
  catch (e) { alert(T(e.message)); }
};
$("btnOpenOut").onclick = () => api("/api/open-output", {});
$("btnVideoFolder").onclick = async () => {
  try { await api("/api/reset-folder", {}); if (currentPath) { const i = await api("/api/probe", { path: currentPath }); showOutDir(i.out_dir); } }
  catch (e) { alert(T(e.message)); }
};
// avisa o servidor que a janela fechou (o próximo ping, se for só um recarregamento, cancela o aviso)
window.addEventListener("pagehide", () => { try { fetch(`/api/bye?k=${TOKEN}`, { keepalive: true }); } catch (e) { /* ignora */ } });

// ------------------------------------------------------------------ QUADRO AO VIVO
const live = {
  at: 10, seq: 0, inflight: false, pending: false, timer: null, first: true,
  w: 1920, h: 1080, scale: 1, x: 0, y: 0, fit: true, transparent: false, cmp: "proc", split: 0.5,
  procKey: "", origKey: "", hasProc: false, hasOrig: false,
};
const vp = $("viewport"), layer = $("layer"), imgP = $("imgProc"), imgO = $("imgOrig");

function touch(key, now) {
  if (!currentPath) return;
  if (live.inflight && Date.now() - (live.inflightSince || 0) > 150000) { live.inflight = false; live.pending = false; setBusy(""); }   // pedido preso: solta
  clearTimeout(live.timer);
  live.timer = setTimeout(runLive, now ? 0 : (SLOW_KEYS.has(key) ? 800 : 160));
}

function setBusy(txt) {
  $("liveBusy").hidden = !txt;
  if (txt) $("liveBusyText").textContent = txt;
}

async function frameJob(orig) {
  const r = await api("/api/frame", { path: currentPath, at: live.at, settings, orig, seq: ++live.seq });
  for (;;) {
    await new Promise((res) => setTimeout(res, 220));
    const j = await api("/api/frame/status?id=" + r.id);
    if (j.state === "running") { setBusy(j.message); continue; }
    return j;
  }
}

function loadImg(img, name) {
  return new Promise((resolve, reject) => {
    const pre = new Image();
    pre.onload = () => { img.src = pre.src; img.style.width = pre.naturalWidth + "px"; img.style.height = pre.naturalHeight + "px"; resolve(pre); };
    pre.onerror = () => reject(new Error("Não consegui carregar o quadro."));
    pre.src = mediaUrl(name);
  });
}

async function runLive() {
  if (!currentPath || $("modeVideo").classList.contains("on")) return;
  if (live.inflight) { live.pending = true; return; }
  live.inflight = true; live.inflightSince = Date.now();
  try {
    const j = await frameJob(false);
    if (j.state === "done") {
      const pre = await loadImg(imgP, j.out_name);
      const sizeChanged = pre.naturalWidth !== live.w || pre.naturalHeight !== live.h;
      live.w = pre.naturalWidth; live.h = pre.naturalHeight; live.transparent = !!j.transparent;
      live.hasProc = true;
      $("liveMsg").hidden = true;
      $("pxInfo").textContent = `${live.w}×${live.h} px`;
      if (live.first || sizeChanged) { live.first = false; fitView(); }
      applyView();
      applyBg();
      vp.classList.add("flash"); setTimeout(() => vp.classList.remove("flash"), 220);
    } else if (j.state === "stale") {
      live.pending = true;        // um pedido mais novo tomou o lugar: refaz com os ajustes atuais
    } else if (j.state === "error") {
      $("liveMsg").hidden = false;
      $("liveMsg").textContent = "⚠ " + j.error;
    }
    if (live.cmp !== "proc") await ensureOrig();
  } catch (e) {
    if (/rodando/.test(e.message)) { setBusy("Aguardando o teste/render terminar…"); await new Promise((r) => setTimeout(r, 1800)); }
    else { $("liveMsg").hidden = false; $("liveMsg").textContent = "⚠ " + e.message; }
  }
  setBusy("");
  live.inflight = false;
  if (live.pending) { live.pending = false; runLive(); }
}

async function ensureOrig() {
  const key = currentPath + "|" + live.at + "|" + live.w + "x" + live.h;
  if (live.origKey === key && live.hasOrig) return;
  const j = await frameJob(true);
  if (j.state === "done") { await loadImg(imgO, j.out_name); live.origKey = key; live.hasOrig = true; applyView(); }
}

function fitView() {
  const r = vp.getBoundingClientRect();
  live.scale = Math.min(r.width / live.w, r.height / live.h);
  live.x = (r.width - live.w * live.scale) / 2;
  live.y = (r.height - live.h * live.scale) / 2;
  live.fit = true;
  markZoom("fit");
}

function applyView() {
  layer.style.transform = `translate(${live.x}px,${live.y}px) scale(${live.scale})`;
  layer.classList.toggle("pix", live.scale >= 2);
  imgP.style.visibility = live.hasProc && live.cmp !== "orig" ? "visible" : "hidden";
  imgO.style.visibility = live.hasOrig && live.cmp !== "proc" ? "visible" : "hidden";
  const sl = $("splitLine");
  sl.hidden = live.cmp !== "split";
  imgP.style.clipPath = imgO.style.clipPath = "";
  if (live.cmp === "split") {
    const p = live.split * 100;
    imgO.style.clipPath = `inset(0 ${100 - p}% 0 0)`;
    imgP.style.clipPath = `inset(0 0 0 ${p}%)`;
    const xs = live.x + live.split * live.w * live.scale;
    sl.style.left = xs + "px";
    $("splitTagL").style.left = Math.max(6, xs - 10 - $("splitTagL").offsetWidth) + "px";
    $("splitTagR").style.left = Math.min(vp.clientWidth - $("splitTagR").offsetWidth - 6, xs + 10) + "px";
  }
  $("splitTagL").hidden = $("splitTagR").hidden = live.cmp !== "split";
}

let customBg = "";          // cor escolhida no seletor livre ("" = vale um dos quadradinhos)
let previewAlpha = false;   // o teste de 5 s atual tem transparência de verdade (WebM)
function currentBg() {
  const b = document.querySelector("#bgSeg button.on");
  return b ? b.dataset.bg : (customBg || "#000");
}
function applyBg() {
  const bg = currentBg();
  vp.classList.toggle("check", live.transparent && bg === "check");
  vp.style.background = live.transparent ? (bg === "check" ? "" : bg) : "#000";
  const vw = $("videoWrap");
  vw.classList.toggle("check", previewAlpha && bg === "check");
  vw.style.background = previewAlpha ? (bg === "check" ? "" : bg) : "#000";
  $("bgBox").style.opacity = (live.transparent || previewAlpha) ? "1" : ".5";
}

function markZoom(z) { document.querySelectorAll("#zoomSeg button").forEach((b) => b.classList.toggle("on", b.dataset.z === String(z))); }

function zoomTo(s, cx, cy) {
  const r = vp.getBoundingClientRect();
  if (cx === undefined) { cx = r.width / 2; cy = r.height / 2; }
  s = Math.max(0.05, Math.min(24, s));
  live.x = cx - (cx - live.x) * s / live.scale;
  live.y = cy - (cy - live.y) * s / live.scale;
  live.scale = s; live.fit = false;
  applyView();
}

document.querySelectorAll("#zoomSeg button").forEach((b) => {
  b.onclick = () => {
    if (b.dataset.z === "fit") { fitView(); applyView(); return; }
    zoomTo(parseFloat(b.dataset.z)); markZoom(b.dataset.z);
  };
});
vp.addEventListener("wheel", (e) => {
  e.preventDefault();
  const r = vp.getBoundingClientRect();
  zoomTo(live.scale * (e.deltaY < 0 ? 1.18 : 1 / 1.18), e.clientX - r.left, e.clientY - r.top);
  markZoom("");
}, { passive: false });

let drag = null;
vp.addEventListener("mousedown", (e) => {
  if (e.target.closest("#splitLine")) { drag = { split: true }; return; }
  drag = { sx: e.clientX, sy: e.clientY, x0: live.x, y0: live.y };
  vp.classList.add("drag");
});
window.addEventListener("mousemove", (e) => {
  if (!drag) return;
  if (drag.split) {
    const r = vp.getBoundingClientRect();
    live.split = Math.max(0.02, Math.min(0.98, (e.clientX - r.left - live.x) / (live.w * live.scale)));
    applyView(); return;
  }
  live.x = drag.x0 + e.clientX - drag.sx; live.y = drag.y0 + e.clientY - drag.sy; live.fit = false;
  applyView();
});
window.addEventListener("mouseup", () => { drag = null; vp.classList.remove("drag"); });
window.addEventListener("resize", () => { if (live.fit && live.hasProc) { fitView(); applyView(); } });
new ResizeObserver(() => { if (live.hasProc) { if (live.fit) fitView(); applyView(); } }).observe(vp);   // divisória, tela cheia, painel escondido
vp.addEventListener("dblclick", (e) => { if (!e.target.closest("#splitLine")) { fitView(); applyView(); } });

// comparar: Pascal / dividido / original
function setCmp(c) {
  live.cmp = c;
  [["cmpProc", "proc"], ["cmpSplit", "split"], ["cmpOrig", "orig"]].forEach(([id, v]) => $(id).classList.toggle("on", v === c));
  applyView();
  if (c !== "proc" && currentPath) { if (live.inflight) live.pending = true; else { live.inflight = true; ensureOrig().catch(() => {}).finally(() => { live.inflight = false; setBusy(""); applyView(); if (live.pending) { live.pending = false; runLive(); } }); } }
}
$("cmpProc").onclick = () => setCmp("proc");
$("cmpSplit").onclick = () => setCmp("split");
$("cmpOrig").onclick = () => setCmp("orig");

document.querySelectorAll("#bgSeg button").forEach((b) => {
  b.onclick = () => { document.querySelectorAll("#bgSeg button").forEach((x) => x.classList.toggle("on", x === b)); $("bgPickBox").classList.remove("on"); applyBg(); };
});
$("bgPick").addEventListener("input", () => {
  customBg = $("bgPick").value;
  document.querySelectorAll("#bgSeg button").forEach((x) => x.classList.remove("on"));
  $("bgPickBox").classList.add("on");
  applyBg();
});

// linha do tempo (qual quadro mostrar)
$("atSlider").oninput = () => { $("atLabel").textContent = mmss(parseFloat($("atSlider").value)); };
$("atSlider").onchange = () => {
  live.at = parseFloat($("atSlider").value);
  settings.preview_start = live.at;
  live.hasOrig = false;
  touch("*", true);
};

// modo: quadro ao vivo / vídeo de teste
function setMode(m) {
  const isLive = m === "live";
  $("modeLive").classList.toggle("on", isLive);
  $("modeVideo").classList.toggle("on", !isLive);
  $("liveWrap").hidden = !isLive;
  $("videoWrap").hidden = isLive;
  $("cmpSeg").style.display = $("zoomSeg").style.display = isLive ? "" : "none";
  $("bgBox").style.display = (isLive || previewAlpha) ? "" : "none";
  $("abBar").hidden = isLive || !previewNames.orig;
  if (isLive) { fitView(); applyView(); touch("*", true); }
}
$("modeLive").onclick = () => setMode("live");
$("modeVideo").onclick = () => setMode("video");

// ------------------------------------------------------------------ trabalhos (teste de 5 s e render)
function setJobBusy(busy) {
  ["btnPreview", "btnRender"].forEach((id) => { $(id).disabled = busy; });
  $("progressBox").hidden = !busy && !activeJob;
}

async function startJob(kind) {
  if (!currentPath) { alert(T("Escolha o vídeo primeiro.")); return; }
  $("result").hidden = true;
  $("reportBox").hidden = true;
  setJobBusy(true);
  $("progressBox").hidden = false;
  $("bar").style.width = "0%";
  $("progressText").textContent = "Preparando…";
  try {
    settings.preview_start = live.at;
    const r = await api(kind === "preview" ? "/api/preview" : "/api/render", { path: currentPath, settings });
    activeJob = { id: r.id, kind };
    poll();
  } catch (e) {
    setJobBusy(false);
    showResult(e.message, true);
  }
}

async function poll() {
  clearTimeout(pollTimer);
  if (!activeJob) return;
  try {
    const j = await api("/api/job?id=" + activeJob.id);
    $("bar").style.width = j.progress.toFixed(1) + "%";
    $("progressText").textContent = `${j.progress.toFixed(0)}% — ${j.message}${j.speed ? " (" + j.speed + ")" : ""}`;
    $("awakeNote").hidden = !(j.state === "running" && j.keep_awake);
    if (j.state === "running") { pollTimer = setTimeout(poll, 700); return; }
    const kind = activeJob.kind;
    activeJob = null;
    setJobBusy(false);
    $("progressBox").hidden = true;
    if (j.state === "done") {
      if (kind === "preview") {
        showPreview(j.out_name, j.orig_name, !!j.alpha); setMode("video");
        if (j.sample) showResult("Amostra de 5 segundos salva em:\n" + j.sample, false, true);
      }
      else showResult("Pronto! O vídeo foi salvo em:\n" + j.out, false, true);
      showReport(j);
    } else if (j.state === "error") {
      showResult("O FFmpeg falhou:\n" + j.error, true);
    } else {
      showResult("Cancelado.", true);
    }
  } catch (e) {
    activeJob = null; setJobBusy(false);
    showResult(e.message, true);
  }
}

let previewNames = { proc: "", orig: "" };

function mediaUrl(name) { return `/media/${encodeURIComponent(name)}?k=${TOKEN}&t=${Date.now()}`; }

function switchAB(which) {
  const v = $("video");
  const name = previewNames[which];
  if (!name) return;
  const t = v.currentTime, paused = v.paused;
  v.src = mediaUrl(name);
  v.onloadedmetadata = () => { try { v.currentTime = t; } catch (e) { /* ignora */ } if (!paused) v.play().catch(() => {}); };
  $("btnProc").classList.toggle("on", which === "proc");
  $("btnOrig").classList.toggle("on", which === "orig");
}
$("btnProc").onclick = () => switchAB("proc");
$("btnOrig").onclick = () => switchAB("orig");
$("btnLogs").onclick = () => api("/api/open-logs", {});

async function showReport(j) {
  const box = $("report");
  $("reportBox").hidden = false;
  box.innerHTML = "";
  const alerts = j.alerts || [];
  $("reportSum").textContent = alerts.length ? `⚠ Relatório do teste: ${alerts.length} aviso(s) — clique para ver` : "Relatório do teste: sem alertas (clique para ver)";
  $("reportSum").classList.toggle("bad", alerts.length > 0);
  $("reportBox").open = false;
  if (alerts.length) {
    alerts.forEach((a) => { const d = document.createElement("div"); d.className = "alertbox"; d.textContent = "⚠ " + a; box.appendChild(d); });
  } else {
    const d = document.createElement("div"); d.className = "okbox"; d.textContent = "Diagnóstico automático: sem alertas."; box.appendChild(d);
  }
  try {
    const r = await api("/api/report?id=" + j.id);
    const det = document.createElement("details");
    const sum = document.createElement("summary"); sum.textContent = "Relatório completo (também salvo em " + (r.dir || "logs") + ")";
    const pre = document.createElement("pre"); pre.textContent = r.text || "(vazio)";
    det.append(sum, pre); box.appendChild(det);
  } catch (e) { /* sem relatório */ }
}

function showPreview(name, orig, alpha) {
  const v = $("video");
  previewAlpha = !!alpha;
  previewNames = { proc: name, orig: orig || "" };
  $("abBar").hidden = !orig;
  $("btnProc").classList.add("on"); $("btnOrig").classList.remove("on");
  v.src = mediaUrl(name);
  v.style.display = "block";
  $("videoEmpty").style.display = "none";
  v.load();
  v.play().catch(() => {});
  $("previewNote").textContent = previewAlpha
    ? "Fundo transparente: escolha a cor de fundo nos quadradinhos (ou em “colorido”) para ver o contorno do cabelo e dos ombros em cada cor."
    : "";
  $("bgBox").style.display = previewAlpha || $("modeLive").classList.contains("on") ? "" : "none";
  applyBg();
}

function showResult(text, isErr, openBtn) {
  const r = $("result");
  r.hidden = false;
  r.className = "result" + (isErr ? " err" : "");
  r.textContent = text;
  if (openBtn) {
    r.appendChild(document.createElement("br"));
    const b = document.createElement("button");
    b.textContent = "Abrir a pasta"; b.className = "small";
    b.onclick = () => api("/api/open-output", {});
    r.appendChild(b);
  }
}

$("btnPreview").onclick = () => startJob("preview");
$("btnRender").onclick = async () => {
  if (currentPath && settings.upscale_engine === "realesrgan" && settings.mod_upscale && settings.bg_mode === "studio_mp4") {
    try {
      $("progressText").textContent = "Estimando o tempo da ampliação avançada…"; $("progressBox").hidden = false;
      const r = await api("/api/ai/estimate", { path: currentPath, settings });
      $("progressBox").hidden = true;
      if (!confirm(T(`Render com ampliação avançada: cerca de ${r.seconds_per_frame.toFixed(1)} s por quadro × ${r.frames} quadros = ${r.eta}. Continuar?`))) return;
    } catch (e) { $("progressBox").hidden = true; alert(T(e.message + "\n\nVai usar o modo Rápido FFmpeg.")); }
  }
  if (settings.mod_chroma && settings.bg_mode === "alpha_prores" && currentInfo && currentInfo.duration > 600) {
    if (!confirm(T("O ProRes 4444 com transparência gera arquivos MUITO grandes (cerca de 2,5 GB por minuto de vídeo). Continuar?"))) return;
  }
  startJob("render");
};
$("btnCancel").onclick = async () => { if (activeJob) await api("/api/cancel", { id: activeJob.id }); };

// ------------------------------------------------------------------ ajustes salvos
async function refreshPresets(list) {
  const sel = $("presetList");
  sel.innerHTML = "";
  (list || []).forEach((n) => { const o = document.createElement("option"); o.textContent = n; o.value = n; sel.appendChild(o); });
}
$("btnReset").onclick = () => applySettings(defaults);
$("btnSavePreset").onclick = async () => {
  const name = $("presetName").value.trim();
  if (!name) { alert(T("Digite um nome para o ajuste.")); return; }
  try {
    const r = await api("/api/preset/save", { name, settings });
    const st = await api("/api/state");
    await refreshPresets(st.user_presets);
    $("presetList").value = r.name;
  } catch (e) { alert(T(e.message)); }
};
$("btnLoadPreset").onclick = async () => {
  const n = $("presetList").value;
  if (!n) return;
  try { applySettings(await api("/api/preset?name=" + encodeURIComponent(n))); } catch (e) { alert(T(e.message)); }
};
$("btnExport").onclick = () => {
  const blob = new Blob([JSON.stringify(settings, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "meus_ajustes_pascal.json"; a.click();
};
$("fileImport").onchange = async (ev) => {
  const f = ev.target.files[0];
  if (!f) return;
  try { applySettings(JSON.parse(await f.text())); } catch (e) { alert(T("Arquivo de ajustes inválido.")); }
  ev.target.value = "";
};

$("btnQuit").onclick = async () => {
  if (!confirm(T("Fechar o Pascal?"))) return;
  try { await api("/api/quit", {}); } catch (e) { /* o servidor fecha antes de responder */ }
  window.close();
};

// ------------------------------------------------------------------ ajuda (FAQ e passo a passo)
function mdToHtml(md) {
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`(.+?)`/g, "<code>$1</code>");
  const out = []; let list = null;
  const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
  md.split(/\r?\n/).forEach((line) => {
    let m;
    if ((m = line.match(/^(#{1,3})\s+(.*)/))) { close(); out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); }
    else if ((m = line.match(/^\s*[-*]\s+(.*)/))) { if (list !== "ul") { close(); out.push("<ul>"); list = "ul"; } out.push(`<li>${inline(m[1])}</li>`); }
    else if ((m = line.match(/^\s*\d+\.\s+(.*)/))) { if (list !== "ol") { close(); out.push("<ol>"); list = "ol"; } out.push(`<li>${inline(m[1])}</li>`); }
    else if ((m = line.match(/^>\s?(.*)/))) { close(); out.push(`<blockquote>${inline(m[1])}</blockquote>`); }
    else if (/^---+$/.test(line.trim())) { close(); }
    else if (!line.trim()) { close(); }
    else { close(); out.push(`<p>${inline(line)}</p>`); }
  });
  close();
  return out.join("\n");
}
let currentDoc = "faq";
async function showDoc(name) {
  currentDoc = name;
  $("docFaq").classList.toggle("on", name === "faq");
  $("docSteps").classList.toggle("on", name !== "faq");
  $("docBody").textContent = "Carregando…";
  try { $("docBody").innerHTML = mdToHtml(await (await fetch("/doc/" + name + "?lang=" + (window.I18N ? window.I18N.lang : "pt"))).text()); }
  catch (e) { $("docBody").textContent = "Não consegui abrir o texto de ajuda."; }
}
window.addEventListener("pascal-lang", () => { if (!$("helpModal").hidden) showDoc(currentDoc); });   // botão PT/EN com a ajuda aberta: troca o texto
$("btnHelp").onclick = () => { $("helpModal").hidden = false; showDoc("faq"); };
$("docFaq").onclick = () => showDoc("faq");
$("docSteps").onclick = () => showDoc("passo-a-passo");
$("helpClose").onclick = () => { $("helpModal").hidden = true; };
$("helpModal").onclick = (e) => { if (e.target === $("helpModal")) $("helpModal").hidden = true; };

// ------------------------------------------------------------------ ampliação avançada
function buildAiBox(ai) {
  const panel = $("panel_nitidez");
  if (!panel || !ai) return;
  const box = document.createElement("div");
  box.className = "ctl";
  box.style.gridColumn = "1 / -1";
  const st = document.createElement("div");
  st.className = "help";
  st.textContent = ai.available
    ? "Ampliação avançada disponível" + (ai.gpu ? " · placa de vídeo: " + ai.gpu : "") + ". Estimativa de tempo e teste em 3 quadros abaixo."
    : "A ampliação avançada não está instalada nesta cópia do Pascal. O modo Rápido será usado e já dá um bom resultado.";
  const row = document.createElement("div");
  row.className = "inl";
  const bTest = document.createElement("button"); bTest.textContent = "Testar em 3 quadros"; bTest.disabled = !ai.available;
  const bEst = document.createElement("button"); bEst.textContent = "Estimar o tempo do render"; bEst.disabled = !ai.available;
  const out = document.createElement("div"); out.className = "help"; out.id = "aiOut"; out.style.marginTop = "6px";
  const imgs = document.createElement("div"); imgs.id = "aiImgs";
  row.append(bTest, bEst);
  box.append(st, row, out, imgs);
  panel.appendChild(box);
  bEst.onclick = async () => {
    if (!currentPath) { alert(T("Escolha o vídeo primeiro.")); return; }
    out.textContent = "Medindo a velocidade da sua placa (na primeira vez leva cerca de 1 minuto)…";
    try {
      const r = await api("/api/ai/estimate", { path: currentPath, settings });
      out.textContent = `≈ ${r.seconds_per_frame.toFixed(1)} s por quadro · ${r.frames} quadros · render completo ≈ ${r.eta}.`;
    } catch (e) { out.textContent = e.message; }
  };
  bTest.onclick = async () => {
    if (!currentPath) { alert(T("Escolha o vídeo primeiro.")); return; }
    out.textContent = "Processando 3 quadros…"; imgs.innerHTML = "";
    try {
      const r = await api("/api/ai/test", { path: currentPath, settings });
      for (;;) {
        await new Promise((res) => setTimeout(res, 1500));
        const j = await api("/api/job?id=" + r.id);
        if (j.state === "running") continue;
        if (j.state !== "done") { out.textContent = j.error || "Falhou."; return; }
        out.textContent = `${j.legend}. Velocidade medida: ${j.seconds_per_frame.toFixed(1)} s por quadro.`;
        (j.images || []).forEach((n) => { const im = document.createElement("img"); im.src = mediaUrl(n); im.style.cssText = "width:100%;margin-top:6px;border-radius:6px"; imgs.appendChild(im); });
        return;
      }
    } catch (e) { out.textContent = e.message; }
  };
}

// ------------------------------------------------------------------ início
(async function init() {
  buildTabs();
  setMode("live");
  try {
    const st = await api("/api/state");
    defaults = st.default;
    settings = Object.assign({}, defaults);
    applySettings(defaults);
    if (!currentPath) showOutDir(st.output_dir);
    $("alertFfmpeg").hidden = st.ffmpeg_ok;
    refreshPresets(st.user_presets);
    buildAiBox(st.ai);
    if (st.input_files.length) {
      $("inputListRow").hidden = false;
      const sel = $("inputList");
      sel.innerHTML = '<option value="">— ou escolha um vídeo da pasta input —</option>';
      st.input_files.forEach((n) => { const o = document.createElement("option"); o.value = n; o.textContent = n; sel.appendChild(o); });
    }
  } catch (e) {
    $("info").textContent = "Erro ao iniciar: " + e.message;
  }
  setInterval(() => { api("/api/ping").catch(() => {}); }, 5000);
  api("/api/ping").catch(() => {});
  const q = new URLSearchParams(location.search);   // atalho: abrir com ?v=CAMINHO_DO_VIDEO&at=SEGUNDOS
  if (q.get("at")) live.at = parseFloat(q.get("at")) || live.at;
  if (q.get("v")) loadVideo(q.get("v"));
})();

// ------------------------------------------------------------------ jeito de aplicativo (layout, tela cheia, sem zoom de página)
const LS = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignora */ } },
};
(function initLayout() {
  const h = parseInt(LS.get("pascal.setH", "0"), 10);
  if (h > 0) document.documentElement.style.setProperty("--set-h", h + "px");   // só se a pessoa já arrastou a divisória; senão vale o padrão do CSS
  if (LS.get("pascal.noset", "0") === "1") document.body.classList.add("noset");
  if (LS.get("pascal.noaside", "0") === "1") document.body.classList.add("noaside");
  syncLayoutButtons();
  const pb = $("presetsBox");           // "Meus ajustes salvos": começa recolhido (só o título) e lembra se a pessoa abriu
  pb.open = LS.get("pascal.presetsOpen", "0") === "1";
  pb.addEventListener("toggle", () => LS.set("pascal.presetsOpen", pb.open ? "1" : "0"));
})();
function syncLayoutButtons() {
  $("btnSetHide").textContent = document.body.classList.contains("noset") ? "▴ Mostrar ajustes" : "▾ Esconder ajustes";
  $("btnAside").classList.toggle("on", document.body.classList.contains("noaside"));
}
function toggleSet() { document.body.classList.toggle("noset"); LS.set("pascal.noset", document.body.classList.contains("noset") ? "1" : "0"); syncLayoutButtons(); }
function toggleAside() { document.body.classList.toggle("noaside"); LS.set("pascal.noaside", document.body.classList.contains("noaside") ? "1" : "0"); syncLayoutButtons(); }
$("btnSetHide").onclick = toggleSet;
$("btnAside").onclick = toggleAside;
$("splitter").addEventListener("dblclick", toggleSet);
(function splitterDrag() {
  const sp = $("splitter");
  let on = false;
  sp.addEventListener("pointerdown", (e) => { on = true; sp.classList.add("drag"); sp.setPointerCapture(e.pointerId); document.body.classList.remove("noset"); syncLayoutButtons(); e.preventDefault(); });
  sp.addEventListener("pointermove", (e) => {
    if (!on) return;
    const r = $("stage").getBoundingClientRect();
    const px = Math.round(Math.max(110, Math.min(r.bottom - e.clientY - 7, r.height - 170)));
    document.documentElement.style.setProperty("--set-h", px + "px");
    LS.set("pascal.setH", String(px));
  });
  const end = () => { on = false; sp.classList.remove("drag"); };
  sp.addEventListener("pointerup", end); sp.addEventListener("pointercancel", end);
})();

function toggleFull() {
  const el = $("viewerCard");
  if (document.fullscreenElement) { document.exitFullscreen().catch(() => {}); return; }
  if (document.body.classList.contains("fullview")) { document.body.classList.remove("fullview"); $("btnFull").textContent = "⛶ Tela cheia"; return; }
  // se o navegador não deixar usar a tela cheia de verdade, o vídeo ocupa a janela inteira
  const fallback = () => { document.body.classList.add("fullview"); $("btnFull").textContent = "✕ Sair da tela cheia"; };
  if (!el.requestFullscreen) { fallback(); return; }
  const t = setTimeout(() => { if (!document.fullscreenElement) fallback(); }, 700);   // alguns navegadores embutidos nem respondem ao pedido
  el.requestFullscreen({ navigationUI: "hide" }).then(() => clearTimeout(t)).catch(() => { clearTimeout(t); fallback(); });
}
$("btnFull").onclick = toggleFull;
document.addEventListener("fullscreenchange", () => {
  if (document.fullscreenElement) document.body.classList.remove("fullview");
  $("btnFull").textContent = document.fullscreenElement || document.body.classList.contains("fullview") ? "✕ Sair da tela cheia" : "⛶ Tela cheia";
  setTimeout(() => { if (live.hasProc) { if (live.fit) fitView(); applyView(); } }, 80);
});
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && document.body.classList.contains("fullview")) { document.body.classList.remove("fullview"); $("btnFull").textContent = "⛶ Tela cheia"; return; }
  if ((e.key === "f" || e.key === "F") && !e.ctrlKey && !e.metaKey && !e.altKey && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName || "")) { e.preventDefault(); toggleFull(); }
});

// o Pascal é um aplicativo, não uma página: nada de zoom da janela (Ctrl + roda, Ctrl + / -, pinça). O zoom da imagem é só dentro do quadro.
window.addEventListener("wheel", (e) => { if (e.ctrlKey) e.preventDefault(); }, { passive: false, capture: true });
window.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && ["+", "-", "=", "_", "0"].includes(e.key)) e.preventDefault(); }, true);
["gesturestart", "gesturechange", "gestureend"].forEach((t) => window.addEventListener(t, (e) => e.preventDefault()));
window.addEventListener("contextmenu", (e) => { if (!e.target.closest("input,textarea,pre,.doc,#report")) e.preventDefault(); });
window.addEventListener("dragstart", (e) => { if (e.target.tagName === "IMG") e.preventDefault(); });
