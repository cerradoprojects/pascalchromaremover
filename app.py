"""Pascal — servidor local + interface no navegador.

Roda de qualquer pasta (ou pendrive), sem instalar nada e sem ser administrador:
  * usa só a biblioteca padrão do Python;
  * procura ffmpeg.exe e ffprobe.exe dentro de ./bin;
  * abre a interface no Chrome (ou Edge) em modo aplicativo.
Toda a parte de filtros do FFmpeg está em pipeline.py.
"""
from __future__ import annotations

import ctypes
import json
import mimetypes
import os
import re
import secrets
import subprocess
import sys
import shutil
import threading
import time
import traceback
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

if os.name == "nt":
    try:    # programa que não consegue abrir (falta uma DLL, por exemplo) não mostra a janela de erro do Windows: o erro volta para o Pascal, que explica
        ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)       # FAILCRITICALERRORS | NOGPFAULTERRORBOX | NOOPENFILEERRORBOX (os programas filhos herdam)
    except (AttributeError, OSError):
        pass

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import pipeline as P  # noqa: E402
import diag as D  # noqa: E402
import upscale_ai as UA  # noqa: E402
import ai_render as AR  # noqa: E402
import matte_ai as MA  # noqa: E402
import keepawake as KA  # noqa: E402
import selfcheck as SC  # noqa: E402

WEB = BASE / "web"
CACHE = BASE / "cache"
OUTPUT = BASE / "output"
INPUT = BASE / "input"
USER_PRESETS = BASE / "presets_usuario"
LOGS = BASE / "logs"
for _d in (CACHE, OUTPUT, INPUT, USER_PRESETS, LOGS):
    _d.mkdir(exist_ok=True)

CONFIG_FILE = BASE / "pascal_config.json"
TOKEN = secrets.token_urlsafe(16)
FFMPEG, FFPROBE = P.find_binaries(BASE)

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
LAST_PING = {"t": 0.0, "seen": False, "bye": 0.0}
LAST_VIDEO = {"path": ""}
PORT = 0

# Tipos de arquivo fixos: o Python no Windows lê o tipo do registro, e em alguns computadores .js/.css vêm como text/plain (a tela não carrega).
MIME = {".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8", ".png": "image/png",
        ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".json": "application/json", ".md": "text/markdown; charset=utf-8",
        ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}


def mime_of(name: str) -> str:
    return MIME.get(Path(name).suffix.lower()) or mimetypes.guess_type(name)[0] or "application/octet-stream"


def console(msg: str) -> None:
    """print() que não derruba o programa se a janela preta não aceitar algum acento."""
    try:
        print(msg, flush=True)
    except (UnicodeEncodeError, OSError):
        try:
            print(msg.encode("ascii", "replace").decode("ascii"), flush=True)
        except OSError:
            pass


# verificação da instalação (Ajuda > Verificar instalação): roda uma vez ao abrir, em segundo plano
SELF: dict = {"result": None, "running": False, "stage": ""}
SELF_LOCK = threading.Lock()


def start_selfcheck(fresh: bool = False) -> None:
    with SELF_LOCK:
        if SELF["running"] or (SELF["result"] is not None and not fresh):
            return
        SELF["running"] = True
        if fresh:
            SELF["result"] = None

    def work() -> None:
        try:
            MA._PY_CACHE.clear()                  # refaz também a busca do Python usada pelo quadro e pelo render
            SELF["stage"] = "Testando se tudo que o Pascal precisa está disponível neste computador…"
            res = SC.run(BASE, FFMPEG, FFPROBE, current_out_dir(), find_browser())
            if not res["matte"]["ok"] and res["matte"]["kind"] not in ("model", "timeout"):
                # o recorte avançado não abriu: o Pascal tenta consertar sozinho antes de pedir qualquer coisa à pessoa
                try:
                    feitos = SC.auto_reparo(BASE, lambda m: SELF.update(stage=m))
                except Exception:  # noqa: BLE001
                    log(traceback.format_exc())
                    feitos = []
                SELF["stage"] = "Conferindo de novo…"
                res = SC.run(BASE, FFMPEG, FFPROBE, current_out_dir(), find_browser())
                res["matte"]["repair"] = feitos
            SELF["result"] = res
            try:
                (CACHE / "diagnostico.txt").write_text(SC.report_text(res, "pt") + "\n\n" + SC.report_text(res, "en") + "\n", encoding="utf-8")
            except OSError:
                pass
            c = res["counts"]
            console(f"Verificação da instalação: {c['ok']} ok, {c['warn']} atenção, {c['fail']} problema(s). Detalhes: Ajuda > Verificar instalação (ou cache\\diagnostico.txt).")
            for i in res["items"]:
                if i["level"] != "ok":
                    console(f"  - {i['pt']['title']}: {i['pt']['detail']}")
            log("VERIFICAÇÃO\n" + SC.report_text(res, "pt"))
        except Exception:  # noqa: BLE001
            log(traceback.format_exc())
        finally:
            SELF["running"] = False

    threading.Thread(target=work, daemon=True).start()


GPU = {"name": None, "busy": False}      # nome da placa Vulkan: descoberto em segundo plano (rodar o .exe pode demorar ou travar em PCs sem driver)


def log(msg: str) -> None:
    try:
        with open(CACHE / "app.log", "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def load_default_preset() -> dict:
    try:
        data = json.loads((BASE / "presets.json").read_text(encoding="utf-8"))
        return P.clean_settings(data["estudio_quente"]["settings"])
    except (OSError, KeyError, ValueError):
        return P.clean_settings({})


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(**kw) -> None:
    cfg = load_config()
    cfg.update(kw)
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _writable_dir(p: Path) -> bool:
    try:
        p.mkdir(parents=True, exist_ok=True)
        t = p / ".pascal_teste"
        t.write_text("x")
        t.unlink()
        return True
    except OSError:
        return False


def current_out_dir(video: str | None = None) -> Path:
    """Pasta onde os vídeos prontos são gravados: a escolhida pelo usuário; se não escolheu,
    a mesma pasta do vídeo original; se ela não aceitar gravação, ./output."""
    d = load_config().get("out_dir", "")
    if d and _writable_dir(Path(d)):
        return Path(d)
    v = video or LAST_VIDEO["path"]
    if v and Path(v).parent.is_dir() and _writable_dir(Path(v).parent):
        return Path(v).parent
    return OUTPUT


def save_sample(out: Path, video: str, dest: Path) -> Path | None:
    """Copia o teste de 5 s (MP4 com fundo de estúdio) para a pasta de destino como <nome>_sample.mp4, para ver em outro player."""
    stem = Path(video).stem
    ext = out.suffix or ".mp4"
    for n in range(1, 50):
        target = dest / (f"{stem}_sample{ext}" if n == 1 else f"{stem}_sample_{n}{ext}")
        try:
            shutil.copyfile(out, target)
            return target
        except OSError:
            continue
    return None


def _ps_dialog(script: str) -> str:
    """Roda um script do PowerShell que abre uma janela do Windows e devolve o que ele escreveu. Se o Windows não abrir a janela, explica por quê."""
    try:
        cp = subprocess.run([SC.ps_exe(), "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script],
                            capture_output=True, creationflags=P.CREATE_NO_WINDOW, timeout=600)
    except FileNotFoundError:
        raise RuntimeError("O PowerShell não está disponível neste computador.") from None
    out = cp.stdout.decode("utf-8", "replace").strip()
    if cp.returncode != 0 and not out:
        err = [ln.strip() for ln in cp.stderr.decode("utf-8", "replace").splitlines() if ln.strip()]
        raise RuntimeError("O Windows não abriu a janela de escolha" + (": " + err[0][:140] if err else f" (código {cp.returncode})") + ".")
    return out


# O dono invisível "sempre na frente" faz a janela de escolha aparecer na frente do Pascal (sem ele, em alguns computadores ela abre escondida atrás).
_PS_OWNER = "$o=New-Object System.Windows.Forms.Form -Property @{TopMost=$true;ShowInTaskbar=$false};"


def folder_dialog_script(start: str) -> str:
    start = start.replace("'", "''")
    return (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        "Add-Type -AssemblyName System.Windows.Forms;" + _PS_OWNER +
        "$d=New-Object System.Windows.Forms.FolderBrowserDialog;"
        "$d.Description='Escolha a pasta onde o Pascal vai salvar os videos prontos';"
        "$d.ShowNewFolderButton=$true;"
        f"$d.SelectedPath='{start}';"
        "if($d.ShowDialog($o) -eq 'OK'){Write-Output $d.SelectedPath}"
    )


def pick_folder_dialog(start: str) -> str:
    """Abre a janela do Windows para escolher uma pasta."""
    return _ps_dialog(folder_dialog_script(start))


def safe_name(name: str) -> str:
    name = re.sub(r"[^\w\- ]", "", name, flags=re.UNICODE).strip()[:60]
    return name or "meu_preset"


def file_dialog_script() -> str:
    return (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        "Add-Type -AssemblyName System.Windows.Forms;" + _PS_OWNER +
        "$d=New-Object System.Windows.Forms.OpenFileDialog;"
        "$d.Title='Escolha o video bruto';"
        "$d.Filter='Videos|*.mp4;*.mov;*.mkv;*.avi;*.webm;*.m4v;*.mxf;*.mts|Todos os arquivos|*.*';"
        f"$d.InitialDirectory='{str(INPUT).replace(chr(39), chr(39) * 2)}';"
        "if($d.ShowDialog($o) -eq 'OK'){Write-Output $d.FileName}"
    )


def pick_file_dialog() -> str:
    """Abre a janela do Windows para escolher o vídeo (via PowerShell, que já vem no Windows)."""
    return _ps_dialog(file_dialog_script())


# ---------------------------------------------------------------- trabalhos
def new_job(kind: str) -> dict:
    job = {"id": secrets.token_hex(4), "kind": kind, "state": "running", "progress": 0.0, "speed": "",
           "message": "Preparando…", "out": "", "out_name": "", "error": "", "started": time.time(), "proc": {}}
    with JOBS_LOCK:
        JOBS[job["id"]] = job
    return job


def any_running() -> bool:
    with JOBS_LOCK:
        return any(j["state"] == "running" for j in JOBS.values())


def run_job(job: dict, cmd: list[str], total: float, out_path: Path, jl: D.JobLog | None = None, post=None) -> None:
    def on_prog(pct: float, speed: str, done: float) -> None:
        base = float(job.get("pbase", 0.0))
        pct = base + pct * (100.0 - base) / 100.0
        job["progress"] = pct
        job["speed"] = speed
        elapsed = time.time() - job["started"]
        if pct > 2:
            job["message"] = f"Processando… faltam cerca de {fmt_secs(elapsed * (100 - pct) / pct)}"
        else:
            job["message"] = "Processando…"

    try:
        log("CMD " + " ".join(cmd))
        code, tail = P.run_ffmpeg(cmd, total, on_prog, job["proc"], (jl.dir / "ffmpeg.log") if jl else None)
        if job.get("cancel"):
            job["state"], job["message"] = "cancelled", "Cancelado."
            try:
                out_path.unlink(missing_ok=True)
            except OSError:
                pass
        elif code == 0 and out_path.exists():
            if post:
                job["message"] = "Analisando o resultado…"
                job["progress"] = 99.0
                try:
                    post()
                except Exception as e:  # noqa: BLE001
                    log("ERRO diagnóstico: " + traceback.format_exc())
                    if jl:
                        jl.alert(f"O diagnóstico automático falhou: {e}")
            job.update(state="done", progress=100.0, message="Pronto!", out=str(out_path), out_name=out_path.name)
            if jl:
                job["log_dir"] = str(jl.dir)
                job["alerts"] = jl.alerts
        else:
            job.update(state="error", error=tail or f"ffmpeg terminou com código {code}", message="Falhou.")
            log("ERRO " + job["error"])
            if jl:
                jl.alert("O FFmpeg falhou: " + (tail.splitlines()[-1] if tail else f"código {code}"))
                jl.finish("FALHOU")
                job["log_dir"] = str(jl.dir)
                job["alerts"] = jl.alerts
    except Exception as e:  # noqa: BLE001
        job.update(state="error", error=str(e), message="Falhou.")
        log(traceback.format_exc())


def fmt_secs(x: float) -> str:
    x = int(x)
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{h}h{m:02d}min" if h else (f"{m}min{s:02d}s" if m else f"{s}s")


def _prepare_log(kind: str, job: dict, path: str, s: dict, cmd: list[str], diag: dict) -> D.JobLog:
    jl = D.JobLog(LOGS, kind, job["id"])
    final = {k: v for k, v in (diag.get("settings") or s).items()}
    jl.json("ajustes.json", final)
    jl.text("comando.txt", "\n".join(cmd))
    fc = diag.get("filter_complex", "")
    vparts = [x for x in fc.split(";") if "[aout]" not in x and "aformat=sample_rates" not in x and "concat=n=2:v=0:a=1" not in x]
    jl.text("filtro_video.txt", ";\n".join(vparts))
    jl.text("filtro_audio.txt", ";\n".join(x for x in fc.split(";") if x not in vparts))
    jl.note(f"ORIGEM: {path}")
    return jl


def use_matte(s: dict) -> tuple[bool, str]:
    """Recorte avançado (RVM)? Se faltar o modelo/pacotes, volta sozinho ao chroma key e devolve o motivo."""
    if not (s["mod_chroma"] and s["matte_engine"] == "rvm"):
        return False, ""
    try:
        ok, why = MA.available(BASE)
    except Exception as e:  # noqa: BLE001      # nada na procura do Python pode derrubar o quadro: sem o recorte avançado, o clássico assume
        ok, why = False, f"erro ao verificar o recorte avançado ({str(e)[:160]})"
    if not ok:
        log("Recorte avançado indisponível: " + why)
    short = why.split(". Detalhe")[0].strip()
    return ok, ("" if ok else "O recorte avançado não está disponível neste computador; usei o recorte clássico (mais rápido, menos natural no cabelo). Motivo: " + short)


def run_matte_stage(job: dict, path: str, s: dict, info: dict, start: float, length: float):
    """Etapa 0: RVM grava cor+transparência do trecho. Devolve (matte, work_dir); matte=None se falhar ou cancelar."""
    work = CACHE / ("matte_" + job["id"])
    job["message"] = "Recortando a pessoa (recorte avançado)… leva alguns minutos por minuto de vídeo"

    def on_p(pct: float) -> None:
        job["progress"] = pct * 0.6
        job["pbase"] = 60.0

    ok, msg, matte = MA.generate(FFMPEG, BASE, path, s, info, start, length, work, on_p, job["proc"], lambda: bool(job.get("cancel")), log)
    if job.get("cancel"):
        job.update(state="cancelled", message="Cancelado.")
        return None, work
    if not ok:
        job.update(state="error", error=msg, message="Falhou.")
        return None, work
    job["message"] = "Aplicando cor, luz e fundo…"
    return matte, work


def start_preview(path: str, raw: dict) -> dict:
    s = P.clean_settings(raw)
    LAST_VIDEO["path"] = path
    info = P.probe(FFPROBE, path)
    length = min(s["preview_len"], max(1.0, info["duration"] or s["preview_len"]))
    start = s["preview_start"]
    if info["duration"] and start + length > info["duration"]:
        start = max(0.0, info["duration"] - length)
    for old in list(CACHE.glob("preview_*.mp4")) + list(CACHE.glob("preview_*.webm")) + list(CACHE.glob("orig_*.mp4")):
        try:
            old.unlink()
        except OSError:
            pass
    job = new_job("preview")
    job["message"] = "Medindo o vídeo (verde, luz, ruído de sala)…"
    alpha_prev = bool(P.output_kind(s) in ("prores", "qtrle") and s["mod_chroma"])     # fundo transparente: teste com alfa (WebM)
    job["alpha"] = alpha_prev
    out = CACHE / f"preview_{job['id']}.{'webm' if alpha_prev else 'mp4'}"
    matte_on, matte_why = use_matte(s)
    if matte_why:
        log(matte_why)

    def work() -> None:
        work_dir = None
        try:
            matte = None
            if matte_on:
                matte, work_dir = run_matte_stage(job, path, s, info, start, length)
                if matte is None:
                    return
            diag: dict = {}
            t0 = time.time()
            cmd = P.build_command(FFMPEG, path, s, info, str(out), preview=True, start=start, length=length, diag=diag, matte=matte)
            prep = time.time() - t0
            jl = _prepare_log("preview", job, path, s, cmd, diag)
            jl.note(f"PREVIEW: início {start:.1f}s, duração {length:.1f}s; preparação (medições) levou {prep:.1f}s")
            jl.note("RECORTE: " + ("avançado (cabelo fio a fio) + tira-verde" if matte else "clássico"))
            if matte_why:
                jl.alert(matte_why)

            def post() -> None:
                # Fundo transparente: o teste (WebM com alfa) só serve para ver aqui na tela, com a cor de fundo escolhida.
                # Fora do Pascal um player comum mostra o verde original por trás, então não vira arquivo na pasta de destino.
                if alpha_prev:
                    jl.note("AMOSTRA: teste com fundo transparente fica só na tela do Pascal (não é salvo na pasta de destino).")
                else:
                    job["message"] = "Salvando a amostra na pasta de destino…"
                    samp = save_sample(out, path, current_out_dir(path))
                    if samp:
                        job["sample"] = str(samp)
                        jl.note(f"AMOSTRA de 5 s salva em: {samp}")
                    else:
                        jl.alert("Não consegui salvar a amostra na pasta de destino (a pasta não aceita gravação).")
                job["message"] = "Gerando o original para comparar…"
                orig = CACHE / f"orig_{job['id']}.mp4"
                D._run([FFMPEG, "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", path, "-map", "0:v:0", "-map", "0:a:0?",
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(orig)], 300)
                if orig.exists():
                    job["orig_name"] = orig.name
                job["message"] = "Analisando o áudio…"
                D.analyze_audio(jl, FFMPEG, path, str(out), start, length, info["has_audio"], s["a_lufs"] if s["a_loudnorm"] and s["mod_audio"] else None)
                job["message"] = "Gravando quadros de comparação…"
                D.grab_frames(jl, FFMPEG, path, str(out), start, length)
                D.video_sanity(jl, FFPROBE, str(out), length, (info["width"], info["height"]), s["mod_upscale"])
                D._NOISE_WARN.clear()
                for line in D.describe_settings(diag.get("settings", s)):
                    jl.note(line)
                for w in D._NOISE_WARN:
                    jl.alert(w)
                txt = jl.finish(f"RELATÓRIO DO PREVIEW — {Path(path).name} ({time.strftime('%d/%m/%Y %H:%M:%S')})")
                log("RESUMO\n" + txt)

            job["log_dir"] = str(jl.dir)
            run_job(job, cmd, length, out, jl, post)
        except Exception as e:  # noqa: BLE001
            log(traceback.format_exc())
            job.update(state="error", error=str(e), message="Falhou.")
        finally:
            if work_dir:
                shutil.rmtree(work_dir, ignore_errors=True)

    threading.Thread(target=work, daemon=True).start()
    return job


def ai_info() -> dict:
    exe = UA.find_exe(BASE)
    howto = UA.HOW_TO
    if exe is None and not UA.vulkan_ok() and any((BASE / "bin").rglob("realesrgan-ncnn-vulkan.exe")):
        howto = "Este computador não tem o driver de vídeo com Vulkan (o arquivo vulkan-1.dll); a ampliação avançada não funciona aqui. O modo Rápido funciona normalmente."
    if exe and GPU["name"] is None and not GPU["busy"]:       # nunca bloqueia a tela: a 1ª resposta vem sem o nome da placa
        GPU["busy"] = True

        def probe() -> None:
            try:
                GPU["name"] = UA.gpu_name(exe)
            finally:
                GPU["busy"] = False

        threading.Thread(target=probe, daemon=True).start()
    return {"available": bool(exe), "models": UA.list_models(exe) if exe else [], "howto": howto, "url": UA.DOWNLOAD_URL,
            "gpu": GPU["name"] or "", "model_info": {k: v[0] for k, v in UA.MODEL_INFO.items()}}


def ai_sec_per_frame(path: str, s: dict) -> float:
    """Segundos por quadro de 1080p nesta placa (mede uma vez e guarda em cache/ai_bench.json)."""
    exe = UA.find_exe(BASE)
    if not exe:
        return -1.0
    sample = CACHE / "ai_bench_frame.png"
    if not sample.exists():
        D._run([FFMPEG, "-v", "error", "-y", "-ss", "10", "-i", path, "-frames:v", "1", str(sample)], 120)
    return UA.benchmark(exe, s["ai_model"], UA.native_scale(s["ai_model"], 2), sample, CACHE / "ai_bench", CACHE / "ai_bench.json")


def start_ai_test(path: str, raw: dict) -> dict:
    s = P.clean_settings(raw)
    info = P.probe(FFPROBE, path)
    job = new_job("aitest")
    job["message"] = "Gerando 3 quadros com a ampliação avançada…"

    def work() -> None:
        try:
            dur = info["duration"] or 30.0
            start = min(s["preview_start"], max(0.0, dur - 2))
            times = [start, start + 1.0, start + 2.0]
            for old in CACHE.glob("ia_*.png"):
                old.unlink(missing_ok=True)
            res = AR.test_frames(FFMPEG, BASE, path, s, info, times, CACHE, CACHE / ("ai_test_" + job["id"]))
            if res.get("error"):
                job.update(state="error", error=res["error"], message="Falhou.")
            else:
                job.update(state="done", progress=100.0, message="Pronto!", images=res["images"], legend=res["legend"],
                           seconds_per_frame=res["seconds_per_frame"])
        except Exception as e:  # noqa: BLE001
            log(traceback.format_exc())
            job.update(state="error", error=str(e), message="Falhou.")

    threading.Thread(target=work, daemon=True).start()
    return job


def start_render_ai(path: str, raw: dict, out_dir: Path) -> dict:
    s = P.clean_settings(raw)
    info = P.probe(FFPROBE, path)
    out = P.unique_output(out_dir, path, "mp4")
    job = new_job("render")
    jl = D.JobLog(LOGS, "render-ia", job["id"])
    jl.json("ajustes.json", s)
    jl.note(f"RENDER COM AMPLIAÇÃO AVANÇADA (estilo {s['ai_model']}, mistura {int(s['ai_blend'] * 100)}%): {info['duration']:.0f}s -> {out.name}")
    job["log_dir"] = str(jl.dir)

    def on_prog(pct: float, msg: str) -> None:
        job["progress"] = pct
        job["message"] = msg

    def work() -> None:
        try:
            ok, msg = AR.render(FFMPEG, FFPROBE, BASE, path, s, info, str(out), CACHE / ("ai_work_" + job["id"]), on_prog, job["proc"],
                                lambda: bool(job.get("cancel")), jl.note)
            if job.get("cancel"):
                job.update(state="cancelled", message="Cancelado.")
                out.unlink(missing_ok=True)
            elif ok and out.exists():
                D.video_sanity(jl, FFPROBE, str(out), info["duration"], (info["width"], info["height"]), s["mod_upscale"])
                jl.finish("RELATÓRIO DO RENDER COM AMPLIAÇÃO AVANÇADA")
                job.update(state="done", progress=100.0, message="Pronto!", out=str(out), out_name=out.name, alerts=jl.alerts)
            else:
                jl.alert(msg)
                jl.finish("FALHOU")
                job.update(state="error", error=msg, message="Falhou.", alerts=jl.alerts)
        except Exception as e:  # noqa: BLE001
            log(traceback.format_exc())
            job.update(state="error", error=str(e), message="Falhou.")

    threading.Thread(target=work, daemon=True).start()
    return job


def start_render(path: str, raw: dict) -> dict:
    s = P.clean_settings(raw)
    LAST_VIDEO["path"] = path
    out_dir = current_out_dir(path)
    matte_on, matte_why = use_matte(s)
    if matte_why:
        log(matte_why)
    if matte_on and s["upscale_engine"] == "realesrgan":
        log("Recorte avançado + ampliação avançada ainda não combinam: usando o motor Rápido FFmpeg no upscaling.")
    if s["upscale_engine"] == "realesrgan" and s["mod_upscale"] and P.output_kind(s) == "mp4" and not matte_on:
        if UA.find_exe(BASE):
            return start_render_ai(path, raw, out_dir)
        log("Ampliação avançada pedida mas não instalada em bin: usando o motor Rápido FFmpeg. " + UA.HOW_TO)
    info = P.probe(FFPROBE, path)
    kind = P.output_kind(s)
    out = P.unique_output(out_dir, path, kind)
    job = new_job("render")
    job["message"] = "Medindo o vídeo (verde, luz, ruído de sala)…"

    def work() -> None:
        work_dir = None
        try:
            matte = None
            if matte_on:
                matte, work_dir = run_matte_stage(job, path, s, info, 0.0, 0.0)
                if matte is None:
                    return
            diag: dict = {}
            cmd = P.build_command(FFMPEG, path, s, info, str(out), preview=False, diag=diag, matte=matte)
            jl = _prepare_log("render", job, path, s, cmd, diag)
            jl.note(f"RENDER COMPLETO: {info['duration']:.0f}s de vídeo -> {out.name}")
            jl.note("RECORTE: " + ("avançado (cabelo fio a fio) + tira-verde" if matte else "clássico"))
            if matte_why:
                jl.alert(matte_why)

            def post() -> None:
                D.video_sanity(jl, FFPROBE, str(out), info["duration"], (info["width"], info["height"]), s["mod_upscale"])
                sample = min(45.0, info["duration"])
                D.analyze_audio(jl, FFMPEG, path, str(out), 0.0, sample, info["has_audio"], s["a_lufs"] if s["a_loudnorm"] and s["mod_audio"] else None)
                D.grab_frames(jl, FFMPEG, path, str(out), 0.0, info["duration"])
                D._NOISE_WARN.clear()
                for line in D.describe_settings(diag.get("settings", s)):
                    jl.note(line)
                for w in D._NOISE_WARN:
                    jl.alert(w)
                jl.note(f"TAMANHO: {out.stat().st_size / 1e6:.0f} MB")
                txt = jl.finish(f"RELATÓRIO DO RENDER — {Path(path).name} ({time.strftime('%d/%m/%Y %H:%M:%S')})")
                log("RESUMO\n" + txt)

            job["log_dir"] = str(jl.dir)
            run_job(job, cmd, info["duration"], out, jl, post)
        except Exception as e:  # noqa: BLE001
            log(traceback.format_exc())
            job.update(state="error", error=str(e), message="Falhou.")
        finally:
            if work_dir:
                shutil.rmtree(work_dir, ignore_errors=True)

    threading.Thread(target=work, daemon=True).start()
    return job


# ---------------------------------------------------------------- quadro ao vivo
FRAMES: dict[str, dict] = {}
FRAME_LOCK = threading.Lock()
FRAME_LATEST = {"seq": 0}
RAW_CACHE: dict[tuple, str] = {}         # resultado bruto do modelo (raw.npz) por quadro: o ajuste da borda não roda o modelo de novo
MATTE_CACHE: dict[tuple, dict] = {}      # recorte por IA de UM quadro (leva ~30 s; os outros ajustes redesenham em ~0,5 s)
SUBJ_CACHE: dict[tuple, dict] = {}
INFO_CACHE: dict[str, dict] = {}


def start_frame(path: str, at: float, raw: dict, orig: bool, seq: int) -> dict:
    """Gera um PNG de um quadro só, com todo o tratamento. Assíncrono: o recorte por IA do quadro leva alguns segundos na 1ª vez."""
    FRAME_LATEST["seq"] = seq
    job = {"id": secrets.token_hex(4), "state": "running", "message": "Preparando o quadro…", "out_name": "", "error": "", "seq": seq}
    FRAMES[job["id"]] = job
    if len(FRAMES) > 40:
        for k in list(FRAMES)[:20]:
            FRAMES.pop(k, None)

    def work() -> None:
        try:
            with FRAME_LOCK:
                if seq != FRAME_LATEST["seq"]:
                    job.update(state="stale", message="Substituído por um pedido mais novo.")
                    return
                s = P.clean_settings(raw)
                info = INFO_CACHE.get(path) or P.probe(FFPROBE, path)
                INFO_CACHE[path] = info
                at_c = max(0.0, min(at, max(0.0, (info["duration"] or 1.0) - 0.1)))
                for old in CACHE.glob("framo_*.png" if orig else "frame_*.png"):
                    try:
                        old.unlink()
                    except OSError:
                        pass
                out = CACHE / (f"framo_{job['id']}.png" if orig else f"frame_{job['id']}.png")
                tw, th = P.target_size(info, s, False)
                if orig:
                    cp = P._run([FFMPEG, "-v", "error", "-y", "-ss", f"{at_c:.3f}", "-i", path, "-frames:v", "1",
                                 "-vf", f"scale={tw}:{th}:flags=lanczos:in_range=auto:out_range=pc:in_color_matrix=auto,format=rgb24", str(out)], timeout=120)
                    if cp.returncode != 0 or not out.exists():
                        raise RuntimeError("Não consegui ler o quadro do vídeo.")
                else:
                    transparent = P.output_kind(s) != "mp4" and s["mod_chroma"]

                    def compose(matte_arg, dest: Path) -> None:
                        """Cor, luz e fundo sobre o recorte dado (matte_arg=None: recorte clássico por chroma key)."""
                        s2 = dict(s)
                        ck = (path, round(at_c, 2), s["chroma_color"])
                        sub = SUBJ_CACHE.get(ck)
                        if sub is None:
                            s2 = P.resolve_key_color(FFMPEG, path, s2, info, at_c)
                            sub = {"color": s2["chroma_color"], "subject": P.analyze_subject(FFMPEG, path, at_c, s2["chroma_color"] if s2["chroma_color"] != "auto" else "#95e591")}
                            SUBJ_CACHE[ck] = sub
                        s2["chroma_color"] = sub["color"]
                        s2["_subject"] = sub["subject"]
                        cmd, _ = P.build_still_command(FFMPEG, path, s2, info, str(dest), at_c, matte=matte_arg, ready=True)
                        cp = subprocess.run(cmd, capture_output=True, text=True, errors="replace", creationflags=P.CREATE_NO_WINDOW)
                        if cp.returncode != 0 or not dest.exists():
                            log("ERRO quadro: " + cp.stderr[-600:])
                            raise RuntimeError("O FFmpeg não conseguiu montar o quadro: " + (cp.stderr.strip().splitlines() or ["erro"])[-1])

                    matte = None
                    matte_on, why = use_matte(s)
                    job["matte_off"] = bool(why)        # a tela marca os ajustes "Recorte:" como sem efeito
                    if why:
                        job["warning"] = why
                    if matte_on:
                        rkey = (path, round(at_c, 2), tw, th)
                        key = rkey + (round(float(s["matte_mix"]), 2), round(float(s["matte_spill"]), 2), s["matte_style"])
                        matte = MATTE_CACHE.get(key)
                        if matte is None or not Path(matte["color"]).exists():
                            matte = None
                            quick = CACHE / f"frame_{job['id']}_q.png"
                            try:
                                # prévia rápida (recorte clássico, ~2 s): aparece na hora enquanto o recorte avançado trabalha (em PC lento leva minutos)
                                job["message"] = "Montando a prévia rápida…"
                                compose(None, quick)
                                job.update(quick=quick.name, transparent=transparent, width=tw, height=th, at=at_c)
                            except Exception as e:  # noqa: BLE001
                                log("prévia rápida falhou: " + str(e))
                            try:
                                # 1) o modelo roda UMA vez por quadro (~30 s); 2) a borda (mistura de cor, tira-verde) é refeita em ~1,5 s a cada ajuste
                                raw_npz = RAW_CACHE.get(rkey)
                                if raw_npz is None or not Path(raw_npz).exists():
                                    job["message"] = "Recortando este quadro… (cerca de 30 s; depois os ajustes são instantâneos)"
                                    ok, msg, raw_npz = MA.generate_raw(FFMPEG, BASE, path, s, info, at_c, CACHE / ("fr_" + secrets.token_hex(3)))
                                    if ok:
                                        RAW_CACHE[rkey] = raw_npz
                                        while len(RAW_CACHE) > 3:
                                            shutil.rmtree(Path(RAW_CACHE.pop(next(iter(RAW_CACHE)))).parent, ignore_errors=True)
                                else:
                                    ok, msg = True, ""
                                if ok:
                                    job["message"] = "Refazendo a borda do recorte…"
                                    ok, msg, matte = MA.post_raw(FFMPEG, raw_npz, s, info, Path(raw_npz).parent / ("post_" + secrets.token_hex(2)))
                                if not ok:        # plano B: o caminho antigo (um passo só, ~30 s)
                                    log("quadro ao vivo: caminho rápido falhou (" + msg + "); usando o completo")
                                    job["message"] = "Recortando este quadro… (cerca de 30 s)"
                                    work_dir = CACHE / ("fm_" + secrets.token_hex(3))
                                    ok, msg, matte = MA.generate(FFMPEG, BASE, path, s, info, at_c, 1.0 / max(1.0, info["fps"]), work_dir, None, None, lambda: False, log)
                                    if not ok:
                                        raise RuntimeError(msg)
                                MATTE_CACHE[key] = matte
                                while len(MATTE_CACHE) > 6:
                                    k0 = next(iter(MATTE_CACHE))
                                    shutil.rmtree(Path(MATTE_CACHE.pop(k0)["color"]).parent, ignore_errors=True)
                            except Exception as e:  # noqa: BLE001
                                # o recorte avançado falhou neste computador: o quadro fica com o recorte clássico (a prévia) e um aviso com o motivo
                                log("recorte avançado do quadro falhou: " + str(e))
                                matte = None
                                job["matte_off"] = True
                                job["warning"] = "O recorte avançado não funcionou neste computador; o quadro mostra o recorte clássico. Motivo: " + str(e)[:300]
                    job["message"] = "Aplicando cor, luz e fundo…"
                    if matte is None and job.get("quick") and (CACHE / job["quick"]).exists():
                        shutil.copyfile(CACHE / job["quick"], out)         # a prévia rápida já é o quadro final (recorte clássico)
                    else:
                        compose(matte, out)
                job.update(state="done", message="Pronto", out_name=out.name, transparent=P.output_kind(s) != "mp4" and not orig and s["mod_chroma"],
                           width=tw, height=th, at=at_c)
        except Exception as e:  # noqa: BLE001
            log(traceback.format_exc())
            job.update(state="error", error=str(e), message="Falhou.")

    threading.Thread(target=work, daemon=True).start()
    return job


def public_job(job: dict) -> dict:
    out = {k: v for k, v in job.items() if k != "proc"}
    out["keep_awake"] = bool(KA.STATE["awake"] and KA.STATE["blocking"])      # PC sem repouso e desligamento bloqueado (keepawake.py)
    return out


# ---------------------------------------------------------------- servidor
class Handler(BaseHTTPRequestHandler):
    server_version = "Pascal/1.0"

    def log_message(self, fmt: str, *args) -> None:  # silencioso
        pass

    # --- utilidades
    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        return host in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _token_ok(self, query: dict) -> bool:
        return secrets.compare_digest(self.headers.get("X-Token", query.get("k", [""])[0]), TOKEN)

    def _json(self, data, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, msg: str, status: int = 400) -> None:
        self._json({"error": msg}, status)

    def _send_bytes(self, body: bytes, ctype: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        """Entrega arquivo com suporte a Range (o player de vídeo precisa disso para andar no tempo)."""
        if not path.is_file():
            self.send_error(404)
            return
        size = path.stat().st_size
        ctype = mime_of(str(path))
        start, end = 0, size - 1
        status = 200
        rng = self.headers.get("Range")
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            if m:
                if m.group(1):
                    start = int(m.group(1))
                    if m.group(2):
                        end = min(int(m.group(2)), size - 1)
                elif m.group(2):
                    start = max(0, size - int(m.group(2)))
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
                status = 206
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "no-store")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(262144, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionError, OSError):
            pass

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            return {}

    # --- GET
    def do_GET(self) -> None:  # noqa: N802
        if not self._host_ok():
            self.send_error(403)
            return
        u = urlparse(self.path)
        q = parse_qs(u.query)
        route = unquote(u.path)
        try:
            if route in ("/", "/index.html"):
                html = (WEB / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)
                self._send_bytes(html.encode("utf-8"), "text/html; charset=utf-8")
            elif route in ("/app.js", "/i18n.js", "/style.css", "/pascal.png", "/pascal-icon.png"):
                self._send_bytes((WEB / route[1:]).read_bytes(), mime_of(route))
            elif route.startswith("/doc/"):
                name = Path(route[len("/doc/"):]).name
                docs = {"faq": "FAQ_PASCAL", "passo-a-passo": "PASSO_A_PASSO_PASCAL"}
                en = (q.get("lang") or ["pt"])[0] == "en"          # botão PT/EN: o texto em inglês fica em <nome>.en.md
                f = BASE / (docs.get(name, "") + (".en" if en else "") + ".md")
                if en and not f.is_file():
                    f = BASE / (docs.get(name, "") + ".md")
                if name in docs and f.is_file():
                    self._send_bytes(f.read_bytes(), "text/markdown; charset=utf-8")
                else:
                    self.send_error(404)
            elif route.startswith("/media/"):
                if not self._token_ok(q):
                    self.send_error(403)
                    return
                name = Path(route[len("/media/"):]).name
                self._send_file(CACHE / name)
            elif route.startswith("/api/"):
                if not self._token_ok(q):
                    self._err("sem permissão", 403)
                    return
                self.api_get(route, q)
            else:
                self.send_error(404)
        except Exception as e:  # noqa: BLE001
            log(traceback.format_exc())
            self._err(str(e), 500)

    def api_get(self, route: str, q: dict) -> None:
        if route == "/api/state":
            self._json({
                "ffmpeg_ok": bool(FFMPEG and FFPROBE), "ffmpeg": FFMPEG or "", "default": load_default_preset(),
                "input_files": sorted(p.name for p in INPUT.iterdir() if p.suffix.lower() in P.VIDEO_EXTS),
                "input_dir": str(INPUT), "output_dir": str(current_out_dir()),
                "user_presets": sorted(p.stem for p in USER_PRESETS.glob("*.json")),
                "ai": ai_info(), "keep_awake": dict(KA.STATE),
            })
        elif route == "/api/selfcheck":      # Ajuda > Verificar instalação (?fresh=1 refaz; ?lang=en em inglês)
            lang = "en" if q.get("lang", ["pt"])[0] == "en" else "pt"
            start_selfcheck(q.get("fresh", ["0"])[0] == "1")
            res = SELF["result"]
            if res is None:
                self._json({"pending": True, "stage": SELF["stage"]})
            else:
                m = res["matte"]
                self._json({"counts": res["counts"], "when": res["when"], "text": SC.report_text(res, lang),
                            "matte": {"ok": m["ok"], "kind": m["kind"], "why": m["why"], "steps": m["steps"][lang],
                                      "repair": [{"text": r[lang], "ok": r["ok"]} for r in m.get("repair", [])]},
                            "items": [{"level": i["level"], "action": i["action"], **i[lang]} for i in res["items"]]})
        elif route == "/api/ping":
            LAST_PING.update(t=time.time(), seen=True)
            self._json({"ok": True})
        elif route == "/api/bye":      # a janela foi fechada (ou recarregada: o próximo ping cancela)
            LAST_PING["bye"] = time.time()
            self._json({"ok": True})
        elif route == "/api/frame/status":
            job = FRAMES.get(q.get("id", [""])[0])
            self._json(job if job else {"error": "quadro não encontrado"}, 200 if job else 404)
        elif route == "/api/job":
            job = JOBS.get(q.get("id", [""])[0])
            self._json(public_job(job) if job else {"error": "trabalho não encontrado"}, 200 if job else 404)
        elif route == "/api/report":
            job = JOBS.get(q.get("id", [""])[0])
            txt = ""
            if job and job.get("log_dir"):
                try:
                    txt = (Path(job["log_dir"]) / "resumo.txt").read_text(encoding="utf-8")
                except OSError:
                    txt = ""
            self._json({"text": txt, "dir": (job or {}).get("log_dir", "")})
        elif route == "/api/preset":
            p = USER_PRESETS / (safe_name(q.get("name", [""])[0]) + ".json")
            if not p.is_file():
                self._err("preset não encontrado", 404)
            else:
                self._json(P.clean_settings(json.loads(p.read_text(encoding="utf-8"))))
        else:
            self._err("rota desconhecida", 404)

    # --- POST
    def do_POST(self) -> None:  # noqa: N802
        if not self._host_ok():
            self.send_error(403)
            return
        u = urlparse(self.path)
        if not self._token_ok(parse_qs(u.query)):
            self._err("sem permissão", 403)
            return
        data = self._body()
        try:
            self.api_post(u.path, data)
        except Exception as e:  # noqa: BLE001
            log(traceback.format_exc())
            self._err(str(e), 500)

    def _resolve_input(self, data: dict) -> str | None:
        raw = str(data.get("path", "")).strip().strip('"')
        if not raw:
            return None
        p = Path(raw)
        if not p.is_absolute() and (INPUT / raw).is_file():
            p = INPUT / raw
        return str(p) if p.is_file() else None

    def _why_missing(self, data: dict) -> str:
        """Por que o vídeo não abriu: não existe, ou este login do Windows não tem permissão para ele (outra pessoa/outro usuário)."""
        raw = str(data.get("path", "")).strip().strip('"')
        if raw:
            try:
                os.stat(raw)
                if not Path(raw).is_file():
                    return "Isso não é um arquivo de vídeo. Escolha o arquivo do vídeo."
            except PermissionError:
                return "O Windows não deixa este login abrir esse arquivo (sem permissão). Copie o vídeo para uma pasta sua, como Documentos ou a Área de Trabalho, e escolha de novo."
            except OSError:
                pass
        return "Arquivo não encontrado. Confira o caminho."

    def api_post(self, route: str, data: dict) -> None:
        if route == "/api/browse":
            self._json({"path": pick_file_dialog()})
        elif route == "/api/probe":
            path = self._resolve_input(data)
            if not path:
                self._err(self._why_missing(data))
                return
            if not FFPROBE:
                self._err("ffprobe.exe não encontrado na pasta bin.")
                return
            info = P.probe(FFPROBE, path)
            info["path"] = path
            LAST_VIDEO["path"] = path
            info["out_dir"] = str(current_out_dir(path))
            info["out_is_custom"] = bool(load_config().get("out_dir"))
            self._json(info)
        elif route == "/api/autodetect":
            path = self._resolve_input(data)
            if not path or not FFMPEG:
                self._err("Escolha o vídeo primeiro.")
                return
            color = P.detect_green(FFMPEG, path, float(data.get("at", 0) or 0))
            self._json({"color": color} if color else {"error": "Não achei verde nas bordas da imagem nesse ponto do vídeo."})
        elif route in ("/api/preview", "/api/render"):
            path = self._resolve_input(data)
            if not path:
                self._err("Escolha o vídeo primeiro.")
                return
            if not (FFMPEG and FFPROBE):
                self._err("ffmpeg.exe / ffprobe.exe não encontrados na pasta bin.")
                return
            if any_running():
                self._err("Já existe um trabalho rodando. Espere terminar ou cancele.")
                return
            job = (start_preview if route == "/api/preview" else start_render)(path, data.get("settings", {}))
            self._json({"id": job["id"]})
        elif route == "/api/ai/test":
            path = self._resolve_input(data)
            if not path:
                self._err("Escolha o vídeo primeiro.")
                return
            if not UA.find_exe(BASE):
                self._err(UA.HOW_TO)
                return
            if any_running():
                self._err("Já existe um trabalho rodando.")
                return
            self._json({"id": start_ai_test(path, data.get("settings", {}))["id"]})
        elif route == "/api/ai/estimate":
            path = self._resolve_input(data)
            if not path:
                self._err("Escolha o vídeo primeiro.")
                return
            s = P.clean_settings(data.get("settings", {}))
            info = P.probe(FFPROBE, path)
            per = ai_sec_per_frame(path, s)
            if per < 0:
                self._err(UA.HOW_TO)
                return
            frames = int(round((info["duration"] or 0) * info["fps"]))
            self._json({"seconds_per_frame": per, "frames": frames, "eta": UA.fmt_eta(per * frames), "eta_seconds": per * frames})
        elif route == "/api/cancel":
            job = JOBS.get(str(data.get("id", "")))
            if job and job["state"] == "running":
                job["cancel"] = True
                proc = job["proc"].get("proc")
                if proc:
                    proc.terminate()
            self._json({"ok": True})
        elif route == "/api/preset/save":
            name = safe_name(str(data.get("name", "")))
            (USER_PRESETS / f"{name}.json").write_text(
                json.dumps(P.clean_settings(data.get("settings", {})), indent=2, ensure_ascii=False), encoding="utf-8")
            self._json({"name": name})
        elif route == "/api/open-logs":
            if os.name == "nt":
                os.startfile(str(LOGS))  # type: ignore[attr-defined]  # noqa: S606
            self._json({"ok": True})
        elif route == "/api/open-output":
            if os.name == "nt":
                os.startfile(str(current_out_dir()))  # type: ignore[attr-defined]  # noqa: S606
            self._json({"ok": True})
        elif route == "/api/browse-folder":
            d = pick_folder_dialog(str(current_out_dir()))
            if d and Path(d).is_dir():
                save_config(out_dir=d)
            self._json({"dir": str(current_out_dir())})
        elif route == "/api/set-folder":
            d = str(data.get("dir", "")).strip().strip('"')
            if not d:
                self._err("Digite o caminho da pasta.")
                return
            try:
                Path(d).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                self._err("Não consegui usar essa pasta: " + str(e))
                return
            save_config(out_dir=d)
            self._json({"dir": str(current_out_dir())})
        elif route == "/api/reset-folder":
            save_config(out_dir="")
            self._json({"dir": str(current_out_dir())})
        elif route == "/api/frame":
            path = self._resolve_input(data)
            if not path:
                self._err("Escolha o vídeo primeiro.")
                return
            if not (FFMPEG and FFPROBE):
                self._err("ffmpeg.exe / ffprobe.exe não encontrados na pasta bin.")
                return
            if any_running():
                self._err("Um preview ou render está rodando; o quadro ao vivo volta quando terminar.")
                return
            job = start_frame(path, float(data.get("at", 0) or 0), data.get("settings", {}), bool(data.get("orig")), int(data.get("seq", 0) or 0))
            self._json({"id": job["id"]})
        elif route == "/api/unblock":        # tira a marca de "baixado da internet" dos arquivos do Pascal e verifica de novo
            ok, msg = SC.unblock(BASE)
            start_selfcheck(True)
            self._json({"ok": ok, "message": msg})
        elif route == "/api/quit":
            self._json({"ok": True})
            threading.Thread(target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True).start()
        else:
            self._err("rota desconhecida", 404)


# ---------------------------------------------------------------- inicialização
def find_browser() -> list[str] | None:
    roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    candidates = []
    for r in filter(None, roots):
        candidates.append(Path(r) / "Google/Chrome/Application/chrome.exe")
    for r in filter(None, roots):
        candidates.append(Path(r) / "Microsoft/Edge/Application/msedge.exe")
    for c in candidates:
        if c.is_file():
            return [str(c)]
    return None


def open_window(url: str) -> None:
    b = find_browser()
    if b:
        try:
            # janela maximizada (o vídeo é o que mais importa; em telas pequenas 1360x900 não cabe); --disable-pinch: sem zoom por gesto
            subprocess.Popen(b + [f"--app={url}", "--window-size=1360,900", "--start-maximized", "--disable-pinch"])
            return
        except OSError:
            pass
    webbrowser.open(url)


class PascalServer(ThreadingHTTPServer):
    """No Windows o SO_REUSEADDR (padrão do http.server) deixa DOIS programas abertos na mesma porta e os pedidos se misturam
    (a janela fala com um servidor e a "senha" é de outro). Sem ele, a segunda cópia pega a próxima porta."""
    allow_reuse_address = False


def watchdog() -> None:
    """Fecha o servidor sozinho quando a janela do aplicativo é fechada.
    Janela fechada = aviso "bye" sem ping depois dele (8 s). Sem aviso nenhum, só desiste após 20 min sem ping:
    o Chrome atrasa os relógios de janela minimizada/escondida (1 ping por minuto), e o limite antigo de 25 s
    derrubava o servidor no meio do uso ("Failed to fetch")."""
    t0 = time.time()
    while True:
        time.sleep(3)
        now = time.time()
        if LAST_PING["seen"] and not any_running():
            if LAST_PING["bye"] > LAST_PING["t"] and now - LAST_PING["bye"] > 8:
                os._exit(0)
            if now - LAST_PING["t"] > 1200:
                os._exit(0)
        if not LAST_PING["seen"] and time.time() - t0 > 180 and not any_running():
            os._exit(0)


def main() -> None:
    global PORT
    httpd = None
    for port in list(range(8765, 8785)) + [0]:
        try:
            httpd = PascalServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if httpd is None:
        print("Não consegui abrir uma porta local.")
        sys.exit(1)
    PORT = httpd.server_address[1]
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Pascal rodando em {url}")
    print("FFmpeg:", FFMPEG or "NÃO ENCONTRADO (coloque ffmpeg.exe e ffprobe.exe na pasta bin)")
    print("Pode fechar esta janela preta depois de fechar o aplicativo.")
    start_selfcheck(True)                 # confere a instalação em segundo plano (resultado na janela preta e em Ajuda > Verificar instalação)
    threading.Thread(target=watchdog, daemon=True).start()
    threading.Thread(target=KA.loop, args=(any_running, log), name="keepawake", daemon=True).start()   # sem repouso/desligamento durante o render
    if "--sem-janela" not in sys.argv:
        threading.Timer(0.6, open_window, args=(url,)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
