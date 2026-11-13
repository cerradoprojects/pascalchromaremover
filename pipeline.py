"""Pascal — montagem dos comandos FFmpeg (sem IA, só filtros clássicos).

Este arquivo não abre janela nem servidor: só recebe os ajustes, olha o vídeo
com o ffprobe e devolve a lista de argumentos para o ffmpeg.
Cada módulo (chroma, cor, nitidez, áudio) só entra no comando se estiver ligado.
"""
from __future__ import annotations

import copy
import json
import math
import os
import re
import subprocess
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# --------------------------------------------------------------------------
# Ajustes padrão (Predefinição "Estúdio Quente")
# --------------------------------------------------------------------------
DEFAULT_SETTINGS: dict = {
    # módulos (caixinhas)
    "mod_chroma": True,
    "mod_grade": True,
    "mod_upscale": True,
    "mod_audio": True,
    # Seção 1 — recorte
    "bg_mode": "studio_mp4",        # studio_mp4 | alpha_prores | alpha_qtrle
    "matte_engine": "rvm",          # rvm = recorte por IA offline (Robust Video Matting) + tira-verde; chroma = recorte clássico por chroma key
    "matte_mix": 0.3,               # 0..1  parte da cor ORIGINAL misturada à cor estimada pelo modelo na borda do cabelo
    "matte_style": "simples",       # simples = recorte do modelo + reforço do miolo + desmistura da borda; partes = cor de borda por partes do corpo (versão anterior)
    "matte_spill": 1.0,             # 0..1  força do tira-verde do recorte por IA
    "chroma_color": "auto",               # "auto" = mede o verde de cada vídeo; ou #rrggbb
    "similarity": 0.14,
    "blend": 0.04,
    "despill": 0.85,                # força do despill (só na faixa de borda)
    "choke": 1,
    "isolate": True,                # apaga o que está ligado às laterais/topo do quadro (parede, caixa, rebatedor)
    "edge_width": 4,                # largura (px) da faixa de borda onde o despill age
    "hair_despill": 0.8,            # 0..1  tira o verde refletido do cabelo/tons escuros e de sobras de sombra verde
    "clean": 0,                    # descarta elementos isolados finos (px; 0 = desligado)
    "trim": 4.0,                    # % do quadro descartado nas laterais/topo (0 = desligado)
    # Seção 2 — cor e luz
    "warmth": 9,                   # % de aquecimento
    "contrast": 1.08,
    "gamma": 1.00,                  # >1 clareia, <1 escurece (somado à exposição automática)
    "brightness": 0.0,
    "saturation": 1.0,
    "highlights": 0.25,              # 0..1  brilho nos tons altos
    "auto_exposure": True,          # mede o rosto e ajusta a exposição sozinho
    "light": 0.8,                   # 0..1  luz de estúdio no sujeito (lado iluminado x lado de sombra)
    "light_dir": "left",            # lado de onde vem a luz principal: left | right
    "rim": 0.0,                    # 0..1  luz de recorte (contorno) no cabelo e ombros
    "bg_style": "preto",             # preto | halo | feixe  (fundo do modo estúdio; "preto" é o natural)
    "black_point": 0.02,            # 0..0.06  ancora o preto (cabelo denso, sem lavado); nunca levanta sombras
    "grain": 1.2,                   # 0..6  grão fino (evita faixas no fundo escuro)
    # Seção 3 — resolução e nitidez
    "resolution": "1080p",          # original | 1080p  (1080p = lado MENOR com 1080 px: 1920x1080 na horizontal, 1080x1920 na vertical; nunca 4K)
    "sharpen": 0.40,
    "clarity": 0.30,                # 0..1  contraste local (dá "pegada" e profundidade)
    "upscale_engine": "ffmpeg",     # ffmpeg | realesrgan (IA offline; exige bin/realesrgan)
    "ai_model": "realesr-animevideov3",
    "sharp_before": True,           # nitidez antes de juntar com o fundo (evita borda clara no cabelo)
    "hair_speckle": 0.0,            # 0..1  apaga pontinhos claros soltos dentro do cabelo (denuncia o chroma)
    "black_lift": 0.0,              # 0..0.08  o preto do sujeito não fica tão preto (níveis de saída)
    "white_soft": 0.0,              # 0..0.08  o branco do sujeito não fica tão branco
    "edge_shade": 0.12,             # 0..1  sombra na borda do cabelo/ombros (tira a "bordinha clara")
    "edge_soft": 1.0,               # 0..3 px  suaviza o contorno (degradê de transparência)          # nitidez antes de juntar com o fundo (teste: evita borda clara no cabelo)
    "ai_blend": 0.6,                # 0..1  parte da IA na mistura (o resto = original ampliado com lanczos)
    "sharp_method": "cas",          # cas | unsharp
    "denoise": "off",              # off | leve | medio | forte
    # Seção 4 — áudio
    "a_nr": 0,                     # redução de ruído de fundo (%) — afftdn com perfil do silêncio da sala
    "a_nf": -25,                    # (sem uso; mantido para presets antigos)
    "a_room": 0,                   # redução de cauda de eco de sala (%) — expansor suave
    "a_highpass": 70,
    "a_lowpass": 16000,
    "a_gate": False,
    "a_body": 0.0,                  # 180 Hz
    "a_boxy": 0.0,                 # 380 Hz (som de sala pequena)
    "a_presence": 0.0,              # 3,5 kHz
    "a_air": 0.0,                   # 9 kHz
    "a_comp": False,
    "a_loudnorm": True,
    "a_lufs": -14,
    # Preview
    "preview_start": 10.0,
    "preview_len": 5.0,
}

# (mínimo, máximo) para números
RANGES = {
    "similarity": (0.01, 0.40), "blend": (0.0, 0.20), "despill": (0.0, 1.0),
    "choke": (0, 5), "edge_width": (1, 12), "hair_despill": (0.0, 1.0), "clean": (0, 20),
    "trim": (0.0, 10.0), "warmth": (0, 40), "contrast": (0.5, 2.0),
    "gamma": (0.5, 2.0), "brightness": (-0.5, 0.5), "saturation": (0.0, 3.0),
    "highlights": (0.0, 1.0), "sharpen": (0.0, 1.0), "clarity": (0.0, 1.0), "light": (0.0, 1.0), "rim": (0.0, 1.0), "grain": (0.0, 6.0), "edge_shade": (0.0, 1.0), "matte_mix": (0.0, 1.0), "matte_spill": (0.0, 1.0), "hair_speckle": (0.0, 1.0), "black_lift": (0.0, 0.08), "white_soft": (0.0, 0.08), "edge_soft": (0.0, 3.0), "ai_blend": (0.0, 1.0), "black_point": (0.0, 0.06), "a_nr": (0, 100), "a_room": (0, 100),
    "a_nf": (-80, -20), "a_highpass": (20, 400), "a_lowpass": (4000, 20000),
    "a_body": (-12, 12), "a_boxy": (-12, 12), "a_presence": (-12, 12),
    "a_air": (-12, 12), "a_lufs": (-30, -9), "preview_start": (0, 86400),
    "preview_len": (1, 30),
}
BOOLS = ["mod_chroma", "mod_grade", "mod_upscale", "mod_audio", "a_gate", "a_comp", "a_loudnorm", "isolate", "auto_exposure", "sharp_before"]
CHOICES = {
    "bg_mode": ["studio_mp4", "alpha_prores", "alpha_qtrle"],
    "resolution": ["original", "1080p"],
    "sharp_method": ["cas", "unsharp"],
    "denoise": ["off", "leve", "medio", "forte"],
    "light_dir": ["left", "right"],
    "upscale_engine": ["ffmpeg", "realesrgan"],
    "ai_model": ["realesr-animevideov3", "realesrgan-x4plus"],
    "bg_style": ["halo", "feixe", "preto"],
    "matte_engine": ["rvm", "chroma"],
    "matte_style": ["simples", "partes"],
}
RES_HEIGHT = {"1080p": 1080}   # altura do lado MENOR (vale para vídeo horizontal e vertical)
DENOISE = {"leve": "1.0:1.0:2:2", "medio": "3:3:6:6", "forte": "5:4:9:9"}

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mxf", ".mts", ".wmv")


def clean_settings(raw: dict | None) -> dict:
    """Junta o que veio da tela com os padrões e corrige valores fora da faixa."""
    s = copy.deepcopy(DEFAULT_SETTINGS)
    raw = raw or {}
    for k, default in DEFAULT_SETTINGS.items():
        if k not in raw:
            continue
        v = raw[k]
        try:
            if k in BOOLS:
                s[k] = bool(v)
            elif k in CHOICES:
                s[k] = v if v in CHOICES[k] else default
            elif k == "chroma_color":
                s[k] = v if (v == "auto" or re.fullmatch(r"#[0-9a-fA-F]{6}", str(v))) else default
            else:
                lo, hi = RANGES[k]
                num = float(v)
                s[k] = int(round(min(hi, max(lo, num)))) if k in ("choke", "edge_width", "clean", "a_nr", "a_room", "a_highpass", "a_lowpass", "a_lufs", "a_nf") else min(hi, max(lo, num))
        except (TypeError, ValueError):
            s[k] = default
    return s


# --------------------------------------------------------------------------
# ffprobe
# --------------------------------------------------------------------------
def _run(cmd: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)


def probe(ffprobe: str, path: str) -> dict:
    """Lê duração, tamanho, fps, áudio e tags de cor do vídeo."""
    cp = _run([ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path])
    if cp.returncode != 0:
        raise RuntimeError("O ffprobe não conseguiu abrir o arquivo: " + cp.stderr.decode("utf-8", "replace")[-300:])
    data = json.loads(cp.stdout.decode("utf-8", "replace"))
    vs = next((s for s in data.get("streams", []) if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic") != 1), None)
    if vs is None:
        raise RuntimeError("O arquivo não tem faixa de vídeo.")
    aus = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)

    w, h = int(vs.get("width", 0)), int(vs.get("height", 0))
    rot = 0
    try:
        rot = int(float((vs.get("tags") or {}).get("rotate", 0)))
    except ValueError:
        rot = 0
    for sd in vs.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if abs(rot) % 180 == 90:
        w, h = h, w

    fps_s = vs.get("avg_frame_rate") or vs.get("r_frame_rate") or "30/1"
    try:
        n, d = fps_s.split("/")
        fps = float(n) / float(d) if float(d) else 30.0
    except (ValueError, ZeroDivisionError):
        fps, fps_s = 30.0, "30/1"
    if fps <= 0 or fps > 240:
        fps, fps_s = 30.0, "30/1"

    dur = 0.0
    for src in (data.get("format", {}).get("duration"), vs.get("duration")):
        try:
            dur = float(src)
            break
        except (TypeError, ValueError):
            continue

    return {
        "duration": dur, "width": w, "height": h, "fps": fps, "fps_str": fps_s,
        "has_audio": aus is not None, "audio_codec": (aus or {}).get("codec_name", ""),
        "color_space": vs.get("color_space", ""), "codec": vs.get("codec_name", ""),
    }


def detect_green(ffmpeg: str, path: str, at: float = 0.0) -> str | None:
    """Mede o verde do fundo: mediana dos pixels bem verdes do quadro (o sujeito quase nunca é tão verde)."""
    cp = _run([ffmpeg, "-v", "error", "-ss", f"{max(0.0, at):.3f}", "-i", path, "-frames:v", "1",
               "-vf", "scale=128:72:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], timeout=60)
    raw = cp.stdout
    n_px = 128 * 72
    if len(raw) < n_px * 3:
        return None
    rs, gs, bs = [], [], []
    for i in range(n_px):
        r, g, b = raw[3 * i], raw[3 * i + 1], raw[3 * i + 2]
        if g > 90 and g - max(r, b) > 35:
            rs.append(r)
            gs.append(g)
            bs.append(b)
    if len(gs) < n_px * 0.04:
        return None
    rs.sort()
    gs.sort()
    bs.sort()
    m = len(gs) // 2
    return "#{:02x}{:02x}{:02x}".format(rs[m], gs[m], bs[m])


def analyze_subject(ffmpeg: str, src: str, at: float, key_hex: str) -> dict:
    """Olha um quadro pequeno e mede onde está a pessoa e quão clara está a pele (para exposição e luz automáticas)."""
    D = key_strength(key_hex)
    cp = _run([ffmpeg, "-v", "error", "-ss", f"{max(0.0, at):.3f}", "-i", src, "-frames:v", "1",
               "-vf", "scale=128:72:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], timeout=60)
    raw = cp.stdout
    W, H = 128, 72
    out = {"cx": 0.5, "top": 0.1, "luma_p80": 0.45, "ok": False}
    if len(raw) < W * H * 3:
        return out
    pts = []   # (x, y, luma)
    for y in range(H):
        for x in range(int(W * 0.28), int(W * 0.72)):
            i = (y * W + x) * 3
            r, g, b = raw[i], raw[i + 1], raw[i + 2]
            if g - max(r, b) < 0.4 * D:
                pts.append((x, y, (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0))
    if len(pts) < 40:
        return out
    ys = sorted(p[1] for p in pts)
    top = ys[int(len(ys) * 0.02)]
    head = [p for p in pts if p[1] < top + H * 0.22]
    cx = sum(p[0] for p in head) / max(1, len(head))
    lum = sorted(p[2] for p in pts if p[1] < top + H * 0.40)   # rosto e pescoço
    p80 = lum[int(len(lum) * 0.8)] if lum else 0.45
    out.update(cx=cx / W, top=top / H, luma_p80=p80, ok=True)
    return out


def key_strength(hexcolor: str) -> float:
    """Quanto o verde do fundo passa do vermelho/azul: g - max(r, b). É a régua do recorte."""
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return max(12.0, float(g - max(r, b)))


# --------------------------------------------------------------------------
# Montagem do filtro de vídeo
# --------------------------------------------------------------------------
class Graph:
    """Monta um -filter_complex em pedaços ligados por rótulos."""

    def __init__(self, first: str = "0:v"):
        self.chains: list[str] = []
        self.rim = None
        self.cur = first
        self.lin: list[str] = []
        self.n = 0

    def label(self) -> str:
        self.n += 1
        return f"s{self.n}"

    def add(self, *filters: str) -> None:
        self.lin.extend(f for f in filters if f)

    def flush(self) -> None:
        if not self.lin:
            return
        out = self.label()
        self.chains.append(f"[{self.cur}]{','.join(self.lin)}[{out}]")
        self.cur, self.lin = out, []

    def split_alpha(self) -> None:
        """Separa a máscara (transparência) da cor: cada uma segue seu caminho e se juntam no fim."""
        self.flush()
        a, b, al = self.label(), self.label(), self.label()
        self.chains.append(f"[{self.cur}]split[{a}][{b}]")
        self.chains.append(f"[{a}]alphaextract[{al}]")
        self.cur, self.acur, self.alin = b, al, []

    def add_a(self, *filters: str) -> None:
        self.alin.extend(filters)

    def merge_alpha(self) -> None:
        self.flush()
        ax, out = self.label(), self.label()
        self.chains.append(f"[{self.acur}]{','.join(self.alin or ['null'])}[{ax}]")
        self.chains.append(f"[{self.cur}][{ax}]alphamerge[{out}]")
        self.cur = out

    def static(self, source_expr: str, fps: str) -> str:
        """Cria um quadro fixo (gradiente) repetido para sempre; devolve o rótulo."""
        lab = self.label()
        self.chains.append(source_expr + f",loop=loop=-1:size=1:start=0,setpts=N/({fps})/TB[{lab}]")
        return lab

    def build(self) -> str:
        return ";".join(self.chains)


def target_size(info: dict, s: dict, preview: bool) -> tuple[int, int]:
    w, h = info["width"], info["height"]
    if s["mod_upscale"] and s["resolution"] in RES_HEIGHT:
        k = RES_HEIGHT[s["resolution"]] / float(min(w, h))      # lado menor = 1080, qualquer orientação
        w, h = int(round(w * k / 2.0)) * 2, int(round(h * k / 2.0)) * 2
    return max(2, w - w % 2), max(2, h - h % 2)


EXPOSURE_TARGET = 0.46
TO_YUV444 = "scale=out_color_matrix=bt709:out_range=tv"   # volta de RGB para YUV sem trocar as cores


def build_video(s: dict, info: dict, preview: bool, transparent_out: bool, stage_a: bool = False, matte: bool = False) -> tuple[str, str]:
    """Devolve (filter_complex, rótulo_da_saída). matte=True: entrada 0 = cor do sujeito, entrada 1 = transparência (recorte por IA já feito)."""
    g = Graph("0:v")
    chroma = s["mod_chroma"]
    W, H = target_size(info, s, preview)
    pix_rgb = False
    if stage_a:   # etapa A do motor IA: tudo até antes da escala, em RGB, na resolução da origem
        s = dict(s, mod_upscale=False, grain=0.0)
        W, H = info["width"], info["height"]
        pix_rgb = True
    # teste de 5 s com fundo transparente: sai com ALFA de verdade (WebM VP9) e a tela escolhe a cor de trás; sem isso, o fundo é um xadrez fixo
    compose = chroma and (not transparent_out or (preview and not s.get("_alpha_preview")))

    # etiqueta de cor: sem etiqueta o ffmpeg assume matriz de SD e muda as cores
    tag = info.get("color_space", "")
    if tag in ("", "unknown", "reserved") and not matte:
        g.add("setparams=colorspace=bt709" if info["height"] >= 720 else "setparams=colorspace=smpte170m")
    if compose:
        g.add(f"fps={info['fps_str']}")

    # 1) limpeza de ruído antes do recorte
    if s["denoise"] != "off" and (chroma or s["mod_upscale"]):
        g.add(f"hqdn3d={DENOISE[s['denoise']]}")

    # normaliza para BT.709 / faixa limitada / 4:4:4 (câmeras Canon vêm em faixa total e matriz BT.601)
    g.add("scale=in_range=auto:out_range=tv:in_color_matrix=auto:out_color_matrix=bt709", "format=yuv444p10le")

    # 2) recorte: a cor do sujeito NUNCA passa pelo chroma key; ele só gera a máscara.
    #    Máscara = "quanto o pixel é mais verde que vermelho/azul" (g - max(r,b)).
    #    Fundo verde ~80, pele < 0, roupa oliva ~15, cabelo ~0: separa bem, mesmo com sombra no fundo.
    if chroma and matte:
        # recorte por IA: a cor e a transparência já vieram prontas (matte_worker.py); aqui só entram na cor/luz
        g.flush()
        al = g.label()
        g.chains.append(f"[1:v]format=gray[{al}]")
        g.acur, g.alin = al, []
        g.rim = None
    elif chroma:
        D = key_strength(s["chroma_color"])
        hi = D * (0.97 - s["similarity"])               # d >= hi  -> fundo (transparente)
        lo = max(2.0, D * (0.18 + s["blend"]))          # d <= lo  -> pessoa (opaco)
        ew, cl = int(s["edge_width"]), int(s["clean"])
        W0, H0 = info["width"], info["height"]
        kr_, kg_, kb_ = (int(s["chroma_color"][i:i + 2], 16) for i in (1, 3, 5))
        g.flush()
        base0, kr = g.label(), g.label()
        g.chains.append(f"[{g.cur}]split=2[{base0}][{kr}]")

        # ---- alfa "mole" por desmistura linear: fundo ~ D, pessoa ~ 0  =>  alfa = 1 - d/D (com folgas nas pontas)
        pr, pg, pb, mx, mask = (g.label() for _ in range(5))
        g.chains.append(f"[{kr}]format=gbrp,extractplanes=r+g+b[{pr}][{pg}][{pb}]")
        g.chains.append(f"[{pr}][{pb}]blend=all_mode=lighten[{mx}]")
        alpha_lut = f"lut=y='clip(({hi:.2f}-val)*255/({hi - lo:.2f}),0,255)'"
        # proporção de verde (d/g): fundo ~ 0,35 mesmo na sombra; roupa oliva ~ 0,13; cabelo/pele ~ 0 ou negativa.
        # Serve para despill dirigido: pixels com proporção de verde alta (sobra de fundo/sombra verde) perdem o verde.
        gbg = max(40.0, float(kg_))
        rbg = D / gbg
        pg1, pg2, d_a, d_b, dnw = (g.label() for _ in range(5))
        g.chains.append(f"[{pg}]split=2[{pg1}][{pg2}]")
        g.chains.append(f"[{pg1}][{mx}]blend=all_mode=subtract,split=2[{d_a}][{d_b}]")
        g.chains.append(f"[{d_a}]{alpha_lut},gblur=sigma=0.6[{mask}]")
        g.chains.append(f"[{d_b}][{pg2}]blend=all_mode=divide,"
                        f"lut=y='clip((val-{0.50 * rbg * 255:.1f})*255/{0.35 * rbg * 255:.1f},0,255)',gblur=sigma=1[{dnw}]")

        # ---- apaga o que está ligado às laterais/topo do quadro (parede, caixa, rebatedor), em 1/16 de resolução
        if s["isolate"]:
            sw, sh = max(8, W0 // 16), max(8, H0 // 16)
            n_it = 40
            ma, mb, ms, mseed_a, mseed_b, mseed_x, mseed_y, mseed = (g.label() for _ in range(8))
            g.chains.append(f"[{mask}]split[{ma}][{mb}]")
            g.chains.append(f"[{ma}]scale={sw}:{sh}:flags=area,lut=y='if(gt(val,110),255,0)',split=2[{ms}][{mseed_a}]")
            g.chains.append(f"[{mseed_a}]split[{mseed_b}][{mseed_x}]")
            g.chains.append(f"[{mseed_b}]crop={sw - 4}:{sh - 2}:2:2,pad={sw}:{sh}:2:2:color=black[{mseed_y}]")
            g.chains.append(f"[{mseed_x}][{mseed_y}]blend=all_mode=subtract[{mseed}]")
            copies = [g.label() for _ in range(n_it)]
            g.chains.append(f"[{ms}]split={n_it}" + "".join(f"[{c}]" for c in copies))
            cur = mseed
            for c in copies:
                nxt, dil = g.label(), g.label()
                g.chains.append(f"[{cur}]dilation[{dil}]")
                g.chains.append(f"[{dil}][{c}]blend=all_mode=darken[{nxt}]")
                cur = nxt
            bigb, nm = g.label(), g.label()
            g.chains.append(f"[{cur}]dilation,dilation,scale={W0}:{H0}:flags=bilinear,gblur=sigma=2[{bigb}]")
            g.chains.append(f"[{mb}][{bigb}]blend=all_mode=subtract[{nm}]")
            mask = nm

        if s["trim"] > 0:
            tx = max(1, int(W0 * s["trim"] / 100.0))
            ty = max(1, int(H0 * s["trim"] / 100.0))
            mt = g.label()
            g.chains.append(f"[{mask}]crop={W0 - 2 * tx}:{H0 - ty}:{tx}:{ty},pad={W0}:{H0}:{tx}:{ty}:color=black[{mt}]")
            mask = mt
        if cl > 0:
            mo, mc, mcore, mcl = g.label(), g.label(), g.label(), g.label()
            g.chains.append(f"[{mask}]split[{mo}][{mc}]")
            hw, hh = max(2, W0 // 2), max(2, H0 // 2)
            hc = max(1, cl // 2)
            g.chains.append(f"[{mc}]scale={hw}:{hh}:flags=bilinear,"
                            f"{','.join(['erosion'] * hc + ['dilation'] * (hc + 3))},"
                            f"scale={W0}:{H0}:flags=bilinear[{mcore}]")
            g.chains.append(f"[{mo}][{mcore}]blend=all_mode=darken[{mcl}]")
            mask = mcl

        # ---- trimap: NÚCLEO opaco (erosão de ew px) + FAIXA de borda onde vale o alfa mole; fora da faixa = transparente
        m_soft, m_bin, m_unm = g.label(), g.label(), g.label()
        g.chains.append(f"[{mask}]split=3[{m_soft}][{m_bin}][{m_unm}]")
        bin_a, bin_b = g.label(), g.label()
        g.chains.append(f"[{m_bin}]lut=y='if(gt(val,128),255,0)',split=2[{bin_a}][{bin_b}]")
        core_raw, outer, restr, alpha0 = g.label(), g.label(), g.label(), g.label()
        g.chains.append(f"[{bin_a}]{','.join(['erosion'] * ew)}[{core_raw}]")
        g.chains.append(f"[{bin_b}]{','.join(['dilation'] * (ew + 2))},gblur=sigma=1.5[{outer}]")
        outer_a, outer_b = g.label(), g.label()
        g.chains.append(f"[{outer}]split=2[{outer_a}][{outer_b}]")
        g.chains.append(f"[{m_soft}][{outer_a}]blend=all_mode=darken[{restr}]")
        core_a, core_b, core_c = g.label(), g.label(), g.label()
        g.chains.append(f"[{core_raw}]split=3[{core_a}][{core_b}][{core_c}]")
        g.chains.append(f"[{restr}][{core_a}]blend=all_mode=lighten[{alpha0}]")

        # ---- cor da borda: luminância DESMISTURADA (C = a*F + (1-a)*B  =>  F = B - (B - C)/a) e croma ESTENDIDO do miolo
        hw2, hh2 = max(2, W0 // 2), max(2, H0 // 2)
        w8, w8b = max(2, W0 // 8), max(2, H0 // 8)
        py_, pu_, pv_ = g.label(), g.label(), g.label()
        g.chains.append(f"[{base0}]extractplanes=y+u+v[{py_}][{pu_}][{pv_}]")
        c1, c2, c3, c4 = (g.label() for _ in range(4))
        g.chains.append(f"[{core_b}]scale={hw2}:{hh2}:flags=area,scale=in_range=pc:out_range=pc,format=gray10le,split=4[{c1}][{c2}][{c3}][{c4}]")
        den_u, den_v = g.label(), g.label()
        EPS_W = int(0.03 * 1023)                       # regularização: sem miolo por perto, a cor tende ao neutro (não a zero!)
        g.chains.append(f"[{c1}]gblur=sigma=2.5,lut=y='val+{EPS_W}',split=2[{den_u}][{den_v}]")
        # peso suave do miolo em resolução total (onde vale a cor original)
        cfull = g.label()
        g.chains.append(f"[{c4}]gblur=sigma=1.5,scale={W0}:{H0}:flags=bilinear,split=3[{cfull}a][{cfull}b][{cfull}c]")

        # fundo local (placa limpa estimada): média de luminância dos pixels de fundo, em 1/8 de resolução
        y_orig, y_bg_in, y_unm_in = g.label(), g.label(), g.label()
        g.chains.append(f"[{py_}]split=3[{y_orig}][{y_bg_in}][{y_unm_in}]")
        inv, inv_a, inv_b = g.label(), g.label(), g.label()
        mu1, mu2 = g.label(), g.label()
        g.chains.append(f"[{m_unm}]split=2[{mu1}][{mu2}]")
        g.chains.append(f"[{mu1}]lut=y='255-val',scale={w8}:{w8b}:flags=area,scale=in_range=pc:out_range=pc,format=gray10le,split=2[{inv_a}][{inv_b}]")
        yb8, num, bloc8, bloc = g.label(), g.label(), g.label(), g.label()
        g.chains.append(f"[{y_bg_in}]scale={w8}:{w8b}:flags=area[{yb8}]")
        yb_key = 64 + 876 * (0.2126 * kr_ + 0.7152 * kg_ + 0.0722 * kb_) / 255.0
        g.chains.append(f"[{yb8}][{inv_a}]blend=all_mode=multiply:shortest=1,gblur=sigma=3,lut=y='val+{int(yb_key * 0.03)}'[{num}]")
        g.chains.append(f"[{inv_b}]gblur=sigma=3,lut=y='val+{EPS_W}'[{inv}]")
        g.chains.append(f"[{num}][{inv}]blend=all_mode=divide:shortest=1,scale={W0}:{H0}:flags=bilinear[{bloc}]")
        # F_Y = Bloc - (Bloc - Y)/a   (alfa limitado a >= 0,09 para não explodir)
        bl_a, bl_b = g.label(), g.label()
        g.chains.append(f"[{bloc}]split=2[{bl_a}][{bl_b}]")
        dark, divd, a10, y_unmix = g.label(), g.label(), g.label(), g.label()
        g.chains.append(f"[{bl_a}][{y_unm_in}]blend=all_mode=subtract:shortest=1[{dark}]")
        g.chains.append(f"[{mu2}]scale=in_range=pc:out_range=pc,format=gray10le,lut=y='max(val,92)'[{a10}]")
        g.chains.append(f"[{dark}][{a10}]blend=all_mode=divide:shortest=1[{divd}]")
        g.chains.append(f"[{bl_b}][{divd}]blend=all_mode=subtract:shortest=1[{y_unmix}]")

        # croma: convolução normalizada a partir do miolo
        fixed = []
        for pl, cm, dn in ((pu_, c2, den_u), (pv_, c3, den_v)):
            a1, a2, a3, a4, a5 = (g.label() for _ in range(5))
            g.chains.append(f"[{pl}]split[{a1}][{a2}]")
            g.chains.append(f"[{a1}]scale={hw2}:{hh2}:flags=area[{a3}]")
            g.chains.append(f"[{a3}][{cm}]blend=all_mode=multiply:shortest=1,gblur=sigma=2.5,lut=y='val+{int(512 * 0.03)}'[{a4}]")
            g.chains.append(f"[{a4}][{dn}]blend=all_mode=divide:shortest=1,scale={W0}:{H0}:flags=bilinear[{a5}]")
            fixed.append((a2, a5))
        outs = []
        for (orig, ext), cw in zip([(y_orig, y_unmix)] + fixed, (f"{cfull}a", f"{cfull}b", f"{cfull}c")):
            o = g.label()
            g.chains.append(f"[{ext}][{orig}][{cw}]maskedmerge[{o}]")
            outs.append(o)
        base2, dsp_src = g.label(), g.label()
        g.chains.append(f"[{outs[0]}][{outs[1]}][{outs[2]}]mergeplanes=0x001020:yuv444p10le,split=2[{base2}][{dsp_src}]")

        # ---- despill: forte na faixa de borda e nos tons ESCUROS (cabelo, onde o verde refletido vira tom esverdeado);
        #      pele e roupa (claros) ficam como são. Peso = max(faixa de borda, escuridão).
        band_raw, band = g.label(), g.label()
        band_w, band_s = g.label(), g.label()
        g.chains.append(f"[{outer_b}][{core_c}]blend=all_mode=subtract,gblur=sigma=1.5,lut=y='clip(val*2,0,255)',split=2[{band}][{band_s}]")
        yd1, yd2, yp, dkw, wsum = (g.label() for _ in range(5))
        g.chains.append(f"[{dsp_src}]split=2[{yd1}][{yd2}]")
        g.chains.append(f"[{yd2}]extractplanes=y[{yp}]")
        hs = float(s.get("hair_despill", 0.8))
        g.chains.append(f"[{yp}]lut=y='clip((330-val)*1023/160,0,1023)*{hs:.2f}',scale=in_range=pc:out_range=pc,format=gray[{dkw}]")
        wsum0, dnw2 = g.label(), g.label()
        g.chains.append(f"[{dkw}][{band}]blend=all_mode=lighten[{wsum0}]")
        g.chains.append(f"[{dnw}]lut=y='val*{hs:.2f}'[{dnw2}]")
        g.chains.append(f"[{wsum0}][{dnw2}]blend=all_mode=lighten[{wsum}]")
        dsp, dsa, edged = g.label(), g.label(), g.label()
        g.chains.append(f"[{yd1}]format=gbrp,despill=type=green:mix=0.5:expand=0,format=yuv444p10le[{dsp}]")
        g.chains.append(f"[{dsp}][{wsum}]alphamerge[{dsa}]")
        edged0 = g.label()
        g.chains.append(f"[{base2}][{dsa}]overlay=format=yuv444p10[{edged0}]")
        es = float(s.get("edge_shade", 0.12))
        edged_s = g.label()
        if es > 0:
            # sombra de borda: escurece só a luminância na faixa do contorno (degradê), tirando a "bordinha clara"
            ey, eu, ev, ew_, ey2, shade = (g.label() for _ in range(6))
            ey_a, ey_b, hw, bgate = (g.label() for _ in range(4))
            g.chains.append(f"[{edged0}]extractplanes=y+u+v[{ey}][{eu}][{ev}]")
            g.chains.append(f"[{ey}]split=2[{ey_a}][{ey_b}]")
            # só escurece onde é cabelo/sombra (luma baixa): pele (bochecha) fica de fora
            g.chains.append(f"[{ey_b}]lut=y='clip((406-val)*1023/136,0,1023)',gblur=sigma=2,format=gray[{hw}]")
            g.chains.append(f"[{band_s}]format=gray[{bgate}]")
            bg2 = g.label()
            g.chains.append(f"[{bgate}][{hw}]blend=all_mode=multiply:shortest=1[{bg2}]")
            g.chains.append(f"[{bg2}]lut=y='255*(1-{es:.2f}*val/255)',scale=in_range=pc:out_range=pc,format=gray10le[{shade}]")
            g.chains.append(f"[{ey_a}][{shade}]blend=all_mode=multiply:shortest=1[{ey2}]")
            g.chains.append(f"[{ey2}][{eu}][{ev}]mergeplanes=0x001020:yuv444p10le[{edged_s}]")
        else:
            g.chains.append(f"[{edged0}]null[{edged_s}]")
            g.chains.append(f"[{band_s}]nullsink")

        # ---- choke (encolher) no alfa final
        final_a = alpha0
        hsp = float(s.get("hair_speckle", 0.0))
        if hsp > 0:
            # pontinhos claros dentro do cabelo: mediana 3x3 na luminância, só onde a região é escura
            sy, su, sv, sya, syb, smed, sw, sout = (g.label() for _ in range(8))
            g.chains.append(f"[{edged_s}]extractplanes=y+u+v[{sy}][{su}][{sv}]")
            g.chains.append(f"[{sy}]split=3[{sya}][{syb}][{smed}]")
            smed2, swd = g.label(), g.label()
            g.chains.append(f"[{smed}]median=radius=1[{smed2}]")
            g.chains.append(f"[{syb}]lut=y='clip((360-val)*1023/180,0,1023)*{hsp:.2f}',gblur=sigma=3,scale=in_range=pc:out_range=pc,format=gray10le[{swd}]")
            g.chains.append(f"[{sya}][{smed2}][{swd}]maskedmerge[{sout}]")
            g.chains.append(f"[{sout}][{su}][{sv}]mergeplanes=0x001020:yuv444p10le[{edged}]")
        else:
            g.chains.append(f"[{edged_s}]null[{edged}]")
        fl = ['erosion'] * int(s['choke']) + (['boxblur=1:1'] if s['choke'] > 0 else [])
        if float(s.get('edge_soft', 1.0)) > 0:
            fl.append(f"gblur=sigma={float(s.get('edge_soft', 1.0)):.2f}")
        if fl:
            fa = g.label()
            g.chains.append(f"[{final_a}]{','.join(fl)}[{fa}]")
            final_a = fa
        g.cur, g.acur, g.alin = edged, final_a, []
        g.rim = None

    # 3) cor e luz
    sub = s.get("_subject") or {"cx": 0.5, "top": 0.1, "luma_p80": 0.45, "ok": False}
    if s["mod_grade"]:
        temp = int(round(6500 - s["warmth"] * 72))
        hl = s["highlights"]
        gam = s["gamma"]
        if s["auto_exposure"] and sub["ok"]:
            # leva a pele (percentil 80) para ~0,50 de luminância (look de baixa luz); o limite evita estourar ou apagar
            p = min(0.9, max(0.08, sub["luma_p80"]))
            gam *= min(1.7, max(0.7, math.log(p) / math.log(EXPOSURE_TARGET)))
        g.add(f"colortemperature=temperature={temp}:pl=0.25")
        g.add(TO_YUV444, "format=yuv444p10le")
        g.add(f"eq=contrast={s['contrast']:.3f}:brightness={s['brightness']:.3f}:saturation={s['saturation']:.3f}:gamma={gam:.3f}",
              f"curves=m='0/0 0.10/0.08 0.30/0.28 0.55/0.56 {0.78:.2f}/{0.79 + 0.07 * hl:.4f} 1/1'", "format=yuv444p10le", f"lutyuv=y='clip(64+876*({s['black_lift']:.3f}+max(0,val-{64 + s['black_point'] * 876:.0f})/{876 * (1 - s['black_point']):.1f}*{1 - s['black_lift'] - s['white_soft']:.3f}),64,1023)'")
        if chroma and (s["light"] > 0 or g.rim):
            # luz de estúdio + luz de recorte mexem só na luminância (planos separados, croma intacto)
            g.flush()
            W0, H0 = info["width"], info["height"]
            py, pu, pv = g.label(), g.label(), g.label()
            g.chains.append(f"[{g.cur}]extractplanes=y+u+v[{py}][{pu}][{pv}]")
            ycur = py
            if s["light"] > 0:
                S = s["light"]
                cx = sub["cx"] * W0
                fy = (sub["top"] + 0.42 * (1.0 - sub["top"])) * H0
                sh = 1 if s["light_dir"] == "left" else -1
                expr = (f"1023*(1-0.30*{S:.2f}*clip((X-{cx:.0f})/({0.12 * W0:.0f})*{sh}+0.35,0,1.3))"
                        f"*(1-0.45*{S:.2f}*pow(clip((Y-{fy:.0f})/({max(1.0, H0 - fy):.0f}),0,1),1.4))")
                gl = g.static(f"nullsrc=s={W0}x{H0}:r={info['fps_str']},format=gray10le,trim=end_frame=1,"
                              f"geq=lum='{expr}'", info["fps_str"])
                nxt = g.label()
                g.chains.append(f"[{ycur}][{gl}]blend=all_mode=multiply:shortest=1[{nxt}]")
                ycur = nxt
            if g.rim:
                nxt = g.label()
                g.chains.append(f"[{ycur}][{g.rim}]blend=all_mode=addition:shortest=1[{nxt}]")
                ycur = nxt
            out = g.label()
            g.chains.append(f"[{ycur}][{pu}][{pv}]mergeplanes=0x001020:yuv444p10le[{out}]")
            g.cur = out

    # 4) escala e nitidez
    if s["mod_upscale"] and s["resolution"] in RES_HEIGHT:
        g.add(f"scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int")
        if chroma:
            g.add_a(f"scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int")
    sharp_f: list[str] = []
    if s["mod_upscale"] and s["clarity"] > 0:
        sharp_f.append(f"unsharp=11:11:{s['clarity'] * 0.9:.3f}:11:11:0.0")   # contraste local (raio grande, só luminância)
    if s["mod_upscale"] and s["sharpen"] > 0:
        if s["sharp_method"] == "cas":
            sharp_f.append(f"cas=strength={s['sharpen']:.3f}")
        else:
            sharp_f.append(f"unsharp=5:5:{s['sharpen'] * 1.4:.3f}:5:5:0.0")
    # com fundo composto, a nitidez vem DEPOIS de juntar com o fundo; só no recorte transparente ela entra antes (mais leve)
    sharp_after = compose and not transparent_out and not s.get("sharp_before", False)
    if not sharp_after:
        g.add(*sharp_f)
    if chroma:
        g.merge_alpha()

    # 5) saída
    if compose:
        g.flush()
        fps = info["fps_str"]
        if transparent_out:   # preview do fundo transparente: tabuleiro xadrez
            cell = max(8, int(round(H / 27)))
            lum = f"if(eq(mod(floor(X/{cell})+floor(Y/{cell}),2),0),232,168)"
        elif s["bg_style"] == "preto":
            lum = "clip(80-48*pow(hypot((X-W/2)/(W/2),(Y-H/2)/(H/2))/1.4142,2),0,1023)"
        else:
            # fundo de estúdio: vinheta escura + halo suave atrás da pessoa (+ feixe diagonal no estilo "feixe")
            sub = s.get("_subject") or {"cx": 0.5}
            cxb, cyb, sg = sub["cx"] * W, 0.40 * H, 0.30 * H
            halo = f"+72*exp(-(pow(X-{cxb:.0f},2)+pow(Y-{cyb:.0f},2))/(2*{sg * sg:.0f}))"
            vign = "(74-36*pow(hypot((X-W/2)/(W/2),(Y-H/2)/(H/2))/1.4142,2))"
            beam = ""
            if s["bg_style"] == "feixe":
                hw = 0.075 * H
                beam = (f"+420*exp(-pow(abs(Y-(0.23*H+X/W*0.40*H))/{hw:.0f},4))*clip(1.15-0.95*X/W,0,1)")
            lum = f"clip({vign}{halo}{beam},0,1023)"
        bgsrc = (f"nullsrc=s={W}x{H}:r={fps},format=yuv444p10le,trim=end_frame=1,geq=lum='{lum}':cb=512:cr=512")
        bg = g.static(bgsrc, fps)
        tail = f"noise=alls={s['grain']:.1f}:allf=t," if s["grain"] > 0 else ""
        post = ("".join(f + "," for f in sharp_f)) if sharp_after else ""
        fgx = g.label()
        g.chains.append(f"[{g.cur}]setpts=PTS-STARTPTS[{fgx}]")   # sem isto o 1º quadro de um trecho (-ss) saía só com o fundo
        g.chains.append(f"[{bg}][{fgx}]overlay=format=yuv444p10:shortest=1,{post}{tail}"
                        + ("scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=bicubic+error_diffusion,format=rgb24[vout]" if pix_rgb else
                           "scale=in_color_matrix=bt709:out_color_matrix=bt709:in_range=tv:out_range=tv:flags=bicubic+error_diffusion,"
                           "format=yuv420p[vout]"))
        return g.build(), "vout"

    if chroma and transparent_out:
        g.add("format=argb" if s["bg_mode"] == "alpha_qtrle" else "format=yuva444p10le")
    else:
        if pix_rgb:
            g.add("scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=bicubic+error_diffusion", "format=rgb24")
        else:
            g.add("scale=in_color_matrix=bt709:out_color_matrix=bt709:in_range=tv:out_range=tv", "format=yuv420p")
    g.add("null")
    g.flush()
    g.chains[-1] = re.sub(r"\[s\d+\]$", "[vout]", g.chains[-1])
    return g.build(), "vout"


# --------------------------------------------------------------------------
# Áudio
# --------------------------------------------------------------------------
def analyze_room(ffmpeg: str, src: str, spans: list[tuple[float, float]]) -> dict:
    """Escuta o áudio e acha (1) o nível da fala e (2) 1 s de "silêncio de sala" para o filtro aprender o ruído.
    Devolve {speech_db, tone_at, tone_db, ok, why}. Se não houver pausa de verdade, ok=False (nada é aprendido errado)."""
    import math
    import struct
    best = None   # (média, início absoluto)
    all_levels: list[float] = []
    for t0, dur in spans:
        cp = _run([ffmpeg, "-v", "error", "-ss", f"{max(0.0, t0):.3f}", "-t", f"{dur:.1f}", "-i", src,
                   "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], timeout=180)
        n = len(cp.stdout) // 2
        if n < 8000:
            continue
        smp = struct.unpack("<%dh" % n, cp.stdout[: n * 2])
        win = 800
        lv = []
        for i in range(0, n - win, win):
            seg = smp[i:i + win]
            lv.append(20 * math.log10(max(1.0, math.sqrt(sum(x * x for x in seg) / win)) / 32768.0))
        all_levels += lv
        for i in range(0, len(lv) - 10):
            w = lv[i:i + 10]
            m = sum(w) / 10.0
            if (best is None or m < best[0]) and max(w) - min(w) < 4.0:
                best = (m, max(0.0, t0) + i * 0.1)
    if not all_levels:
        return {"speech_db": -16.0, "tone_at": 0.0, "tone_db": -60.0, "ok": False, "why": "sem áudio legível"}
    srt = sorted(all_levels)
    speech = max(-40.0, min(-6.0, srt[int(len(srt) * 0.9)]))
    if best is None:
        return {"speech_db": speech, "tone_at": 0.0, "tone_db": -60.0, "ok": False, "why": "nenhum trecho estável de silêncio"}
    ok = best[0] < speech - 8.0
    return {"speech_db": speech, "tone_at": best[1], "tone_db": best[0], "ok": ok,
            "why": "" if ok else "o trecho mais quieto não é silêncio de verdade (fala contínua?)"}


AFFTDN_LATENCY = 0.025   # o afftdn atrasa o som ~25 ms; cortamos esse começo para manter a sincronia com o vídeo


def audio_chain(s: dict, speech_db: float, denoise: bool, loud: dict | None = None, measure: bool = False) -> str:
    """Filtros de áudio. Ordem: graves -> ruído (perfil da sala) -> cauda de eco -> EQ -> nível."""
    f = [f"highpass=f={s['a_highpass']}:poles=2", f"lowpass=f={s['a_lowpass']}"]
    if denoise and s["a_nr"] > 0:
        nr = max(1.0, s["a_nr"] * 0.2)            # 60% -> 12 dB
        rf = -(35 + s["a_nr"] * 0.25)             # 60% -> -50 dB
        f.append(f"asendcmd=c='0.1 afftdn sn start;0.9 afftdn sn stop',afftdn=nr={nr:.1f}:nf=-30:rf={rf:.0f}:gs=3")
    if s["a_gate"] and s["a_room"] > 0:
        # expansor SUAVE: abafa no máximo ~8 dB o que está bem abaixo da fala (cauda do eco), sem "picotar"
        d = s["a_room"] / 100.0
        S = speech_db
        pts = [(S - 70, S - 70 - 12 * d), (S - 35, S - 35 - 8 * d), (S - 22, S - 22 - 4 * d), (S - 12, S - 12 - 1 * d), (S - 4, S - 4)]
        pts = [(x, y) for x, y in pts if x < -1.0] + [(0, 0)]
        f.append("compand=attacks=0.02:decays=0.25:soft-knee=8:points=" + "|".join(f"{x:.1f}/{y:.1f}" for x, y in pts))
    for freq, width, gain in ((180, 1.2, s["a_body"]), (380, 1.6, s["a_boxy"]),
                              (3500, 1.0, s["a_presence"]), (9000, 1.5, s["a_air"])):
        if abs(gain) >= 0.05:
            f.append(f"equalizer=f={freq}:t=q:w={width}:g={gain:.2f}")
    if s["a_comp"]:
        # compressor suave: só segura os picos da fala (threshold no nível da fala); não achata nem levanta o ruído
        thr = 10 ** ((speech_db + 3) / 20.0)
        f.append(f"acompressor=threshold={min(1.0, max(0.001, thr)):.4f}:ratio=2:attack=15:release=200:makeup=1")
    if s["a_loudnorm"]:
        # loudnorm em UM passo "levanta" o som fraco (o ruído que acabamos de tirar volta). Por isso são 2 passos:
        # (o som é processado em mono e depois duplicado nos dois lados: isso soma +3 LU, por isso o alvo do loudnorm é lufs-3)
        # 1) mede o volume; 2) aplica um ganho único e linear (a relação voz x ruído fica como está).
        if measure:
            f.append(f"loudnorm=I={s['a_lufs'] - 3.0:.1f}:TP=-1.5:LRA=11:print_format=json")
        elif loud:
            f.append(f"loudnorm=I={s['a_lufs'] - 3.0:.1f}:TP=-1.5:LRA=11:measured_I={loud['input_i']}:measured_TP={loud['input_tp']}:"
                     f"measured_LRA={loud['input_lra']}:measured_thresh={loud['input_thresh']}:offset={loud['target_offset']}:linear=true")
        else:
            f.append(f"loudnorm=I={s['a_lufs'] - 3.0:.1f}:TP=-1.5:LRA=11")
        f.append("aresample=48000")   # o loudnorm devolve 192 kHz; voltamos para 48 kHz
    f.append("alimiter=limit=0.89")
    return ",".join(f)


def measure_loudness(ffmpeg: str, in_args: list[str], s: dict, room: dict, has_noise: bool) -> dict | None:
    """Passo 1 do loudnorm: roda a cadeia de áudio sem gravar nada e lê o volume medido (JSON no stderr)."""
    graph = audio_graph(s, room, has_noise, measure=True)
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "info"] + in_args + ["-filter_complex", graph, "-map", "[aout]", "-f", "null", "-"]
    cp = _run(cmd, timeout=3600)
    txt = cp.stderr.decode("utf-8", "replace")
    m = re.search(r"\{\s*\"input_i\".*?\}", txt, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return {k: d[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}
    except (ValueError, KeyError):
        return None


def audio_graph(s: dict, room: dict, has_noise_input: bool, noise_idx: int = 1, main: str = "0:a",
                loud: dict | None = None, measure: bool = False) -> str:
    """Pedaço de -filter_complex que gera [aout] (estéreo 48 kHz). O ruído da sala entra como 1 s antes da fala."""
    chain = audio_chain(s, room["speech_db"], has_noise_input, loud, measure)
    fmt = "aformat=sample_rates=48000:channel_layouts=mono"
    if has_noise_input:
        return (f"[{noise_idx}:a]{fmt}[an];[{main}]{fmt}[am];[an][am]concat=n=2:v=0:a=1,{chain},"
                f"atrim=start={1.0 + AFFTDN_LATENCY:.3f},asetpts=PTS-STARTPTS,pan=stereo|c0=c0|c1=c0[aout]")
    return f"[{main}]{fmt},{chain},pan=stereo|c0=c0|c1=c0[aout]"


# --------------------------------------------------------------------------
# Comando final
# --------------------------------------------------------------------------
def output_kind(s: dict) -> str:
    """mp4 | prores | qtrle — o que o render completo vai gerar."""
    if s["mod_chroma"] and s["bg_mode"] == "alpha_prores":
        return "prores"
    if s["mod_chroma"] and s["bg_mode"] == "alpha_qtrle":
        return "qtrle"
    return "mp4"


SUFFIX = {"mp4": "_STUDIO.mp4", "prores": "_ALPHA_PREMIERE.mov", "qtrle": "_ALPHA_LEVE.mov"}


def resolve_key_color(ffmpeg: str, src: str, s: dict, info: dict, at: float | None) -> dict:
    """Troca "auto" pela cor medida no próprio vídeo (tenta alguns pontos; se falhar, usa um verde claro comum)."""
    if s["chroma_color"] != "auto":
        return s
    dur = info["duration"] or 0.0
    tries = [at] if at is not None else []
    tries += [min(10.0, dur * 0.3), dur * 0.5, 0.0]
    found = None
    for t0 in tries:
        found = detect_green(ffmpeg, src, max(0.0, t0))
        if found:
            break
    s = dict(s)
    s["chroma_color"] = found or "#95e591"
    s["_detected"] = bool(found)
    return s


def build_command(ffmpeg: str, src: str, s: dict, info: dict, out_path: str,
                  preview: bool, start: float = 0.0, length: float = 0.0, diag: dict | None = None, matte: dict | None = None) -> list[str]:
    kind = output_kind(s)
    transparent = kind in ("prores", "qtrle")
    s = resolve_key_color(ffmpeg, src, s, info, start if preview else None)
    s = dict(s)
    s["_subject"] = analyze_subject(ffmpeg, src, start if preview else min(10.0, (info["duration"] or 20) * 0.3),
                                    s["chroma_color"] if s["chroma_color"] != "auto" else "#95e591")
    s["_alpha_preview"] = bool(preview and transparent and s["mod_chroma"])
    if matte:   # o recorte por IA já saiu no tamanho final (1080p): o resto do grafo trabalha nele
        info = dict(info, width=matte["w"], height=matte["h"])
    fc, vlabel = build_video(s, info, preview, transparent, matte=bool(matte))

    use_af = info["has_audio"] and s["mod_audio"]
    room = None
    if use_af:
        dur = info["duration"] or 60.0
        spans = [(max(0.0, start - 15), 45.0)] if preview else [(0.0, min(dur, 150.0))]
        room = analyze_room(ffmpeg, src, spans)
        if not room["ok"]:   # sem pausa de verdade: tenta o começo do arquivo antes de desistir
            alt = analyze_room(ffmpeg, src, [(0.0, min(dur, 120.0))])
            room = alt if alt["ok"] else room
        s["_room"] = room

    cmd = [ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "warning", "-progress", "pipe:1", "-nostats"]
    ai = 0   # índice da entrada que traz o áudio
    if matte:
        cmd += ["-i", matte["color"], "-i", matte["alpha"]]
        ai = 2
        if info["has_audio"]:
            if preview:
                cmd += ["-ss", f"{start:.3f}", "-t", f"{length:.3f}"]
            cmd += ["-i", src]
    else:
        if preview:
            cmd += ["-ss", f"{start:.3f}", "-t", f"{length:.3f}"]
        cmd += ["-i", src]
    amap = ["-map", f"{ai}:a:0"] if info["has_audio"] else []
    if use_af:
        if room["ok"]:
            cmd += ["-ss", f"{room['tone_at']:.3f}", "-t", "1.0", "-i", src]   # entrada 1 = silêncio de sala
        loud = None
        if s["a_loudnorm"]:
            in_args = (["-ss", f"{start:.3f}", "-t", f"{length:.3f}"] if preview else []) + ["-i", src]
            if room["ok"]:
                in_args += ["-ss", f"{room['tone_at']:.3f}", "-t", "1.0", "-i", src]
            loud = measure_loudness(ffmpeg, in_args, s, room, room["ok"])
            room["loud"] = loud
        fc += ";" + audio_graph(s, room, room["ok"], noise_idx=ai + 1, main=f"{ai}:a", loud=loud)
        amap = ["-map", "[aout]"]
        use_af = False   # já aplicado dentro do filter_complex
    cmd += ["-filter_complex", fc, "-map", f"[{vlabel}]"] + amap
    if diag is not None:
        diag["settings"] = s
        diag["filter_complex"] = fc
        diag["has_audio_chain"] = bool(info["has_audio"] and s["mod_audio"])

    if preview and s["_alpha_preview"]:
        # WebM VP9 com alfa: o Chrome/Edge toca com transparência e a cor de fundo é escolhida na tela
        cmd += ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28", "-deadline", "realtime", "-cpu-used", "5",
                "-row-mt", "1", "-auto-alt-ref", "0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
        if info["has_audio"]:
            cmd += ["-c:a", "libopus", "-b:a", "160k", "-ar", "48000"]
    elif preview:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-movflags", "+faststart"]
        if info["has_audio"]:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    elif kind == "mp4":
        cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-movflags", "+faststart"]
        if info["has_audio"]:
            if s["mod_audio"]:
                cmd += ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
            elif info["audio_codec"] in ("aac", "mp3", "ac3", "alac"):
                cmd += ["-c:a", "copy"]
            else:
                cmd += ["-c:a", "aac", "-b:a", "256k"]
    else:
        if kind == "prores":
            cmd += ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                    "-alpha_bits", "16", "-vendor", "apl0"]
        else:
            cmd += ["-c:v", "qtrle", "-pix_fmt", "argb"]
        cmd += ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
        if info["has_audio"]:
            cmd += ["-c:a", "pcm_s16le", "-ar", "48000"]

    cmd.append(out_path)
    return cmd


def unique_output(out_dir: Path, src: str, kind: str) -> Path:
    stem = Path(src).stem
    p = out_dir / (stem + SUFFIX[kind])
    n = 2
    while p.exists():
        p = out_dir / f"{stem}{SUFFIX[kind][:-4]}_{n}{SUFFIX[kind][-4:]}"
        n += 1
    return p


# --------------------------------------------------------------------------
# Binários e execução
# --------------------------------------------------------------------------
def find_binaries(base: Path) -> tuple[str | None, str | None]:
    """Procura ffmpeg.exe / ffprobe.exe em ./bin (inclusive em subpastas) e, se não achar, no PATH."""
    import shutil
    found: dict[str, str | None] = {}
    for name in ("ffmpeg", "ffprobe"):
        exe = name + (".exe" if os.name == "nt" else "")
        hit = None
        bin_dir = base / "bin"
        if bin_dir.is_dir():
            direct = bin_dir / exe
            if direct.is_file():
                hit = str(direct)
            else:
                hit = next((str(p) for p in bin_dir.rglob(exe)), None)
        found[name] = hit or shutil.which(name)
    return found["ffmpeg"], found["ffprobe"]


def run_ffmpeg(cmd: list[str], total_seconds: float, on_progress=None, holder: dict | None = None,
               log_path: Path | None = None) -> tuple[int, str]:
    """Roda o ffmpeg e vai avisando o andamento (0-100). Devolve (código, últimas linhas de erro)."""
    import tempfile
    import threading
    log = tempfile.TemporaryFile()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=log, creationflags=CREATE_NO_WINDOW)
    if holder is not None:
        holder["proc"] = proc
    info: dict[str, str] = {}

    def reader() -> None:
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = raw.decode("utf-8", "replace").strip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            info[k] = v
            if k == "progress" and on_progress:
                try:
                    done = int(info.get("out_time_us", "0")) / 1_000_000.0
                except ValueError:
                    done = 0.0
                pct = min(99.0, 100.0 * done / total_seconds) if total_seconds > 0 else 0.0
                on_progress(pct, info.get("speed", ""), done)

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    code = proc.wait()
    th.join(timeout=3)
    log.seek(0)
    full = log.read().decode("utf-8", "replace")
    tail = "\n".join(full.strip().splitlines()[-12:])
    log.close()
    if log_path is not None:
        try:
            log_path.write_text(full, encoding="utf-8")
        except OSError:
            pass
    return code, tail


def build_audio_command(ffmpeg: str, src: str, s: dict, info: dict, out_path: str) -> list[str] | None:
    """Só o áudio do render completo (AAC), pelo mesmo caminho do render normal. Usado pelo motor IA, que gera o vídeo em pedaços."""
    if not info["has_audio"]:
        return None
    cmd = [ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "warning", "-i", src]
    if s["mod_audio"]:
        dur = info["duration"] or 60.0
        room = analyze_room(ffmpeg, src, [(0.0, min(dur, 150.0))])
        if not room["ok"]:
            alt = analyze_room(ffmpeg, src, [(0.0, min(dur, 120.0))])
            room = alt if alt["ok"] else room
        in_args = ["-i", src]
        if room["ok"]:
            cmd += ["-ss", f"{room['tone_at']:.3f}", "-t", "1.0", "-i", src]
            in_args += ["-ss", f"{room['tone_at']:.3f}", "-t", "1.0", "-i", src]
        loud = measure_loudness(ffmpeg, in_args, s, room, room["ok"]) if s["a_loudnorm"] else None
        cmd += ["-filter_complex", audio_graph(s, room, room["ok"], loud=loud), "-map", "[aout]"]
    else:
        cmd += ["-map", "0:a:0"]
    return cmd + ["-vn", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", out_path]


def build_still_command(ffmpeg: str, src: str, s: dict, info: dict, out_png: str, at: float,
                        matte: dict | None = None, ready: bool = False) -> tuple[list[str], dict]:
    """Um quadro só, com todo o tratamento (cor, luz, nitidez, fundo), em PNG: serve ao quadro ao vivo da interface.
    Com fundo de estúdio sai opaco; com saída transparente sai PNG com alfa. ready=True: s já traz cor do verde e medição do sujeito."""
    transparent = output_kind(s) in ("prores", "qtrle")
    s = dict(s)
    if not ready:
        s = resolve_key_color(ffmpeg, src, s, info, at)
        s["_subject"] = analyze_subject(ffmpeg, src, at, s["chroma_color"] if s["chroma_color"] != "auto" else "#95e591")
    if matte:
        info = dict(info, width=matte["w"], height=matte["h"])
    fc, vlabel = build_video(s, info, False, transparent, matte=bool(matte))   # False: alfa de verdade (o xadrez fica por conta da tela)
    fc += f";[{vlabel}]scale=in_range=tv:in_color_matrix=bt709:out_range=pc:flags=bicubic+accurate_rnd+full_chroma_int,format={'rgba' if transparent else 'rgb24'}[still]"
    cmd = [ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error"]
    if matte:
        cmd += ["-i", matte["color"], "-i", matte["alpha"]]
    else:
        cmd += ["-ss", f"{max(0.0, at):.3f}", "-i", src]
    cmd += ["-filter_complex", fc, "-map", "[still]", "-frames:v", "1", out_png]
    return cmd, s
