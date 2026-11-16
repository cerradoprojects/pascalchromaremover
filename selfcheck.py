"""Verificação da instalação do Pascal (Ajuda > Verificar instalação).

Testa, em linguagem simples, o que costuma dar errado em outro computador: FFmpeg bloqueado ou ausente, pacotes do recorte avançado,
modelo, pastas sem permissão, navegador, memória, espaço em disco, pasta aberta de dentro do zip e arquivos marcados como "baixados da internet".
Cada item traz o texto em português e em inglês. Só biblioteca padrão.
"""
from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
VC_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"


class _MemStatus(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]


def _ram_gb() -> tuple[float, float] | None:
    """(total, livre) em GB, ou None se o Windows não responder."""
    try:
        m = _MemStatus()
        m.dwLength = ctypes.sizeof(_MemStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return m.ullTotalPhys / 2**30, m.ullAvailPhys / 2**30
    except (AttributeError, OSError):
        pass
    return None


def ps_exe() -> str:
    """Caminho completo do PowerShell (não depende do PATH, que em alguns computadores vem cortado)."""
    root = os.environ.get("SystemRoot") or os.environ.get("windir") or r"C:\Windows"
    p = Path(root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    return str(p) if p.is_file() else "powershell"


def _is_blocked(err: Exception) -> bool:
    """O Windows (antivírus, SmartScreen, Controle de Aplicativo) recusou rodar o arquivo?"""
    code = getattr(err, "winerror", None)
    return code in (5, 1260, 4551, 4552, 4553, 225)       # acesso negado, política de grupo, controle de aplicativo, vírus detectado


def _item(level: str, pt: tuple, en: tuple, action: str = "") -> dict:
    """pt/en = (título, detalhe, o que fazer)."""
    pad = lambda t: (list(t) + ["", "", ""])[:3]           # noqa: E731
    p, e = pad(pt), pad(en)
    return {"level": level, "action": action,
            "pt": {"title": p[0], "detail": p[1], "fix": p[2]}, "en": {"title": e[0], "detail": e[1], "fix": e[2]}}


def _check_exe(path: str | None, name: str) -> dict:
    if not path:
        return _item("fail", (f"{name} não encontrado", f"O arquivo {name} não está na pasta bin do Pascal.",
                              "Baixe o Pascal.zip completo na página Releases do GitHub (não o botão Code > Download ZIP, que só traz o código) e extraia tudo."),
                     (f"{name} not found", f"{name} is not in Pascal's bin folder.",
                      "Download the full Pascal.zip from the GitHub Releases page (not Code > Download ZIP, which only has the source) and extract everything."))
    try:
        r = subprocess.run([path, "-version"], capture_output=True, text=True, errors="replace", timeout=45, creationflags=CREATE_NO_WINDOW)
        if r.returncode == 0:
            first = (r.stdout.strip().splitlines() or [""])[0][:90]
            return _item("ok", (f"{name} funciona", first), (f"{name} works", first))
        tail = (r.stderr.strip().splitlines() or [f"código {r.returncode}"])[-1][:160]
        return _item("fail", (f"{name} não rodou", tail, "Extraia o zip de novo (o arquivo pode ter vindo incompleto)."),
                     (f"{name} did not run", tail, "Extract the zip again (the file may be incomplete)."))
    except subprocess.TimeoutExpired:
        return _item("warn", (f"{name} demorou para responder", "Mais de 45 segundos. O antivírus pode estar examinando o arquivo.", "Espere um pouco e use Verificar de novo."),
                     (f"{name} was slow to answer", "More than 45 seconds. The antivirus may be scanning the file.", "Wait a bit and check again."))
    except OSError as e:
        if _is_blocked(e):
            return _item("fail", (f"O Windows bloqueou o {name}", str(e)[:160],
                                  "Clique em Desbloquear arquivos (abaixo). Se continuar, abra o antivírus ou a Segurança do Windows e libere a pasta do Pascal."),
                         (f"Windows blocked {name}", str(e)[:160],
                          "Click Unblock files (below). If it persists, open your antivirus or Windows Security and allow Pascal's folder."), "unblock")
        return _item("fail", (f"{name} não rodou", str(e)[:160], "Extraia o zip de novo e tente outra vez."),
                     (f"{name} did not run", str(e)[:160], "Extract the zip again and retry."))


def run(base: Path, ffmpeg: str | None, ffprobe: str | None, out_dir: Path, browser: list | None) -> dict:
    items: list[dict] = []

    # sistema
    ram = _ram_gb()
    cpus = os.cpu_count() or 0
    sysline = f"{platform.platform()} · {cpus} núcleos" + (f" · {ram[0]:.1f} GB de memória" if ram else "")
    sysline_en = f"{platform.platform()} · {cpus} cores" + (f" · {ram[0]:.1f} GB of memory" if ram else "")
    items.append(_item("ok", ("Computador", sysline + f" · Python {platform.python_version()}"), ("Computer", sysline_en + f" · Python {platform.python_version()}")))

    # onde o Pascal está
    p = str(base)
    low = p.lower()
    if ".zip" in low or "\\temp\\temp" in low:
        items.append(_item("fail", ("O Pascal está sendo aberto de dentro do zip", p, "Clique com o botão direito no Pascal.zip, escolha Extrair tudo e abra o Iniciar_Pascal.bat da pasta extraída."),
                           ("Pascal is being run from inside the zip", p, "Right-click Pascal.zip, choose Extract all, and open Iniciar_Pascal.bat from the extracted folder.")))
    elif len(p) > 110:
        items.append(_item("warn", ("O caminho da pasta do Pascal é muito longo", f"{len(p)} caracteres: {p}", "Mova a pasta para um lugar curto, por exemplo C:\\Pascal, para o Windows não perder arquivos."),
                           ("Pascal's folder path is very long", f"{len(p)} characters: {p}", "Move the folder somewhere short, for example C:\\Pascal, so Windows doesn't drop files.")))
    else:
        items.append(_item("ok", ("Pasta do Pascal", p), ("Pascal folder", p)))

    # FFmpeg e FFprobe
    items.append(_check_exe(ffmpeg, "ffmpeg.exe"))
    items.append(_check_exe(ffprobe, "ffprobe.exe"))

    # recorte avançado: modelo + pacotes
    model = None
    for cand in (base / "bin" / "rvm" / "rvm_resnet50_fp32.onnx", base / "bin" / "rvm_resnet50_fp32.onnx"):
        if cand.is_file():
            model = cand
            break
    if model is None:
        items.append(_item("warn", ("Modelo do recorte avançado ausente", "Falta bin\\rvm\\rvm_resnet50_fp32.onnx.", "Sem ele o Pascal usa o recorte clássico. Baixe o Pascal.zip completo para ter o recorte avançado."),
                           ("Advanced cutout model missing", "bin\\rvm\\rvm_resnet50_fp32.onnx is missing.", "Without it Pascal uses the classic cutout. Download the full Pascal.zip to get the advanced cutout.")))
    elif model.stat().st_size < 50 * 2**20:
        items.append(_item("warn", ("Modelo do recorte avançado incompleto", f"{model.stat().st_size / 2**20:.0f} MB (o esperado é cerca de 100 MB).", "Baixe o Pascal.zip de novo."),
                           ("Advanced cutout model is incomplete", f"{model.stat().st_size / 2**20:.0f} MB (about 100 MB expected).", "Download Pascal.zip again.")))
    else:
        import pacotes as PK
        portable = str(base / "python" / "python.exe")
        try:
            found, errs = None, []
            for cmd in PK.candidatos(base):        # o portátil do Pascal, o que roda o programa, os instalados (X:\Python etc.)
                ok, txt, ver, _b = PK.testar(cmd, base, timeout=150 if cmd[0] == portable else 60)
                if ok:
                    found = (cmd[0], txt, ver)
                    break
                if txt:
                    errs.append((cmd[0], txt, ver))
            if found:
                where = f"Python {found[2]} · {found[0]}"
                items.append(_item("ok", ("Recorte avançado disponível", f"{found[1]} ({where})"), ("Advanced cutout available", f"{found[1]} ({where})")))
            else:
                # o erro mais útil é o de um Python que abriu (tem versão); o "não abriu" fica de fallback
                errs.sort(key=lambda e: 0 if e[2] else 1)
                err = "; ".join(f"{t} ({c})" for c, t, _v in errs[:2])[:300] or "nenhum Python encontrado neste computador"
                need_vc = any(k in err.upper() for k in ("DLL", "MSVCP", "VCRUNTIME", "ONNXRUNTIME_PYBIND"))
                local_vc = (base / "python" / "msvcp140.dll").is_file()
                act = ""
                if need_vc and local_vc:      # os arquivos do C++ já estão na pasta: então é o Windows/antivírus que impede o carregamento
                    pre_pt = "Os arquivos do C++ já vão dentro do Pascal, então algo no Windows (antivírus ou bloqueio de segurança) está impedindo o carregamento. Clique em Desbloquear arquivos ou libere a pasta do Pascal no antivírus. "
                    pre_en = "The C++ files already ship inside Pascal, so something in Windows (antivirus or a security block) is preventing them from loading. Click Unblock files or allow Pascal's folder in your antivirus. "
                    act = "unblock"
                elif need_vc:
                    pre_pt = f"Extraia de novo o Pascal.zip mais recente (ele já leva os arquivos do C++) ou peça a quem administra o computador para instalar o \"Microsoft Visual C++ Redistributable\" (64 bits): {VC_URL} . "
                    pre_en = f"Extract the latest Pascal.zip again (it already carries the C++ files) or ask whoever administers the computer to install the \"Microsoft Visual C++ Redistributable\" (64-bit): {VC_URL} . "
                elif not any(e[2] for e in errs) or "só para Python" in err or "64 bits" in err:
                    pre_pt = ("O Python do Pascal não abriu (o computador pode bloquear programas fora das pastas autorizadas). Instale o Python 3.13 ou 3.14 de 64 bits "
                              "(em computador corporativo o instalador costuma ficar numa pasta de programas liberados, por exemplo X:\\Python) e abra o Pascal de novo: os pacotes já vão dentro do Pascal, não precisa instalar mais nada. ")
                    pre_en = ("Pascal's own Python did not open (the computer may block programs outside approved folders). Install Python 3.13 or 3.14 64-bit "
                              "and open Pascal again: the packages already ship inside Pascal, nothing else to install. ")
                else:
                    pre_pt = pre_en = ""
                items.append(_item("warn", ("Recorte avançado indisponível neste computador", err, pre_pt + "Enquanto isso o Pascal usa o recorte clássico (mais rápido, menos natural no cabelo)."),
                                   ("Advanced cutout unavailable on this computer", err, pre_en + "Meanwhile Pascal uses the classic cutout (faster, less natural on hair)."), act))
        except subprocess.TimeoutExpired:
            items.append(_item("warn", ("O recorte avançado demorou demais para iniciar", "Mais de 2 minutos para carregar os pacotes (antivírus examinando?).", "Tente de novo em alguns minutos."),
                               ("The advanced cutout took too long to start", "More than 2 minutes to load the packages (antivirus scanning?).", "Try again in a few minutes.")))
        except OSError as e:
            items.append(_item("warn", ("Não consegui testar o recorte avançado", str(e)[:160], "O Pascal usa o recorte clássico."),
                               ("Couldn't test the advanced cutout", str(e)[:160], "Pascal uses the classic cutout.")))

    # arquivos do C++ (Visual C++) e do Vulkan: o recorte avançado precisa do primeiro; a ampliação avançada, do segundo
    sysroot = os.environ.get("SystemRoot") or os.environ.get("windir") or r"C:\Windows"
    if (base / "python" / "msvcp140.dll").is_file():
        items.append(_item("ok", ("Arquivos do C++ (Visual C++)", "Já vão dentro do Pascal (pasta python): não precisa instalar nada."),
                           ("C++ files (Visual C++)", "They already ship inside Pascal (python folder): nothing to install.")))
    elif (Path(sysroot) / "System32" / "msvcp140.dll").is_file():
        items.append(_item("ok", ("Arquivos do C++ (Visual C++)", "Instalados no Windows."), ("C++ files (Visual C++)", "Installed in Windows.")))
    else:
        items.append(_item("warn", ("Faltam os arquivos do C++ (Visual C++)", "O recorte avançado precisa deles (msvcp140.dll).",
                                    "Extraia de novo o Pascal.zip mais recente (ele já leva esses arquivos) ou peça a quem administra o computador para instalar o Microsoft Visual C++ Redistributable."),
                           ("C++ files (Visual C++) are missing", "The advanced cutout needs them (msvcp140.dll).",
                            "Extract the latest Pascal.zip again (it already carries these files) or ask whoever administers the computer to install the Microsoft Visual C++ Redistributable.")))
    if any((base / "bin").rglob("realesrgan-ncnn-vulkan.exe")) and not (Path(sysroot) / "System32" / "vulkan-1.dll").is_file():
        items.append(_item("warn", ("Este computador não tem o Vulkan (driver de vídeo)", "Falta o arquivo vulkan-1.dll.",
                                    "Só a ampliação avançada fica indisponível; o modo Rápido e o recorte funcionam normalmente."),
                           ("This computer has no Vulkan (video driver)", "vulkan-1.dll is missing.",
                            "Only the advanced upscaling is unavailable; Fast mode and the cutout work normally.")))

    # pastas de trabalho
    bad = []
    for d in (base / "cache", base / "logs", base / "output", base / "presets_usuario", out_dir):
        try:
            d.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=str(d), prefix="_teste_", delete=True):
                pass
        except OSError as e:
            bad.append(f"{d} ({e.strerror or e})")
    if bad:
        items.append(_item("fail", ("O Pascal não consegue gravar em uma pasta", "; ".join(bad), "Mova a pasta do Pascal para um lugar onde você possa gravar (por exemplo C:\\Pascal) ou escolha outra pasta de destino."),
                           ("Pascal can't write to a folder", "; ".join(bad), "Move Pascal's folder somewhere you can write (for example C:\\Pascal) or pick another destination folder.")))
    else:
        items.append(_item("ok", ("Pastas de trabalho gravam normalmente", str(out_dir)), ("Work folders are writable", str(out_dir))))

    # PowerShell (o botão Escolher… usa a janela do Windows pelo PowerShell)
    if ps_exe() == "powershell" and not shutil.which("powershell"):
        items.append(_item("warn", ("PowerShell não encontrado", "O botão Escolher… precisa dele para abrir a janela de escolha do Windows.", "Cole o caminho do vídeo (e da pasta) nos campos do Pascal."),
                           ("PowerShell not found", "The Choose… buttons need it to open the Windows chooser window.", "Paste the video (and folder) path into Pascal's fields.")))

    # navegador
    if browser:
        items.append(_item("ok", ("Navegador para a janela do Pascal", Path(browser[0]).name), ("Browser for Pascal's window", Path(browser[0]).name)))
    else:
        items.append(_item("warn", ("Chrome ou Edge não encontrados", "O Pascal abre no navegador padrão, que pode não funcionar bem.", "Instale o Google Chrome ou use o Microsoft Edge e abra o Pascal de novo."),
                           ("Chrome or Edge not found", "Pascal opens in the default browser, which may not work well.", "Install Google Chrome or use Microsoft Edge and open Pascal again.")))

    # memória
    if ram:
        if ram[0] < 6:
            items.append(_item("warn", ("Pouca memória neste computador", f"{ram[0]:.1f} GB no total ({ram[1]:.1f} GB livres agora).",
                                        "O recorte avançado usa cerca de 3 GB: pode ficar muito lento ou falhar. Feche outros programas ou use o recorte clássico."),
                               ("Little memory on this computer", f"{ram[0]:.1f} GB total ({ram[1]:.1f} GB free now).",
                                "The advanced cutout uses about 3 GB: it can be very slow or fail. Close other programs or use the classic cutout.")))
        elif ram[1] < 2.5:
            items.append(_item("warn", ("Pouca memória livre agora", f"{ram[1]:.1f} GB livres de {ram[0]:.1f} GB.", "Feche o navegador, o Premiere e outros programas pesados."),
                               ("Little free memory right now", f"{ram[1]:.1f} GB free of {ram[0]:.1f} GB.", "Close the browser, Premiere and other heavy programs.")))
    if cpus and cpus <= 2:
        items.append(_item("warn", ("Processador com poucos núcleos", f"{cpus} núcleos.", "O primeiro quadro pode levar vários minutos; o vídeo completo será muito lento."),
                           ("Processor with few cores", f"{cpus} cores.", "The first frame can take several minutes; the full video will be very slow.")))

    # espaço em disco
    try:
        free = shutil.disk_usage(str(out_dir)).free / 2**30
        if free < 5:
            items.append(_item("warn", ("Pouco espaço em disco na pasta de destino", f"{free:.1f} GB livres.", "O vídeo com transparência pode ocupar mais de 2 GB por minuto."),
                               ("Little disk space in the destination folder", f"{free:.1f} GB free.", "The transparent video can take over 2 GB per minute.")))
    except OSError:
        pass

    # marca de "baixado da internet"
    marked = False
    for f in (ffmpeg, ffprobe, str(base / "python" / "python.exe")):
        if f:
            try:
                with open(f + ":Zone.Identifier", "rb"):
                    marked = True
                    break
            except OSError:
                pass
    if marked:
        items.append(_item("warn", ("Os arquivos estão marcados como \"baixados da internet\"", "O Windows pode bloquear ou examinar cada programa na primeira vez.",
                                    "Se algo não funcionar, clique em Desbloquear arquivos (abaixo)."),
                           ("Files are marked as \"downloaded from the internet\"", "Windows may block or scan each program the first time.",
                            "If something doesn't work, click Unblock files (below)."), "unblock"))

    counts = {k: sum(1 for i in items if i["level"] == k) for k in ("ok", "warn", "fail")}
    return {"items": items, "counts": counts, "when": time.strftime("%Y-%m-%d %H:%M:%S")}


def report_text(result: dict, lang: str) -> str:
    sign = {"ok": "[OK]  ", "warn": "[ATENÇÃO]  " if lang != "en" else "[WARNING]  ", "fail": "[PROBLEMA]  " if lang != "en" else "[PROBLEM]  "}
    head = "Pascal — verificação da instalação" if lang != "en" else "Pascal — installation check"
    lines = [f"{head} ({result['when']})", ""]
    for i in result["items"]:
        t = i["en" if lang == "en" else "pt"]
        lines.append(sign[i["level"]] + t["title"] + (" — " + t["detail"] if t["detail"] else ""))
        if t["fix"] and i["level"] != "ok":
            lines.append("      → " + t["fix"])
    return "\n".join(lines)


def unblock(base: Path) -> tuple[bool, str]:
    """Tira a marca de "baixado da internet" de todos os arquivos da pasta do Pascal (só os arquivos do próprio usuário; sem administrador)."""
    p = str(base).replace("'", "''")
    script = f"Get-ChildItem -LiteralPath '{p}' -Recurse -File -Force -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue"
    try:
        r = subprocess.run([ps_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], capture_output=True, text=True, errors="replace",
                           timeout=600, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0, (r.stderr.strip().splitlines() or [""])[-1][:200]
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)[:200]
