"""Diagnóstico automático: cada preview/render deixa uma pasta em ./logs com tudo que aconteceu.

Dentro de cada pasta (logs/AAAAMMDD-HHMMSS_preview_xxxx/):
  resumo.txt        leitura rápida em português, com ALERTAS quando algo está errado
  ajustes.json      os ajustes usados (inclui a cor do verde medida, o nível da fala, o silêncio de sala achado)
  comando.txt       o comando do ffmpeg, um argumento por linha
  filtro_video.txt / filtro_audio.txt   os filtros, para ler com calma
  ffmpeg.log        o que o ffmpeg escreveu (avisos e erros)
  analise_audio.json  medidas do áudio (antes x depois)
  quadro_*.png / comparacao_*.png  imagens do original e do resultado nos mesmos instantes
Só usa a biblioteca padrão e o ffmpeg (roda no pendrive).
"""
from __future__ import annotations

import json
import math
import re
import struct
import subprocess
import time
from pathlib import Path

import pipeline as P

NO_WINDOW = P.CREATE_NO_WINDOW
_NOISE_WARN: list[str] = []


def _run(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=NO_WINDOW)


class JobLog:
    def __init__(self, base: Path, kind: str, job_id: str):
        self.dir = base / f"{time.strftime('%Y%m%d-%H%M%S')}_{kind}_{job_id}"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.alerts: list[str] = []
        self.lines: list[str] = []

    def json(self, name: str, obj) -> None:
        (self.dir / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    def text(self, name: str, txt: str) -> None:
        (self.dir / name).write_text(txt, encoding="utf-8")

    def note(self, line: str) -> None:
        self.lines.append(line)

    def alert(self, line: str) -> None:
        self.alerts.append(line)

    def finish(self, header: str) -> str:
        body = [header, ""]
        if self.alerts:
            body.append("=== ALERTAS ===")
            body += [f" ! {a}" for a in self.alerts]
            body.append("")
        else:
            body.append("Sem alertas.")
            body.append("")
        body += self.lines
        txt = "\n".join(body) + "\n"
        self.text("resumo.txt", txt)
        return txt


# ---------------------------------------------------------------- áudio
def pcm_levels(ffmpeg: str, media: str, ss: float = 0.0, dur: float | None = None, sr: int = 8000):
    """Níveis RMS (dBFS) de janelas de 100 ms, mais pico e amostras no limite. Devolve (levels, peak_db, clipped, seconds)."""
    cmd = [ffmpeg, "-v", "error"]
    if ss:
        cmd += ["-ss", f"{ss:.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", media, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    cp = _run(cmd, 600)
    n = len(cp.stdout) // 2
    if n < sr // 2:
        return [], -120.0, 0, 0.0
    smp = struct.unpack("<%dh" % n, cp.stdout[: n * 2])
    win = sr // 10
    lv = []
    for i in range(0, n - win, win):
        seg = smp[i:i + win]
        lv.append(20 * math.log10(max(1.0, math.sqrt(sum(x * x for x in seg) / win)) / 32768.0))
    peak = max(max(smp), -min(smp))
    clipped = sum(1 for x in smp if x >= 32700 or x <= -32700)
    return lv, 20 * math.log10(max(1, peak) / 32768.0), clipped, n / sr


def level_stats(lv: list[float]) -> dict:
    if not lv:
        return {}
    s = sorted(lv)
    p10, p50, p90 = s[len(s) // 10], s[len(s) // 2], s[int(len(s) * 0.9)]
    steps = [abs(a - b) for a, b in zip(lv, lv[1:])]
    big = sum(1 for d in steps if d > 18)
    # maior trecho contínuo abaixo de -55 dBFS (silêncio de verdade / áudio "caindo")
    longest = cur = 0
    for v in lv:
        cur = cur + 1 if v < -55 else 0
        longest = max(longest, cur)
    return {"pausa_p10_db": round(p10, 1), "mediana_db": round(p50, 1), "fala_p90_db": round(p90, 1),
            "SNR_db": round(p90 - p10, 1), "quedas_bruscas_18dB": big, "pct_janelas": len(lv),
            "silencio_continuo_s": round(longest / 10.0, 1),
            "pct_abaixo_-55dB": round(100.0 * sum(1 for v in lv if v < -55) / len(lv), 1)}


def loudness(ffmpeg: str, media: str, ss: float = 0.0, dur: float | None = None) -> dict:
    cmd = [ffmpeg, "-hide_banner", "-nostdin"]
    if ss:
        cmd += ["-ss", f"{ss:.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", media, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]
    txt = _run(cmd, 900).stderr.decode("utf-8", "replace")
    tail = txt[txt.rfind("Summary:"):] if "Summary:" in txt else ""
    out = {}
    for key, pat in (("lufs_integrado", r"I:\s+(-?[\d.]+)\s+LUFS"), ("faixa_LRA", r"LRA:\s+(-?[\d.]+)\s+LU"),
                     ("pico_real_dBTP", r"Peak:\s+(-?[\d.]+)\s+dBFS")):
        m = re.search(pat, tail)
        if m:
            out[key] = float(m.group(1))
    return out


def analyze_audio(log: JobLog, ffmpeg: str, src: str, out: str, start: float, length: float, has_audio: bool,
                  target_lufs: float | None = None) -> None:
    """Compara o áudio do resultado com o do original nos mesmos instantes e registra alertas."""
    if not has_audio:
        log.note("ÁUDIO: o vídeo de origem não tem áudio.")
        return
    lv_o, pk_o, cl_o, sec_o = pcm_levels(ffmpeg, src, start, length)
    lv_p, pk_p, cl_p, sec_p = pcm_levels(ffmpeg, out, 0.0, length)  # mesmo trecho do original (render longo: só os primeiros segundos)
    so, sp = level_stats(lv_o), level_stats(lv_p)
    lo = loudness(ffmpeg, src, start, length)
    lp = loudness(ffmpeg, out, 0.0, length)
    data = {"original": {**so, **lo, "pico_amostra_dB": round(pk_o, 1), "segundos": round(sec_o, 2)},
            "resultado": {**sp, **lp, "pico_amostra_dB": round(pk_p, 1), "amostras_no_limite": cl_p, "segundos": round(sec_p, 2)}}
    log.json("analise_audio.json", data)

    log.note("ÁUDIO (original -> resultado)")
    for k in ("fala_p90_db", "pausa_p10_db", "SNR_db", "lufs_integrado", "faixa_LRA", "pico_real_dBTP", "quedas_bruscas_18dB", "pct_abaixo_-55dB"):
        log.note(f"  {k:22s} {data['original'].get(k, '-')!s:>8} -> {data['resultado'].get(k, '-')!s:>8}")
    log.note(f"  duração                {data['original']['segundos']:>8} -> {data['resultado']['segundos']:>8} s")

    if not lv_p:
        log.alert("ÁUDIO AUSENTE: o arquivo gerado não tem áudio legível.")
        return
    if sp.get("fala_p90_db", -99) < -45:
        log.alert(f"ÁUDIO QUASE MUDO: a fala está em {sp.get('fala_p90_db')} dBFS (deveria estar perto de -15).")
    if sp.get("pct_abaixo_-55dB", 0) > 60:
        log.alert(f"ÁUDIO: {sp['pct_abaixo_-55dB']}% do tempo está em silêncio quase total.")
    if sp.get("SNR_db", 0) < so.get("SNR_db", 0) - 3.0:
        log.alert(f"RUÍDO PIOROU: diferença voz x ruído caiu de {so.get('SNR_db')} para {sp.get('SNR_db')} dB.")
    if sp.get("quedas_bruscas_18dB", 0) > max(3, so.get("quedas_bruscas_18dB", 0) * 2 + 2):
        log.alert(f"FALA PICOTADA: {sp['quedas_bruscas_18dB']} quedas bruscas de volume (original: {so.get('quedas_bruscas_18dB', 0)}). "
                  "Reduza 'Redução de ruído' e 'Intensidade da redução de eco'.")
    if cl_p > 20:
        log.alert(f"CORTE (clipping): {cl_p} amostras no limite máximo — o som estoura.")
    if target_lufs is not None and lp.get("lufs_integrado") is not None and abs(lp["lufs_integrado"] - target_lufs) > 3.0:
        log.alert(f"VOLUME FORA DO ALVO: {lp['lufs_integrado']} LUFS (alvo {target_lufs}).")
    if abs(sec_p - sec_o) > 0.35:
        log.alert(f"DURAÇÃO DIFERENTE: áudio {sec_p:.2f}s x original {sec_o:.2f}s (possível perda de sincronia).")


# ---------------------------------------------------------------- imagens
def grab_frames(log: JobLog, ffmpeg: str, src: str, out: str, start: float, length: float) -> list[str]:
    """Salva quadros do original e do resultado nos mesmos instantes e uma imagem lado a lado."""
    made = []
    for i, frac in enumerate((0.12, 0.5, 0.88), 1):
        t_out = max(0.0, length * frac)
        o_png = log.dir / f"quadro_original_{i}.png"
        p_png = log.dir / f"quadro_resultado_{i}.png"
        c_png = log.dir / f"comparacao_{i}.png"
        _run([ffmpeg, "-v", "error", "-y", "-ss", f"{start + t_out:.3f}", "-i", src, "-frames:v", "1", str(o_png)], 120)
        _run([ffmpeg, "-v", "error", "-y", "-ss", f"{t_out:.3f}", "-i", out, "-frames:v", "1", str(p_png)], 120)
        if o_png.exists() and p_png.exists():
            _run([ffmpeg, "-v", "error", "-y", "-i", str(o_png), "-i", str(p_png), "-filter_complex",
                  "[0:v]scale=960:-2[a];[1:v]scale=960:-2[b];[a][b]hstack", "-frames:v", "1", str(c_png)], 120)
            made.append(c_png.name)
    return made


def video_sanity(log: JobLog, ffprobe: str, out: str, expect_len: float, src_wh: tuple | None = None, upscale_on: bool = False) -> None:
    try:
        info = P.probe(ffprobe, out)
    except Exception as e:  # noqa: BLE001
        log.alert(f"O arquivo gerado não abre no ffprobe: {e}")
        return
    log.note(f"RESULTADO: {info['width']}x{info['height']} {info['fps']:.2f} fps, {info['duration']:.2f}s, codec {info['codec']}, "
             f"{'com' if info['has_audio'] else 'SEM'} áudio")
    if src_wh and upscale_on and min(info["width"], info["height"]) != 1080:
        log.alert(f"TAMANHO FORA DO PADRÃO: origem {src_wh[0]}x{src_wh[1]}, resultado {info['width']}x{info['height']} (esperado lado menor = 1080).")
    if expect_len and abs(info["duration"] - expect_len) > 0.6:
        log.alert(f"DURAÇÃO DO VÍDEO: {info['duration']:.2f}s, esperado {expect_len:.2f}s.")


def describe_settings(s: dict) -> list[str]:
    out = ["AJUSTES USADOS (valores principais)"]
    keys = ["mod_chroma", "mod_grade", "mod_upscale", "mod_audio", "bg_mode", "bg_style", "chroma_color", "similarity", "blend",
            "despill", "choke", "edge_width", "clean", "trim", "isolate", "warmth", "contrast", "gamma", "saturation", "light", "rim",
            "auto_exposure", "resolution", "sharpen", "clarity", "denoise", "a_nr", "a_room", "a_body", "a_boxy", "a_presence", "a_lufs"]
    for k in keys:
        if k in s:
            out.append(f"  {k:14s} {s[k]}")
    sub, room = s.get("_subject"), s.get("_room")
    if room and not room.get("ok") and s.get("mod_audio") and s.get("a_nr", 0) > 0:
        _NOISE_WARN.append("RUÍDO NÃO REDUZIDO: não achei uma pausa de silêncio de sala neste vídeo/trecho. Escolha um início de teste com uma pausa (ou grave 2 s de silêncio no começo).")
    if sub:
        out.append(f"  (medido) pessoa: centro x={sub.get('cx', 0):.2f}, topo y={sub.get('top', 0):.2f}, luminância da pele p80={sub.get('luma_p80', 0):.2f}, ok={sub.get('ok')}")
    if room:
        if not room.get("ok") and s.get("mod_audio") and s.get("a_nr", 0) > 0:
            out.append("  !! SEM REDUÇÃO DE RUÍDO: não achei 1 s de silêncio de sala estável neste vídeo/trecho.")
        out.append(f"  (medido) áudio: fala={room.get('speech_db', 0):.1f} dBFS, silêncio de sala em {room.get('tone_at', 0):.1f}s "
                   f"({room.get('tone_db', 0):.1f} dBFS), aproveitável={room.get('ok')} {room.get('why', '')}")
        if room.get("loud"):
            out.append(f"  (medido) loudnorm passo 1: {room['loud']}")
        elif s.get("a_loudnorm"):
            out.append("  (medido) loudnorm passo 1: FALHOU (usou 1 passo)")
    return out
