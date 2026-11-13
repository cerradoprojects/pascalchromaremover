"""Recorte por IA offline (Robust Video Matting) — etapa 0 do render. Roda matte_worker.py num Python que tenha numpy + onnxruntime.

Saída: dois arquivos temporários (cor do sujeito já sem verde + transparência) que o pipeline.py usa no lugar do chroma key.
Sem o modelo (bin/rvm/*.onnx) ou sem esses pacotes, o programa cai sozinho para o recorte clássico por chroma key."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pipeline as P

MODEL_NAME = "rvm_resnet50_fp32.onnx"
MODEL_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/" + MODEL_NAME
HOW_TO = (f"Detalhe técnico (só para quem monta a pasta): baixe {MODEL_URL} para bin\\rvm\\ ; o Python precisa de numpy e onnxruntime (python\\Lib\\site-packages).")

_PY_CACHE: dict[str, str | None] = {}
_PY_ERR = {"msg": ""}          # última linha do erro ao importar numpy/onnxruntime (para dizer o motivo na tela)


def last_error() -> str:
    return _PY_ERR["msg"]


def variant_of(s: dict) -> str:
    """Estilo da borda do cabelo -> variante do matte_worker (E = simples, D = por partes do corpo)."""
    return "D" if s.get("matte_style") == "partes" else "E"


def find_model(base: Path) -> Path | None:
    for p in (base / "bin" / "rvm" / MODEL_NAME, base / "bin" / MODEL_NAME):
        if p.exists():
            return p
    return None


def find_python(base: Path) -> str | None:
    """Primeiro Python que consegue importar numpy e onnxruntime (o portátil, o que roda o programa, o do sistema)."""
    if "py" in _PY_CACHE:
        return _PY_CACHE["py"]
    portable = str(base / "python" / "python.exe")
    cands = [portable, sys.executable, shutil.which("python") or "", shutil.which("py") or ""]
    found = None
    timed_out = False
    first_err = ""
    tried: set[str] = set()
    for c in cands:
        try:
            key = c.lower().replace("/", "\\")
            if not c or key in tried or "\\windowsapps\\" in key or not Path(c).exists():      # atalho da Microsoft Store (só abre a loja) não serve
                continue
            tried.add(key)
            cmd = [c, "-3"] if Path(c).stem.lower() == "py" else [c]
            # o Python do Pascal: tempo folgado (na 1ª vez o antivírus pode examinar os pacotes por vários segundos); os de fora: pouco
            r = subprocess.run(cmd + ["-c", "import numpy, onnxruntime"], capture_output=True, text=True, errors="replace",
                               timeout=240 if c == portable else 30, creationflags=P.CREATE_NO_WINDOW)
        except subprocess.TimeoutExpired:
            timed_out = True
            continue
        except (OSError, ValueError):
            continue
        if r.returncode == 0:
            found = " ".join(cmd)
            break
        if not first_err:
            first_err = (r.stderr.strip().splitlines() or [""])[-1][:200]
    _PY_ERR["msg"] = "" if found else first_err
    if found or not timed_out:          # demora não é resposta: não guarda "não achei" e tenta de novo no próximo quadro
        _PY_CACHE["py"] = found
    return found


def available(base: Path) -> tuple[bool, str]:
    if find_model(base) is None:
        return False, "modelo do RVM ausente em bin\\rvm. " + HOW_TO
    if find_python(base) is None:
        return False, "nenhum Python com numpy + onnxruntime encontrado" + (f" ({last_error()})" if last_error() else "") + ". " + HOW_TO
    return True, ""


def generate(ffmpeg: str, base: Path, src: str, s: dict, info: dict, start: float, length: float, work: Path,
             on_progress=None, holder: dict | None = None, cancelled=lambda: False, note=lambda m: None) -> tuple[bool, str, dict | None]:
    """Gera cor+transparência do trecho [start, start+length] (length=0: até o fim). Devolve (ok, mensagem, {"color","alpha","start"})."""
    ok, why = available(base)
    if not ok:
        return False, why, None
    py = find_python(base)
    model = find_model(base)
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    out_c, out_a = work / "cor.mkv", work / "alfa.mkv"
    tw, th = P.target_size(info, s, False)    # o recorte já sai em 1080p (vertical ou horizontal)
    dur = length if length > 0 else max(0.1, (info["duration"] or 1.0) - start)
    total = max(1, int(round(dur * info["fps"])))
    cmd = py.split() + [str(Path(__file__).with_name("matte_worker.py")), "--ffmpeg", ffmpeg, "--src", src, "--start", f"{start:.3f}",
                        "--length", f"{length:.3f}", "--width", str(tw), "--height", str(th), "--fps", info["fps_str"],
                        "--model", str(model), "--out-color", str(out_c), "--out-alpha", str(out_a),
                        "--mix", f"{float(s.get('matte_mix', 0.3)):.3f}", "--spill", f"{float(s.get('matte_spill', 1.0)):.3f}",
                        "--variant", variant_of(s), "--tag", info.get("color_space", "")]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", creationflags=P.CREATE_NO_WINDOW)
    if holder is not None:
        holder["proc"] = proc
    tail: list[str] = []
    for line in proc.stdout:
        line = line.strip()
        if line.startswith("PROG ") and on_progress:
            try:
                on_progress(min(100.0, 100.0 * int(line.split()[1]) / total))
            except ValueError:
                pass
        elif line:
            tail.append(line)
            tail = tail[-12:]
        if cancelled():
            proc.kill()
            return False, "cancelado", None
    proc.wait()
    if proc.returncode != 0 or not out_c.exists() or not out_a.exists():
        return False, "O recorte avançado falhou: " + error_tail("\n".join(tail)), None
    return True, "", {"color": str(out_c), "alpha": str(out_a), "start": start, "w": tw, "h": th}


def error_tail(text: str) -> str:
    """O erro de verdade do worker: a última linha de erro do Python (as últimas linhas costumam ser só o FFmpeg se despedindo)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    errs = [ln for ln in lines if not ln.startswith("[") and re.search(r"(Error|Exception|Traceback|INVALID|[Ff]ail)", ln)]
    return " | ".join(errs[-2:] or lines[-4:])[:400]


def _run_worker(args: list[str], what: str) -> tuple[bool, str]:
    py = find_python(Path(__file__).parent)
    cmd = py.split() + [str(Path(__file__).with_name("matte_worker.py"))] + args
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", creationflags=P.CREATE_NO_WINDOW)
    if r.returncode != 0:
        return False, f"{what} falhou: {error_tail(r.stdout + chr(10) + r.stderr)}"
    return True, ""


def generate_raw(ffmpeg: str, base: Path, src: str, s: dict, info: dict, start: float, work: Path) -> tuple[bool, str, str | None]:
    """Quadro ao vivo, etapa lenta: roda o modelo UMA vez no quadro e guarda o resultado bruto (raw.npz). Devolve (ok, mensagem, caminho)."""
    ok, why = available(base)
    if not ok:
        return False, why, None
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    tw, th = P.target_size(info, s, False)
    raw = work / "raw.npz"
    ok, msg = _run_worker(["--ffmpeg", ffmpeg, "--src", src, "--start", f"{start:.3f}", "--length", f"{1.0 / max(1.0, info['fps']):.4f}",
                           "--width", str(tw), "--height", str(th), "--fps", info["fps_str"], "--model", str(find_model(base)),
                           "--dump-raw", str(raw), "--tag", info.get("color_space", "")], "O recorte avançado do quadro")
    return (True, "", str(raw)) if ok and raw.exists() else (False, msg or "O recorte avançado do quadro não gerou resultado.", None)


def post_raw(ffmpeg: str, raw: str, s: dict, info: dict, work: Path) -> tuple[bool, str, dict | None]:
    """Quadro ao vivo, etapa rápida (~1,5 s): refaz só a borda (mistura de cor, tira-verde) a partir do resultado bruto do modelo."""
    tw, th = P.target_size(info, s, False)
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    out_c, out_a = work / "cor.mkv", work / "alfa.mkv"
    ok, msg = _run_worker(["--ffmpeg", ffmpeg, "--post-raw", raw, "--width", str(tw), "--height", str(th), "--fps", info["fps_str"],
                           "--out-color", str(out_c), "--out-alpha", str(out_a),
                           "--mix", f"{float(s.get('matte_mix', 0.3)):.3f}", "--spill", f"{float(s.get('matte_spill', 1.0)):.3f}",
                           "--variant", variant_of(s)], "A borda do quadro")
    if not ok or not out_c.exists() or not out_a.exists():
        return False, msg or "A borda do quadro não gerou resultado.", None
    return True, "", {"color": str(out_c), "alpha": str(out_a), "start": 0.0, "w": tw, "h": th}
