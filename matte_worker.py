"""Recorte por IA (Robust Video Matting, offline) de um trecho do vídeo.
Grava dois arquivos: a COR do sujeito (já com o verde tirado das bordas/cabelo) e a TRANSPARÊNCIA.
É um programa à parte porque precisa de numpy + onnxruntime, que o Python portátil pode não ter (ver matte_ai.py).
Imprime "PROG n" a cada poucos quadros e "FIM n" no final."""
import argparse
import queue
import subprocess
import sys
import threading
import time

import numpy as np

try:                      # o modo --post-raw não precisa do modelo
    import onnxruntime as ort
except ImportError:       # pragma: no cover
    ort = None

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
import os
VARIANT = os.environ.get("MATTE_VARIANT", "E")      # E = simples (padrão: o modelo manda); D = por classe (guardada); atual/B/C = extensão antiga por média
EXT = {"atual": (0.9, 0.95, 0.45), "B": (0.97, 0.995, 0.25), "C": (0.985, 1.0, 0.15)}.get(VARIANT, (0.985, 1.0, 0.15))


def box(x: np.ndarray, r: int) -> np.ndarray:
    """Média em janela (2r+1) nos dois eixos, com cumsum (sem scipy)."""
    k = 2 * r + 1
    for ax in (0, 1):
        x = np.swapaxes(x, 0, ax)
        n = x.shape[0]
        pad = [(r + 1, r)] + [(0, 0)] * (x.ndim - 1)
        c = np.cumsum(np.pad(x, pad, mode="edge"), axis=0, dtype=np.float32)
        x = (c[k:k + n] - c[0:n]) / k
        x = np.swapaxes(x, 0, ax)
    return x


def despill(fg: np.ndarray, a: np.ndarray, strength: float) -> np.ndarray:
    """Tira o verde que sobra: g -> g - (g - max(r,b)) * peso. Peso = máx(faixa de borda, escuridão): pele e roupa clara não mudam."""
    r, g, b = fg[..., 0], fg[..., 1], fg[..., 2]
    spill = np.maximum(0.0, g - np.maximum(r, b))
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    m = ((a > 0.02) & (a < 0.98)).astype(np.float32)
    edge = box(box(m, 3), 3) * 3.0
    dark = np.clip((0.45 - y) / 0.25, 0.0, 1.0)
    w = np.clip(np.maximum(edge, dark), 0.0, 1.0) * strength
    out = fg.copy()
    out[..., 1] = g - spill * w
    return out


def extend_color(color: np.ndarray, alpha: np.ndarray, core_t: float = 0.9, hi: float = 0.95, wid: float = 0.45) -> np.ndarray:
    """Na borda (transparência parcial) a cor do modelo carrega tom do fundo (oliva) e, sobre preto, vira um contorno visível.
    Troca a cor dessas bordas pela cor do miolo opaco mais próximo (média ponderada em 1/4 de resolução)."""
    H, W = alpha.shape
    q = 4
    Hq, Wq = -(-H // q), -(-W // q)
    core = (alpha > core_t).astype(np.float32)
    pad = ((0, Hq * q - H), (0, Wq * q - W))
    cp = np.pad(color * core[..., None], pad + ((0, 0),), mode="edge")
    kp = np.pad(core, pad, mode="edge")
    num = cp.reshape(Hq, q, Wq, q, 3).mean((1, 3))
    den = kp.reshape(Hq, q, Wq, q).mean((1, 3))
    for _ in range(2):
        num = box(num, 3)
        den = box(den, 3)
    ext = num / np.maximum(den, 1e-3)[..., None]
    ext = np.repeat(np.repeat(ext, q, 0), q, 1)[:H, :W]
    have = np.repeat(np.repeat(den, q, 0), q, 1)[:H, :W]
    w = np.clip((hi - alpha) / wid, 0.0, 1.0) * np.clip(have / 0.02, 0.0, 1.0)
    return color * (1.0 - w[..., None]) + ext * w[..., None]


# --------------------------------------------------------------------------------------------------------------------
# Cor de borda por CLASSE (variante D, padrão desde 12/11). Cada pixel de borda é de uma parte do corpo (pele, roupa, cabelo);
# usamos a cor verdadeira DESSA parte, nunca uma média de partes diferentes (a média punha pele em fio de cabelo = "mecha loura").
#  A) limite de verde: o verde relativo g/max(r,b) de um pixel de borda não passa do verde do MIOLO da mesma classe
#     (classe = calor (r-b)/(r+b): pele quente | roupa oliva | cabelo e cinza neutros; miolo = longe >= ~12 px da borda).
#  B) borda translúcida troca a cor pela do miolo vizinho, mas só se combinar com a luz e o calor do próprio pixel.
# Ambos só perto do fundo (pele/roupa translúcida no meio do corpo não é mexida: era a causa de blocos em quadros ruins).
Q = 4
WARM_C = (0.03, 0.14, 0.30)         # calor típico: neutro/cabelo | oliva/roupa | pele
D0 = 0.04                           # densidade mínima de miolo para a classe "existir" por perto
TOL_Y = 0.08                        # o miolo pode ser até 0,08 mais claro que o pixel (borda escura sobe), não mais


def _r(px: float) -> int:
    return max(1, int(round(px / Q / 2.0)))


def down(a: np.ndarray, how: str = "mean") -> np.ndarray:
    """Redução por blocos Q×Q em duas etapas (reduz primeiro o eixo contíguo: bem mais rápido)."""
    H, W = a.shape[:2]
    ph, pw = (-H) % Q, (-W) % Q
    if ph or pw:
        a = np.pad(a, ((0, ph), (0, pw)) + ((0, 0),) * (a.ndim - 2), mode="edge")
    H, W = a.shape[:2]
    red = {"mean": np.mean, "min": np.min, "max": np.max}[how]
    if a.ndim == 2:
        t = red(a.reshape(H, W // Q, Q), axis=2)
        return red(t.reshape(H // Q, Q, W // Q), axis=1)
    c = a.shape[2]
    t = red(a.reshape(H, W // Q, Q, c), axis=2)
    return red(t.reshape(H // Q, Q, W // Q, c), axis=1)


def _luma(c: np.ndarray) -> np.ndarray:
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def _warmth(c: np.ndarray) -> np.ndarray:
    return (c[..., 0] - c[..., 2]) / (c[..., 0] + c[..., 2] + 0.05)


def _tri3(x: np.ndarray):
    c0, c1, c2 = WARM_C
    w0 = np.clip((c1 - x) / (c1 - c0), 0.0, 1.0)
    w2 = np.clip((x - c1) / (c2 - c1), 0.0, 1.0)
    return w0, 1.0 - w0 - w2, w2


def edge_colors(orig: np.ndarray, fgr: np.ndarray, alpha: np.ndarray, mix: float = 0.3, spill: float = 1.0, head: float = 1.06,
                floor=(0.97, 0.92, 0.6), color0: np.ndarray | None = None, swap: bool = True) -> np.ndarray:
    """swap=False: só o limite de verde por classe (A); não troca a cor da borda pela do miolo vizinho (B). color0: cor-base já pronta."""
    H, W = alpha.shape
    if color0 is None:
        color0 = fgr * (1.0 - mix) + orig * mix
    core_q = (down(alpha, "min") >= 0.985).astype(np.float32)
    bgf = down((alpha < 0.1).astype(np.float32))                  # fração de fundo por bloco
    c_q = down(color0)
    r_l, r_g, r_z = _r(24), _r(96), _r(24)
    deep = (box(core_q, max(1, int(round(12 / Q)))) > 0.999).astype(np.float32)
    c1 = (box(core_q, 1) > 0.999).astype(np.float32)
    rho_q = c_q[..., 1] / np.maximum(np.maximum(c_q[..., 0], c_q[..., 2]), 0.02)
    wb = _tri3(_warmth(c_q))
    planes = []
    for b in range(3):
        m = deep * wb[b]
        planes += [(rho_q * m)[..., None], m[..., None]]
    planes += [c_q * c1[..., None], c1[..., None]]                 # 4 canais: cor do miolo raso
    base = np.concatenate(planes, axis=2)                          # (Hq,Wq,10)
    S_loc = box(box(base, r_l), r_l)
    S_reg = box(box(base[..., :6], r_g), r_g)
    f_core = box(box(core_q, r_z), r_z)                            # ~1 longe de borda/buraco, ~0,5 na borda
    bgw_b = np.clip(box(box(bgf, _r(16)), _r(16)) * 4.0, 0.0, 1.0)  # fundo por perto (<= ~16 px): troca de cor
    bgw_a = np.clip(box(box(bgf, _r(32)), _r(32)) * 3.0, 0.0, 1.0)  # fundo por perto (<= ~32 px): limite de verde

    near = (f_core < 0.999) & (bgw_a > 0.0)
    zone_q = np.repeat(np.repeat(near, Q, 0), Q, 1)[:H, :W] & (alpha > 0.003)
    ys, xs = np.nonzero(zone_q)
    out = color0.copy()
    if len(ys) == 0:
        return out
    qy, qx = ys // Q, xs // Q
    c0 = color0[ys, xs]
    a = alpha[ys, xs]
    t = _tri3(_warmth(c0))
    ms = np.maximum(c0[:, 0], c0[:, 2])
    self_c = c0.copy()
    self_c[:, 1] = np.minimum(c0[:, 1], ms)

    # B) cor do miolo vizinho (guardada)
    if swap:
        Rg = S_loc[qy, qx][:, 6:10]
        den = Rg[:, 3]
        rn = Rg[:, :3] / np.maximum(den, 1e-3)[:, None]
        Ys, Yr = _luma(self_c), _luma(rn)
        g_l = np.clip(1.0 - (Yr - Ys - TOL_Y) / 0.06, 0.0, 1.0)
        g_w = np.clip(1.0 - (_warmth(rn) - _warmth(self_c) - 0.06) / 0.08, 0.0, 1.0)
        w_a = np.clip((1.0 - a) / 0.15, 0.0, 1.0) * np.clip(den / 0.03, 0.0, 1.0) * g_l * g_w * bgw_b[qy, qx]
        f1 = c0 * (1.0 - w_a)[:, None] + rn * w_a[:, None]
    else:
        f1 = c0.copy()

    # A) verde relativo máximo da classe (miolo >= ~12 px da borda) + folga
    def kap(S):
        Sg = S[qy, qx]
        num = np.zeros(len(ys), np.float32)
        den_ = np.zeros(len(ys), np.float32)
        for b in range(3):
            n_, d_ = Sg[:, b * 2], Sg[:, b * 2 + 1]
            k_b = np.maximum(n_ / np.maximum(d_, 1e-3), floor[b])
            w = t[b] * np.clip(d_ / D0, 0.0, 1.0)
            num += w * k_b
            den_ += w
        return num / np.maximum(den_, 1e-4), np.clip(den_, 0.0, 1.0)

    k_l, conf_l = kap(S_loc)
    k_r, conf_r = kap(S_reg)
    kappa = k_l * conf_l + (1.0 - conf_l) * k_r
    conf = np.maximum(conf_l, conf_r)
    wz = np.clip(2.0 * (1.0 - f_core), 0.0, 1.0)[qy, qx] * bgw_a[qy, qx]
    allowed = np.maximum(np.maximum(f1[:, 0], f1[:, 2]), 0.02) * kappa * head
    f1[:, 1] -= np.maximum(0.0, f1[:, 1] - allowed) * conf * wz * spill
    out[ys, xs] = f1
    return out


def despill_fast(fg: np.ndarray, a: np.ndarray, strength: float) -> np.ndarray:
    """Mesmo critério do despill antigo (g -> g - (g - max(r,b)) * peso; peso = máx(faixa de borda, escuridão)), só nos pixels da pessoa."""
    H, W = a.shape
    idx = np.flatnonzero(a.ravel() > 0.003)
    out = fg.copy()
    if len(idx) == 0:
        return out
    flat = out.reshape(-1, 3)
    c = flat[idx]
    r, g, b = c[:, 0], c[:, 1], c[:, 2]
    spill = np.maximum(0.0, g - np.maximum(r, b))
    if not (spill > 0.0).any():
        return out
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    m = ((a > 0.02) & (a < 0.98)).astype(np.float32)
    edge_q = box(box(down(m), 1), 1) * 3.0
    e = edge_q[(idx // W) // Q, (idx % W) // Q]
    dark = np.clip((0.45 - y) / 0.25, 0.0, 1.0)
    w = np.clip(np.maximum(e, dark), 0.0, 1.0) * strength
    c[:, 1] = g - spill * w
    flat[idx] = c
    return out


# --------------------------------------------------------------------------------------------------------------------
# Variante E ("simples", 12/11 à noite): o recorte do modelo manda; só mexemos no que ele erra. Princípio: mexer o mínimo
# fora da borda, na borda só uma suavização sutil, e obedecer o modelo (o alfa dele fica; só tapamos buraco no cabelo escuro).
#  1) CURA: o modelo deixa o cabelo escuro "vazado" (alfa baixo no miolo): sobre o fundo escuro vira mancha preta com contorno
#     claro. Onde o quadro ORIGINAL é escuro e não tem verde nenhum, colado na pessoa, é pessoa: o alfa sobe.
#  2) COR: a do modelo (70%) com 30% da original; nos pixels curados, a original (o modelo achava que ali era fundo).
#  3) Limite de verde por classe (parte A da variante D) e tira-verde padrão.
#  4) DESMISTURA na borda translúcida: pixel = alfa*pessoa + (1-alfa)*tela  =>  pessoa = (pixel - (1-alfa)*tela) / alfa, com a cor
#     local da tela medida no próprio quadro; só depois tira o verde. Antes (D) o verde era tirado ANTES de desmisturar e a luz da
#     tela ficava no pixel: era a "linha clara" no contorno do cabelo. O resultado nunca fica mais claro que a cor do passo 3.
def heal_alpha(orig: np.ndarray, alpha: np.ndarray):
    """(alfa reforçado, (ys, xs, peso) dos pixels reforçados, (ys, xs, evidência) dos candidatos). Evidência = pixel escuro sem excesso de verde (g - max(r,b) pequeno frente ao da tela)."""
    H, W = alpha.shape
    gate_q = np.clip(box(box(down(alpha), 2), 2) / 0.3, 0.0, 1.0)         # perto da pessoa (alfa suavizado do modelo)
    # candidatos: a região da porta alargada em 1 bloco, para que a porta (interpolada) chegue a ~0 antes da borda do conjunto (sem degraus)
    near = np.repeat(np.repeat(box((gate_q > 0.02).astype(np.float32), 1) > 0.0, Q, 0), Q, 1)[:H, :W] & (alpha < 0.985)
    ys, xs = np.nonzero(near)
    if len(ys) == 0:
        return alpha, None, None
    o = orig[ys, xs]
    ds = (orig[::7, ::7, 1] - np.maximum(orig[::7, ::7, 0], orig[::7, ::7, 2]))[alpha[::7, ::7] < 0.01]
    D = min(0.6, max(0.12, float(np.median(ds)) if ds.size > 500 else 0.30))     # excesso de verde da tela neste quadro
    key = np.clip(1.0 - (o[:, 1] - np.maximum(o[:, 0], o[:, 2])) / D, 0.0, 1.0)
    ev = np.clip((key - 0.55) / 0.25, 0.0, 1.0) * np.clip((0.35 - _luma(o)) / 0.15, 0.0, 1.0)
    ev = ev * _bilerp(gate_q, ys, xs)
    cand = (ys, xs, ev)                                                   # evidência por pixel: serve ao alfa físico da cor
    # média da evidência numa janela de ~9 px (tira os degraus de bloco do vídeo); só o miolo do cabelo passa
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
    hmap = np.zeros((y1 - y0, x1 - x0), np.float32)
    hmap[ys - y0, xs - x0] = ev
    hmap = box(box(hmap, 2), 2)
    h = np.clip((hmap[ys - y0, xs - x0] - 0.45) / 0.40, 0.0, 1.0)
    old = alpha[ys, xs]
    new = old + (1.0 - old) * h                                           # reforço: soma ao alfa do modelo, nunca fica abaixo dele
    up = new > old + 0.005
    if not up.any():
        return alpha, None, cand
    ys, xs, new, old = ys[up], xs[up], new[up], old[up]
    healed = alpha.copy()
    healed[ys, xs] = new
    return healed, (ys, xs, np.clip((new - old) / 0.3, 0.0, 1.0)), cand


def screen_color(orig: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Cor local da tela (média do fundo em volta, ~±24 px) em 1/4 de resolução; sem fundo por perto, a mediana do quadro."""
    H, W = alpha.shape
    Hq, Wq = -(-H // Q), -(-W // Q)
    o = np.pad(orig[Q // 2::Q, Q // 2::Q], ((0, Hq - len(range(Q // 2, H, Q))), (0, Wq - len(range(Q // 2, W, Q))), (0, 0)), mode="edge")
    a = np.pad(alpha[Q // 2::Q, Q // 2::Q], ((0, Hq - len(range(Q // 2, H, Q))), (0, Wq - len(range(Q // 2, W, Q)))), mode="edge")
    m = (a < 0.02).astype(np.float32)
    num = box(box(o * m[..., None], 3), 3)
    den = box(box(m, 3), 3)
    ds = orig[::7, ::7][alpha[::7, ::7] < 0.01]
    gmed = np.median(ds.reshape(-1, 3), axis=0) if len(ds) > 500 else np.array([0.55, 0.85, 0.5], np.float32)
    return np.where(den[..., None] > 0.02, num / np.maximum(den, 1e-4)[..., None], gmed).astype(np.float32)


def _bilerp(m: np.ndarray, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
    """Lê um mapa em 1/4 de resolução (Hq,Wq[,C]) nas posições (ys,xs) do quadro inteiro, com interpolação bilinear (sem degraus de bloco)."""
    hq, wq = m.shape[:2]
    fy = np.clip((ys + 0.5) / Q - 0.5, 0, hq - 1)
    fx = np.clip((xs + 0.5) / Q - 0.5, 0, wq - 1)
    y0, x0 = np.floor(fy).astype(np.int64), np.floor(fx).astype(np.int64)
    y1, x1 = np.minimum(y0 + 1, hq - 1), np.minimum(x0 + 1, wq - 1)
    wy, wx = fy - y0, fx - x0
    if m.ndim == 3:
        wy, wx = wy[:, None], wx[:, None]
    return m[y0, x0] * (1 - wy) * (1 - wx) + m[y0, x1] * (1 - wy) * wx + m[y1, x0] * wy * (1 - wx) + m[y1, x1] * wy * wx


def _min2d(a: np.ndarray, r: int) -> np.ndarray:
    """Mínimo numa janela (2r+1)² de uma matriz 2D (inf = ausente), sem scipy."""
    H, W = a.shape
    p = np.pad(a, ((r, r), (r, r)), constant_values=np.inf)
    out = np.full_like(a, np.inf)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            np.minimum(out, p[dy:dy + H, dx:dx + W], out=out)
    return out


def unmix_band(c_a: np.ndarray, orig: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Borda translúcida perto do fundo: a luz da cor vira a da desmistura (pixel - (1-alfa)*tela)/alfa, verde tirado depois; nunca mais clara que c_a."""
    ys, xs = np.nonzero((alpha > 0.02) & (alpha < 0.985))
    if len(ys) == 0:
        return c_a
    qy, qx = ys // Q, xs // Q
    bgw = np.clip(box(box(down((alpha < 0.1).astype(np.float32)), 2), 2) * 4.0, 0.0, 1.0)      # fundo por perto (<= ~16 px)
    a = alpha[ys, xs]
    B = _bilerp(screen_color(orig, alpha), ys, xs)
    F = np.clip((orig[ys, xs] - (1.0 - a)[:, None] * B) / np.maximum(a, 0.10)[:, None], 0.0, 1.0)
    F[:, 1] = np.minimum(F[:, 1], np.maximum(F[:, 0], F[:, 2]))                                # tira-verde DEPOIS de desmisturar
    w = np.clip((0.985 - a) / 0.10, 0.0, 1.0) * np.clip((a - 0.02) / 0.06, 0.0, 1.0) * _bilerp(bgw, ys, xs)
    ca = c_a[ys, xs]
    y_ca = _luma(ca)
    ratio = np.minimum(1.0, _luma(F) / np.maximum(y_ca, 1e-3))             # só a LUZ vem da desmistura; o tom fica o de c_a (sem pontos coloridos)
    # piso: a borda não fica mais escura que o trecho mais escuro do miolo opaco em volta (sem "contorno preto" em volta do cabelo)
    core_q = down(alpha, "min") >= 0.985
    ref_q = _min2d(np.where(core_q, _luma(down(c_a)), np.inf).astype(np.float32), 2)
    have_q = np.isfinite(ref_q).astype(np.float32)
    hv = _bilerp(have_q, ys, xs)
    floor_y = np.where(hv > 0.5, 0.85 * _bilerp(np.where(np.isfinite(ref_q), ref_q, 0.0).astype(np.float32), ys, xs) / np.maximum(hv, 1e-3), 0.0)
    ratio = np.minimum(1.0, np.maximum(ratio, floor_y / np.maximum(y_ca, 1e-3)))
    out = c_a.copy()
    out[ys, xs] = ca * (1.0 - w)[:, None] + (ca * ratio[:, None]) * w[:, None]
    return out


def process_E(orig: np.ndarray, fgr: np.ndarray, alpha: np.ndarray, mix: float, spill: float) -> tuple[np.ndarray, np.ndarray]:
    a_e, healed, cand = heal_alpha(orig, alpha)
    a_phys = alpha                       # alfa "físico" (só para calcular a COR): modelo + evidência de que o pixel não tem verde nenhum
    if cand is not None:
        cy, cx, cev = cand
        a_phys = alpha.copy()
        a_phys[cy, cx] = alpha[cy, cx] + (1.0 - alpha[cy, cx]) * cev
    color0 = fgr * (1.0 - mix) + orig * mix
    if healed is not None:
        ys, xs, w_h = healed
        color0[ys, xs] += (orig[ys, xs] - color0[ys, xs]) * w_h[:, None]
    c = despill_fast(edge_colors(orig, fgr, a_e, mix, spill, color0=color0, swap=False), a_e, spill)
    return a_e, np.clip(unmix_band(c, orig, a_phys), 0.0, 1.0)


class TemporalGuard:
    """Tira as "piscadas" claras do cabelo: um pixel escuro da borda que fica bem mais claro por 1 a 3 quadros e depois volta.
    Compara a luz com alfa (o que o olho vê) do quadro com a MEDIANA dos vizinhos (3 antes, 3 depois); se passar da mediana + folga, baixa o alfa
    do pixel (translúcido) ou a cor dele (opaco). Só mexe em pixel escuro perto da borda. Os quadros saem com 3 quadros de atraso (7 ficam na memória).
    Medido em 150 quadros de um vídeo de teste (10-15 s): piscadas no cabelo 51 -> 31 px/quadro (variante E) e 98 -> 23 (variante D)."""

    def __init__(self, k: int = 3, delta: float = 0.012):
        self.k, self.delta = k, delta
        self.frames: list = []
        self.emitted = 0

    def push(self, color: np.ndarray, alpha: np.ndarray) -> list:
        self.frames.append({"c": (color * 255.0 + 0.5).astype(np.uint8), "a": alpha})
        out = []
        while len(self.frames) - self.emitted > self.k:
            out.append(self._emit(self.emitted))
            self.emitted += 1
            while self.emitted > self.k:
                self.frames.pop(0)
                self.emitted -= 1
        return out

    def flush(self) -> list:
        out = []
        while self.emitted < len(self.frames):
            out.append(self._emit(self.emitted))
            self.emitted += 1
        return out

    @staticmethod
    def _pm(fr: dict, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
        c = fr["c"][ys, xs].astype(np.float32)
        return fr["a"][ys, xs] * ((0.2126 * c[:, 0] + 0.7152 * c[:, 1] + 0.0722 * c[:, 2]) / 255.0)

    def _emit(self, i: int):
        """(cor uint8, alfa float) do quadro i, já sem piscadas."""
        cur = self.frames[i]
        c8, a = cur["c"], cur["a"]
        lo, hi = max(0, i - self.k), min(len(self.frames) - 1, i + self.k)
        if hi - lo < 2:
            return c8, a
        # faixa de borda: onde há alfa translúcido, alargada em 1 bloco; só pixel escuro
        tr = down(((a > 0.02) & (a < 0.985)).astype(np.float32))
        H, W = a.shape
        band = np.repeat(np.repeat(box(tr, 1) > 0.0, Q, 0), Q, 1)[:H, :W] & (a > 0.02)
        ys, xs = np.nonzero(band)
        if len(ys) == 0:
            return c8, a
        pm = self._pm(cur, ys, xs)
        dark = pm < 0.35 * np.maximum(a[ys, xs], 1e-3)               # luma do pixel < 0,35
        ys, xs, pm = ys[dark], xs[dark], pm[dark]
        if len(ys) == 0:
            return c8, a
        med = np.median(np.stack([self._pm(self.frames[j], ys, xs) for j in range(lo, hi + 1) if j != i]), axis=0)
        lim = med + self.delta
        over = pm > lim
        if not over.any():
            return c8, a
        f = (lim[over] / pm[over]).astype(np.float32)
        yy, xx = ys[over], xs[over]
        trn = a[yy, xx] < 0.985
        a2, c2 = a, c8
        if trn.any():
            a2 = a.copy()
            a2[yy[trn], xx[trn]] = a[yy[trn], xx[trn]] * f[trn]
        op = ~trn
        if op.any():
            c2 = c8.copy()
            c2[yy[op], xx[op]] = (c8[yy[op], xx[op]].astype(np.float32) * f[op][:, None] + 0.5).astype(np.uint8)
        return c2, a2


def _person_box(alpha: np.ndarray, margin: int = 96):
    """Retângulo (y0, y1, x0, x1), alinhado aos blocos de Q px, que cobre a pessoa + margem; None se a pessoa ocupa quase o quadro todo (ou não há pessoa)."""
    H, W = alpha.shape
    m = alpha > 0.1
    rows, cols = np.flatnonzero(m.any(axis=1)), np.flatnonzero(m.any(axis=0))
    if len(rows) == 0:
        return None
    y0, y1 = max(0, (int(rows[0]) - margin) // Q * Q), min(H, -(-(int(rows[-1]) + 1 + margin) // Q) * Q)
    x0, x1 = max(0, (int(cols[0]) - margin) // Q * Q), min(W, -(-(int(cols[-1]) + 1 + margin) // Q) * Q)
    return None if (y1 - y0) * (x1 - x0) > 0.75 * H * W else (y0, y1, x0, x1)


def process(orig: np.ndarray, fgr: np.ndarray, alpha: np.ndarray, mix: float, spill: float) -> tuple[np.ndarray, np.ndarray]:
    """(alfa final, cor final 0..1). A conta é feita só no retângulo da pessoa (o resto é fundo puro): ~2x mais rápido; fora dele a cor sai preta."""
    bx = _person_box(alpha)
    if bx is None:
        return _process_full(orig, fgr, alpha, mix, spill)
    y0, y1, x0, x1 = bx
    a2, c2 = _process_full(orig[y0:y1, x0:x1], fgr[y0:y1, x0:x1], alpha[y0:y1, x0:x1], mix, spill)
    A = alpha.copy()
    A[y0:y1, x0:x1] = a2
    C = np.zeros_like(orig)
    C[y0:y1, x0:x1] = c2
    return A, C


def _process_full(orig: np.ndarray, fgr: np.ndarray, alpha: np.ndarray, mix: float, spill: float) -> tuple[np.ndarray, np.ndarray]:
    """(alfa final, cor final do sujeito 0..1). Variantes: E simples (padrão) | D por classe | C média antiga (MATTE_VARIANT)."""
    if VARIANT == "E":
        try:
            return process_E(orig, fgr, alpha, mix, spill)
        except Exception as e:  # noqa: BLE001  (nunca derruba o render: volta ao método por classe)
            print(f"AVISO recorte simples falhou ({type(e).__name__}: {e}); usando o método por classe", flush=True)
    return alpha, edge_pipeline(orig, fgr, alpha, mix, spill)


def edge_pipeline(orig: np.ndarray, fgr: np.ndarray, alpha: np.ndarray, mix: float, spill: float) -> np.ndarray:
    """Cor final do sujeito (0..1) a partir da cor original, da cor estimada pelo modelo e do alfa."""
    if VARIANT in ("D", "E"):
        try:
            return np.clip(despill_fast(edge_colors(orig, fgr, alpha, mix, spill), alpha, spill), 0.0, 1.0)
        except Exception as e:  # noqa: BLE001  (nunca derruba o render: volta ao método antigo)
            print(f"AVISO cor de borda por classe falhou ({type(e).__name__}: {e}); usando o método antigo", flush=True)
    color = fgr * (1.0 - mix) + orig * mix
    return np.clip(despill(extend_color(color, alpha, *EXT), alpha, spill), 0.0, 1.0)


def start_writers(a, W: int, H: int):
    """Os dois codificadores (cor em x264 10 bits 4:4:4 e alfa em ffv1), iguais aos do render."""
    common_in = ["-f", "rawvideo", "-s", f"{W}x{H}", "-framerate", a.fps]
    w_c = subprocess.Popen([a.ffmpeg, "-v", "error", "-y", "-nostdin", *common_in, "-pix_fmt", "rgb24", "-i", "-",
                            "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd+full_chroma_int,format=yuv444p10le",
                            "-c:v", "libx264", "-threads", "2", "-crf", "12", "-preset", "veryfast", "-pix_fmt", "yuv444p10le",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", a.out_color],
                           stdin=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
    w_a = subprocess.Popen([a.ffmpeg, "-v", "error", "-y", "-nostdin", *common_in, "-pix_fmt", "gray", "-i", "-",
                            "-c:v", "ffv1", "-threads", "1", "-level", "3", "-pix_fmt", "gray", a.out_alpha],
                           stdin=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
    return w_c, w_a


def dump_raw(a) -> int:
    """Roda só o modelo em UM quadro (com aquecimento) e guarda a cor original e as estimativas do modelo, para refazer a borda sem rodar o modelo de novo."""
    W, H = a.width, a.height
    n_, _, d_ = a.fps.partition("/")
    fpsf = float(n_) / float(d_ or 1)
    warm = min(1.0, a.start)
    skip = int(round(warm * fpsf))
    pre = "setparams=colorspace=bt709," if a.tag in ("", "unknown", "reserved") and H >= 720 else ""
    reader = subprocess.Popen([a.ffmpeg, "-v", "error", "-nostdin", "-ss", f"{a.start - warm:.3f}", "-t", f"{a.length + warm:.3f}", "-i", a.src, "-an",
                               "-vf", f"{pre}scale={W}:{H}:in_range=auto:in_color_matrix=auto", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                              stdout=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
    so = ort.SessionOptions()
    so.intra_op_num_threads = 4
    so.add_session_config_entry("session.intra_op.allow_spinning", "0")
    sess = ort.InferenceSession(a.model, so, providers=["CPUExecutionProvider"])
    ds = np.array([min(1.0, 512.0 / max(W, H))], np.float32)
    rec = [np.zeros((1, 1, 1, 1), np.float32) for _ in range(4)]
    size = W * H * 3
    n, last = 0, None
    while True:
        buf = reader.stdout.read(size)
        if len(buf) < size:
            break
        orig8 = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        fgr, pha, *rec = sess.run(None, {"src": (orig8.astype(np.float32) / 255.0).transpose(2, 0, 1)[None], "r1i": rec[0], "r2i": rec[1],
                                         "r3i": rec[2], "r4i": rec[3], "downsample_ratio": ds})
        n += 1
        if n > skip:
            last = (orig8.copy(), fgr[0].transpose(1, 2, 0).astype(np.float16), pha[0, 0].astype(np.float16))
    reader.stdout.close()
    reader.wait()
    if last is None:
        return 1
    np.savez(a.dump_raw, orig=last[0], fgr=last[1], pha=last[2])
    print("FIM 1", flush=True)
    return 0


def post_raw(a) -> int:
    """Refaz só a borda (cor e alfa finais) a partir do dump do modelo e grava cor.mkv/alfa.mkv de 1 quadro."""
    z = np.load(a.post_raw)
    orig = z["orig"].astype(np.float32) / 255.0
    alpha, color = process(orig, z["fgr"].astype(np.float32), np.clip(z["pha"].astype(np.float32), 0.0, 1.0), a.mix, a.spill)
    H, W = alpha.shape
    w_c, w_a = start_writers(a, W, H)
    w_c.communicate((color * 255.0 + 0.5).astype(np.uint8).tobytes())
    w_a.communicate((alpha * 255.0 + 0.5).astype(np.uint8).tobytes())
    print("FIM 1", flush=True)
    return 0 if w_c.returncode == 0 and w_a.returncode == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", required=True)
    ap.add_argument("--src", default="")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--length", type=float, default=0.0)      # 0 = até o fim
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--fps", required=True)                    # "30000/1001"
    ap.add_argument("--model", default="")
    ap.add_argument("--out-color", default="")
    ap.add_argument("--out-alpha", default="")
    ap.add_argument("--mix", type=float, default=0.3)          # parte da cor ORIGINAL misturada à cor do modelo
    ap.add_argument("--spill", type=float, default=1.0)        # força do tira-verde
    ap.add_argument("--tag", default="")                       # etiqueta de cor da origem
    ap.add_argument("--variant", default="")                   # E (simples) ou D (por partes do corpo); vazio = o padrão do programa
    ap.add_argument("--dump-raw", default="")                  # só o modelo, 1 quadro -> .npz (quadro ao vivo)
    ap.add_argument("--post-raw", default="")                  # só a borda, a partir do .npz -> cor.mkv/alfa.mkv de 1 quadro
    a = ap.parse_args()
    if a.variant:
        globals()["VARIANT"] = a.variant
    if a.post_raw:
        return post_raw(a)
    if a.dump_raw:
        return dump_raw(a)
    if not (a.src and a.model and a.out_color and a.out_alpha):
        ap.error("faltam --src, --model, --out-color e --out-alpha")
    W, H = a.width, a.height
    n_, _, d_ = a.fps.partition("/")
    fpsf = float(n_) / float(d_ or 1)
    warm = min(1.0, a.start)                       # aquecimento: o modelo é recorrente e precisa de alguns quadros antes
    skip = int(round(warm * fpsf))
    pre = "setparams=colorspace=bt709," if a.tag in ("", "unknown", "reserved") and H >= 720 else ""
    t_arg = ["-t", f"{a.length + warm:.3f}"] if a.length > 0 else []
    reader = subprocess.Popen([a.ffmpeg, "-v", "error", "-nostdin", "-ss", f"{a.start - warm:.3f}", *t_arg, "-i", a.src, "-an",
                               "-vf", f"{pre}scale={W}:{H}:in_range=auto:in_color_matrix=auto", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                              stdout=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
    common_in = ["-f", "rawvideo", "-s", f"{W}x{H}", "-framerate", a.fps]
    w_c = subprocess.Popen([a.ffmpeg, "-v", "error", "-y", "-nostdin", *common_in, "-pix_fmt", "rgb24", "-i", "-",
                            "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd+full_chroma_int,format=yuv444p10le",
                            "-c:v", "libx264", "-threads", "2", "-crf", "12", "-preset", "veryfast", "-pix_fmt", "yuv444p10le",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", a.out_color],
                           stdin=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
    w_a = subprocess.Popen([a.ffmpeg, "-v", "error", "-y", "-nostdin", *common_in, "-pix_fmt", "gray", "-i", "-",
                            "-c:v", "ffv1", "-threads", "1", "-level", "3", "-pix_fmt", "gray", a.out_alpha],
                           stdin=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
    so = ort.SessionOptions()
    so.intra_op_num_threads = 4                       # mais threads que isso disputam com os codificadores e ficam 10x mais lentas
    so.add_session_config_entry("session.intra_op.allow_spinning", "0")
    sess = ort.InferenceSession(a.model, so, providers=["CPUExecutionProvider"])
    ds = np.array([min(1.0, 512.0 / max(W, H))], np.float32)
    rec = [np.zeros((1, 1, 1, 1), np.float32) for _ in range(4)]
    size = W * H * 3
    n = 0
    st = {"written": 0, "err": None}
    tm = {"leitura": 0.0, "modelo": 0.0, "tira-verde": 0.0, "gravacao": 0.0}
    q: queue.Queue = queue.Queue(maxsize=3)         # quadros já passados pelo modelo, esperando o tratamento da borda

    # filtro temporal só em trechos de verdade (o quadro ao vivo tem 1 quadro e não tem vizinhos)
    guard = TemporalGuard() if os.environ.get("MATTE_TEMPORAL", "1") != "0" and (a.length == 0 or a.length * fpsf > 6) else None

    def emit(frames_out: list) -> None:
        for col, alp in frames_out:
            t1 = time.time()
            w_c.stdin.write(col.tobytes() if col.dtype == np.uint8 else (col * 255.0 + 0.5).astype(np.uint8).tobytes())
            w_a.stdin.write((alp * 255.0 + 0.5).astype(np.uint8).tobytes())
            tm["gravacao"] += time.time() - t1
            st["written"] += 1
            if st["written"] % 4 == 0:
                print(f"PROG {st['written']}", flush=True)

    def handle(item) -> None:
        orig_, fgr_, alpha_ = item
        t1 = time.time()
        alpha_, color = process(orig_, fgr_, alpha_, a.mix, a.spill)
        ready = guard.push(color, alpha_) if guard else [(color, alpha_)]
        tm["tira-verde"] += time.time() - t1
        emit(ready)

    def consumer() -> None:
        """2ª linha: tira-verde/desmistura + gravação, em paralelo com o modelo do quadro seguinte (o numpy e o onnxruntime soltam o GIL)."""
        try:
            while True:
                item = q.get()
                if item is None:
                    break
                handle(item)
            if guard:
                emit(guard.flush())
        except Exception as e:  # noqa: BLE001
            st["err"] = e
            print(f"ERRO no tratamento da borda: {type(e).__name__}: {e}", flush=True)
            while q.get() is not None:              # esvazia a fila para a 1ª linha não travar
                pass

    seq_mode = os.environ.get("MATTE_PIPELINE", "1") == "0"
    worker = threading.Thread(target=consumer, name="borda", daemon=True)
    worker.start()
    while st["err"] is None:
        t0 = time.time()
        buf = reader.stdout.read(size)
        tm["leitura"] += time.time() - t0
        if len(buf) < size:
            break
        orig = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255.0
        t0 = time.time()
        fgr, pha, *rec = sess.run(None, {"src": orig.transpose(2, 0, 1)[None], "r1i": rec[0], "r2i": rec[1], "r3i": rec[2],
                                         "r4i": rec[3], "downsample_ratio": ds})
        tm["modelo"] += time.time() - t0
        n += 1
        if n <= skip:
            continue
        if seq_mode:                       # MATTE_PIPELINE=0: tudo na mesma linha (para comparar o tempo)
            handle((orig, fgr[0].transpose(1, 2, 0), np.clip(pha[0, 0], 0.0, 1.0)))
        else:
            q.put((orig, fgr[0].transpose(1, 2, 0), np.clip(pha[0, 0], 0.0, 1.0)))
    q.put(None)
    worker.join()
    if seq_mode and guard:
        emit(guard.flush())
    written = st["written"]
    for p in (w_c, w_a):
        p.stdin.close()
    reader.stdout.close()
    reader.wait()
    for p in (w_c, w_a):
        p.wait()
    print("TEMPOS " + " ".join(f"{k}={v / max(1, n):.2f}s/quadro" for k, v in tm.items()), flush=True)
    print(f"FIM {written}", flush=True)
    return 0 if written > 0 and st["err"] is None and w_c.returncode == 0 and w_a.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
