"""Upscaling com IA offline (Real-ESRGAN ncnn Vulkan) — opcional, gratuito e portátil.

O programa oficial é um .exe único (~6 MB + modelos) que roda em qualquer placa com Vulkan (Intel, AMD, Nvidia), sem instalar nada
e sem ser administrador. Aqui só localizamos o .exe, medimos a velocidade da sua placa e processamos pastas de quadros.

Se o .exe não estiver na pasta bin, o programa cai automaticamente no modo "Rápido FFmpeg" e mostra de onde baixar.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

DOWNLOAD_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
DOWNLOAD_PAGE = "https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0"
HOW_TO = (
    "A ampliação avançada não está instalada nesta cópia do Pascal. Enquanto isso o Pascal usa o modo Rápido, que já dá um bom resultado. "
    f"(Detalhe técnico para quem monta a pasta: {DOWNLOAD_URL} -> conteúdo em bin\\realesrgan\\.)"
)

# modelos que vêm no zip oficial -> (nome do -n, escalas nativas disponíveis, descrição)
MODEL_INFO = {
    "realesr-animevideov3": ("rápido; feito para vídeo/anime — tende a alisar a pele (use o blend)", (2, 3, 4)),
    "realesrgan-x4plus": ("foto real; mais natural e MUITO mais lento", (4,)),
    "realesrgan-x4plus-anime": ("ilustração; não indicado para rosto", (4,)),
}


def find_exe(base: Path) -> Path | None:
    """Procura realesrgan-ncnn-vulkan.exe em ./bin (inclusive subpastas)."""
    names = ("realesrgan-ncnn-vulkan.exe", "realesrgan-ncnn-vulkan")
    bin_dir = base / "bin"
    if not bin_dir.is_dir():
        return None
    for n in names:
        p = bin_dir / n
        if p.is_file():
            return p
    for n in names:
        hit = next((p for p in bin_dir.rglob(n)), None)
        if hit:
            return hit
    return None


def list_models(exe: Path) -> list[str]:
    mdir = exe.parent / "models"
    if not mdir.is_dir():
        return []
    found = {re.sub(r"-x\d$", "", p.stem) for p in mdir.glob("*.param")}
    return sorted(found)


def native_scale(model: str, wanted: int) -> int:
    """Escala que o modelo suporta (o -s do exe só aceita as escalas treinadas)."""
    opts = MODEL_INFO.get(model, ("", (4,)))[1]
    return wanted if wanted in opts else max(opts)


def _run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)


def gpu_name(exe: Path) -> str:
    """Pergunta ao próprio .exe qual placa Vulkan ele vai usar."""
    try:
        cp = _run([str(exe), "-i", "nao_existe.png", "-o", "x.png", "-v"], 30)
        txt = (cp.stdout + cp.stderr).decode("utf-8", "replace")
        m = re.search(r"\[0 ([^\]]+)\]", txt)
        return m.group(1) if m else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def process_folder(exe: Path, in_dir: Path, out_dir: Path, model: str, scale: int, on_line=None, holder: dict | None = None,
                   threads: str = "1:2:2") -> tuple[int, str]:
    """Roda a IA numa pasta de PNGs. Devolve (código, últimas linhas). on_line(percent_do_lote) é chamado conforme o exe avisa."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(exe.resolve()), "-i", str(in_dir.resolve()), "-o", str(out_dir.resolve()), "-n", model, "-s", str(scale), "-f", "png", "-j", threads]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(exe.parent), creationflags=CREATE_NO_WINDOW)
    if holder is not None:
        holder["proc"] = proc
    tail: list[str] = []
    n_in = len(list(in_dir.glob("*.png")))
    done = 0
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.decode("utf-8", "replace").strip()
        if not line:
            continue
        tail.append(line)
        tail = tail[-12:]
        if "done" in line.lower():
            done += 1
            if on_line and n_in:
                on_line(100.0 * done / n_in)
    code = proc.wait()
    return code, "\n".join(tail)


def benchmark(exe: Path, model: str, scale: int, sample_png: Path, workdir: Path, cache_file: Path | None = None) -> float:
    """Segundos por quadro de 1080p nesta máquina (2 quadros: o primeiro paga a compilação dos shaders e é descartado)."""
    key = f"{model}-x{scale}-{sample_png.stat().st_size // 4096}"
    if cache_file and cache_file.is_file():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if key in data:
                return float(data[key])
        except (OSError, ValueError):
            pass
    ind, outd = workdir / "bench_in", workdir / "bench_out"
    for d in (ind, outd):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
    for i in (1, 2):
        shutil.copyfile(sample_png, ind / f"b{i}.png")
    t0 = time.time()
    code, _ = process_folder(exe, ind, outd, model, scale)
    total = time.time() - t0
    shutil.rmtree(ind, ignore_errors=True)
    shutil.rmtree(outd, ignore_errors=True)
    if code != 0:
        return -1.0
    per = total / 2.0 * 0.9    # desconta um pouco a partida (um lote grande dilui o custo fixo)
    if cache_file:
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.is_file() else {}
            data[key] = per
            cache_file.write_text(json.dumps(data), encoding="utf-8")
        except (OSError, ValueError):
            pass
    return per


def fmt_eta(seconds: float) -> str:
    if seconds < 90:
        return f"{seconds:.0f} s"
    if seconds < 5400:
        return f"{seconds / 60:.0f} min"
    return f"{seconds / 3600:.1f} h"
