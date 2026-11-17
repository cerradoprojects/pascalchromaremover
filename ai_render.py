"""Render com upscaling por IA offline (Real-ESRGAN ncnn Vulkan), em pedaços, sem encher o disco.

Fluxo de cada pedaço (~2 s de vídeo):
  A) FFmpeg roda o mesmo grafo do programa (recorte, cor, luz, fundo) NA RESOLUÇÃO DA ORIGEM e grava PNGs;
  B) o Real-ESRGAN amplia os PNGs (2x);
  C) FFmpeg mistura  IA x (original ampliado com lanczos)  na proporção do slider (padrão 60/40), aplica nitidez/grão e codifica.
No fim: junta os pedaços, gera o áudio pelo mesmo caminho do render normal e une tudo. Só saída MP4 (fundo de estúdio).
"""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import pipeline as P
import upscale_ai as UA

CHUNK = 48   # quadros por pedaço


def _run(cmd: list[str], holder: dict | None = None, timeout: int = 1800) -> tuple[int, str]:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=P.CREATE_NO_WINDOW)
    if holder is not None:
        holder["proc"] = proc
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        return 1, "tempo esgotado"
    return proc.returncode, out.decode("utf-8", "replace")[-1500:]


def prepare(ffmpeg: str, src: str, s: dict, info: dict, at: float) -> dict:
    """Mede cor do verde e posição da pessoa uma vez só (o render inteiro usa os mesmos valores)."""
    s = P.resolve_key_color(ffmpeg, src, s, info, at)
    s = dict(s)
    s["_subject"] = P.analyze_subject(ffmpeg, src, at, s["chroma_color"] if s["chroma_color"] != "auto" else "#95e591")
    return s


def stage_a_cmd(ffmpeg: str, src: str, s: dict, info: dict, t0: float, n: int, indir: Path) -> list[str]:
    fc, lab = P.build_video(s, info, False, False, stage_a=True)
    return [ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error", "-ss", f"{t0:.4f}", "-i", src,
            "-filter_complex", fc, "-map", f"[{lab}]", "-frames:v", str(n), "-c:v", "png", "-compression_level", "1",
            "-start_number", "1", "-t", f"{(n + 1) / info['fps']:.4f}", str(indir / "%06d.png")]


def sharp_chain(s: dict) -> str:
    f: list[str] = []
    if s["clarity"] > 0:
        f.append(f"unsharp=11:11:{s['clarity'] * 0.9:.3f}:11:11:0.0")
    if s["sharpen"] > 0:
        f.append(f"cas=strength={s['sharpen']:.3f}" if s["sharp_method"] == "cas" else f"unsharp=5:5:{s['sharpen'] * 1.4:.3f}:5:5:0.0")
    if s["grain"] > 0:
        f.append(f"noise=alls={s['grain']:.1f}:allf=t")
    return "".join(x + "," for x in f)


def blend_graph(s: dict, W: int, H: int) -> str:
    sc = f"scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int,format=gbrp"
    op = max(0.0, min(1.0, float(s["ai_blend"])))
    return (f"[0:v]{sc}[a];[1:v]{sc}[b];[a][b]blend=all_mode=normal:all_opacity={op:.3f}:shortest=1,"
            f"scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+error_diffusion,format=yuv444p10le,{sharp_chain(s)}"
            "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+error_diffusion,format=yuv420p[vout]")


def stage_c_cmd(ffmpeg: str, info: dict, s: dict, W: int, H: int, outdir: Path, indir: Path, seg: Path) -> list[str]:
    fps = info["fps_str"]
    return [ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error",
            "-framerate", fps, "-i", str(outdir / "%06d.png"), "-framerate", fps, "-i", str(indir / "%06d.png"),
            "-filter_complex", blend_graph(s, W, H), "-map", "[vout]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(seg)]


def render(ffmpeg: str, ffprobe: str, base: Path, src: str, s: dict, info: dict, out_path: str, work: Path,
           on_progress=None, holder: dict | None = None, cancelled=lambda: False, note=lambda m: None) -> tuple[bool, str]:
    exe = UA.find_exe(base)
    if exe is None:
        return False, UA.HOW_TO
    model = s["ai_model"]
    scale = UA.native_scale(model, 2)
    fps = info["fps"]
    total = max(1, int(round((info["duration"] or 1) * fps)))
    W, H = P.target_size(info, s, False)
    s = prepare(ffmpeg, src, s, info, min(10.0, (info["duration"] or 20) * 0.3))
    shutil.rmtree(work, ignore_errors=True)
    segdir = work / "seg"
    segdir.mkdir(parents=True, exist_ok=True)
    segs: list[Path] = []
    t_start = time.time()
    done = 0
    k = 0
    while done < total:
        if cancelled():
            return False, "cancelado"
        n = min(CHUNK, total - done)
        indir, outdir = work / "in", work / "out"
        for d in (indir, outdir):
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True, exist_ok=True)
        t0 = done * 1001.0 / 30000.0 if abs(fps - 29.97) < 0.01 else done / fps
        code, tail = _run(stage_a_cmd(ffmpeg, src, s, info, t0, n, indir), holder)
        if not any(indir.glob("*.png")):
            if segs:
                break
            return False, "Falha ao preparar os quadros (etapa A): " + tail
        n_real = len(list(indir.glob("*.png")))
        last_chunk = n_real < n   # a origem acabou antes do previsto
        base_pct = 100.0 * done / total

        def cb(p: float, _n=n_real, _b=base_pct) -> None:
            if on_progress:
                el = time.time() - t_start
                frac = (_b + (100.0 * _n / total) * p / 100.0) / 100.0
                eta = el * (1 - frac) / frac if frac > 0.002 else 0
                on_progress(min(99.0, frac * 100.0), f"Ampliação avançada: pedaço {k + 1} — falta cerca de {UA.fmt_eta(eta)}" if eta else "Ampliação avançada: iniciando…")

        code, tail = UA.process_folder(exe, indir, outdir, model, scale, on_line=cb, holder=holder)
        if cancelled():
            return False, "cancelado"
        if code != 0 or len(list(outdir.glob("*.png"))) < n_real:
            return False, "A ampliação avançada falhou (confira se a placa de vídeo tem o driver atualizado): " + tail
        seg = segdir / f"seg_{k:05d}.mp4"
        code, tail = _run(stage_c_cmd(ffmpeg, info, s, W, H, outdir, indir, seg), holder)
        if code != 0 or not seg.exists():
            return False, "Falha ao misturar e codificar (etapa C): " + tail
        segs.append(seg)
        done += n_real
        k += 1
        if last_chunk:
            break
        if on_progress:
            on_progress(min(99.0, 100.0 * done / total), f"Ampliação avançada: {done}/{total} quadros")
    lst = work / "lista.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs), encoding="utf-8")
    vid = work / "video.mp4"
    code, tail = _run([ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(vid)])
    if code != 0:
        return False, "Falha ao juntar os pedaços: " + tail
    acmd = P.build_audio_command(ffmpeg, src, s, info, str(work / "audio.m4a"))
    if acmd:
        code, tail = _run(acmd, holder)
        if code != 0:
            return False, "Falha no áudio: " + tail
        code, tail = _run([ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error", "-i", str(vid), "-i", str(work / "audio.m4a"),
                           "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", out_path])
    else:
        code, tail = _run([ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error", "-i", str(vid), "-c", "copy", "-movflags", "+faststart", out_path])
    shutil.rmtree(work, ignore_errors=True)
    return (code == 0), ("" if code == 0 else "Falha ao unir vídeo e áudio: " + tail)


def test_frames(ffmpeg: str, base: Path, src: str, s: dict, info: dict, times: list[float], out_dir: Path, work: Path) -> dict:
    """Gera 3 variantes (lanczos / IA / mistura) de alguns quadros para o usuário comparar. Devolve nomes e segundos por quadro."""
    exe = UA.find_exe(base)
    if exe is None:
        return {"error": UA.HOW_TO}
    model = s["ai_model"]
    scale = UA.native_scale(model, 2)
    s = prepare(ffmpeg, src, s, info, times[0] if times else 0.0)
    W, H = P.target_size(info, s, False)
    shutil.rmtree(work, ignore_errors=True)
    indir, outdir = work / "in", work / "out"
    for d in (indir, outdir):
        d.mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(times, 1):
        fc, lab = P.build_video(s, info, False, False, stage_a=True)
        _run([ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", src, "-filter_complex", fc,
              "-map", f"[{lab}]", "-frames:v", "1", str(indir / f"{i:06d}.png")])
    t0 = time.time()
    code, tail = UA.process_folder(exe, indir, outdir, model, scale)
    per = (time.time() - t0) / max(1, len(times))
    if code != 0:
        return {"error": "A ampliação avançada falhou: " + tail}
    sub = s.get("_subject") or {"cx": 0.5, "top": 0.1}
    cx, cy = int(sub["cx"] * W), int((sub["top"] + 0.10) * H)
    cw = min(W, 900)
    x0, y0 = max(0, min(W - cw, cx - cw // 2)), max(0, min(H - cw, cy - cw // 3))
    names = []
    for i in range(1, len(times) + 1):
        a, b = outdir / f"{i:06d}.png", indir / f"{i:06d}.png"
        tag = f"ia_{i}"
        crop = f"crop={cw}:{cw}:{x0}:{y0}"
        sc = f"scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int"
        op = max(0.0, min(1.0, float(s["ai_blend"])))
        fc = (f"[0:v]{sc},{crop}[ai];[1:v]{sc},{crop}[lz];[0:v]{sc}[a2];[1:v]{sc}[b2];"
              f"[a2][b2]blend=all_mode=normal:all_opacity={op:.3f}:shortest=1,{crop}[bl];[lz][ai][bl]hstack=3[o]")
        outp = out_dir / f"{tag}.png"
        _run([ffmpeg, "-hide_banner", "-y", "-nostdin", "-loglevel", "error", "-i", str(a), "-i", str(b), "-filter_complex", fc,
              "-map", "[o]", "-frames:v", "1", str(outp)])
        if outp.exists():
            names.append(outp.name)
    shutil.rmtree(work, ignore_errors=True)
    return {"images": names, "seconds_per_frame": per, "legend": "da esquerda para a direita: Rápida | Avançada pura | mistura " + f"{int(op * 100)}%"}
