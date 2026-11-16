"""Pacotes do recorte avançado (numpy + onnxruntime) para qualquer Python, sem pip e sem internet.

O Pascal leva os pacotes prontos para cada versão de Python:
  3.12 -> python\\Lib\\site-packages   (o Python portátil do próprio Pascal)
  3.13 -> pacotes\\py313               (ex.: o Python instalado de X:\\Python no computador corporativo)
  3.14 -> pacotes\\py314
`ativar()` põe a pasta certa no começo do sys.path. Só biblioteca padrão: pode ser importado antes do numpy.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
VERSOES = ((3, 12), (3, 13), (3, 14))      # versões para as quais o Pascal leva os pacotes
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
# imprime a versão ANTES de importar: se o import falhar, ainda dá para dizer qual Python era
_TESTE = ("import sys, struct; print('VER', '%d.%d.%d' % sys.version_info[:3], struct.calcsize('P') * 8, flush=True); "
          "sys.path.insert(0, {base!r}); import pacotes; pacotes.ativar(); "
          "print('STEP numpy', flush=True); import numpy; print('STEP onnxruntime', flush=True); import onnxruntime; "
          "print('OK numpy', numpy.__version__, '| onnxruntime', onnxruntime.__version__)")

# códigos de saída do Windows quando o programa "cai" sem dizer nada (NTSTATUS)
CRASH = {0xC0000005: "acesso inválido à memória", 0xC000001D: "instrução que o processador não tem", 0xC0000135: "falta uma DLL",
         0xC000007B: "DLL de outro tipo (32/64 bits)", 0xC0000142: "uma DLL não conseguiu iniciar", 0xC0000409: "falha interna de segurança",
         0xC0000374: "memória corrompida", 0xC0000022: "acesso negado pelo Windows"}


def explica_codigo(code: int) -> str:
    """'0xC0000005 (acesso inválido à memória)' ou só o número, para um código de saída do Windows."""
    c = code & 0xFFFFFFFF
    return f"0x{c:08X}" + (f" ({CRASH[c]})" if c in CRASH else "")


def pasta(base: Path = BASE, ver: tuple = None) -> Path | None:
    """Pasta com numpy/onnxruntime para esta versão do Python (None se o Pascal não leva para ela)."""
    maj, mi = (ver or sys.version_info)[:2]
    cands = [base / "pacotes" / f"py{maj}{mi}"]
    if (maj, mi) == (3, 12):
        cands.append(base / "python" / "Lib" / "site-packages")
    for p in cands:
        if (p / "numpy").is_dir() and (p / "onnxruntime").is_dir():
            return p
    return None


def ativar(base: Path = BASE) -> Path | None:
    """Deixa `import numpy, onnxruntime` funcionar neste Python. Devolve a pasta usada (ou None)."""
    if sys.maxsize <= 2**32:          # Python de 32 bits: os pacotes são de 64
        return None
    p = pasta(base)
    if p and str(p) not in sys.path:
        sys.path.insert(0, str(p))
    # o onnxruntime precisa do C++ da Microsoft (msvcp140.dll). Se o Windows não tem, usa a cópia que vai na pasta python do Pascal.
    sys32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "msvcp140.dll"
    local = base / "python"
    if hasattr(os, "add_dll_directory") and not sys32.is_file() and (local / "msvcp140.dll").is_file():
        try:
            os.add_dll_directory(str(local))
        except OSError:
            pass
    return p


def _globs(raiz: Path, padroes: tuple) -> list:
    try:
        if not raiz.is_dir():
            return []
        out = []
        for pad in padroes:
            out += sorted(raiz.glob(pad), reverse=True)
        return out
    except OSError:
        return []


def candidatos(base: Path = BASE) -> list:
    """Pythons a testar, na ordem: o portátil do Pascal, o que roda o programa, os instalados no computador.
    Inclui X:\\Python (pasta de programas liberados em computador corporativo), o instalador do python.org (por usuário e para todos) e o gerenciador de Pythons novo."""
    lista = [base / "python" / "python.exe", Path(sys.executable)]
    lista += _globs(Path("X:/Python"), ("python.exe", "*/python.exe", "*/*/python.exe"))
    la = os.environ.get("LOCALAPPDATA")
    if la:
        lista += _globs(Path(la) / "Python", ("pythoncore-3.*/python.exe",))
        lista += _globs(Path(la) / "Programs" / "Python", ("Python3*/python.exe",))
    for raiz in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"), "C:/"):
        if raiz:
            lista += _globs(Path(raiz), ("Python3*/python.exe",))
    for nome in ("python", "py"):
        w = shutil.which(nome)
        if w:
            lista.append(Path(w))
    cmds, vistos = [], set()
    for p in lista:
        chave = str(p).lower().replace("/", "\\")
        if chave in vistos or "\\windowsapps\\" in chave:       # atalho da Microsoft Store (só abre a loja) não serve
            continue
        vistos.add(chave)
        cmds.append([str(p), "-3"] if p.stem.lower() == "py" else [str(p)])
    return cmds


def testar(cmd: list, base: Path = BASE, timeout: float = 30) -> tuple:
    """Roda `import numpy, onnxruntime` nesse Python (com os pacotes do Pascal). Devolve (ok, texto, versão 'X.Y.Z', bits).
    texto = 'numpy … | onnxruntime …' se deu certo, senão a última linha do erro já explicada."""
    if not cmd or not Path(cmd[0]).is_file():
        return False, "", "", 0
    try:
        r = subprocess.run(cmd + ["-c", _TESTE.format(base=str(base))], capture_output=True, text=True, errors="replace",
                           timeout=timeout, creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise
    except (OSError, ValueError) as e:            # bloqueado pelo Windows, sem permissão etc.
        return False, f"não abriu ({e.__class__.__name__}: {str(e)[:120]})", "", 0
    ver, bits, etapa = "", 0, ""
    for ln in r.stdout.splitlines():
        if ln.startswith("VER "):
            partes = ln.split()
            ver, bits = partes[1], int(partes[2]) if len(partes) > 2 and partes[2].isdigit() else 0
        elif ln.startswith("STEP "):
            etapa = ln[5:].strip()
        elif ln.startswith("OK ") and r.returncode == 0:
            return True, ln[3:].strip(), ver, bits
    linhas = r.stderr.strip().splitlines()
    caiu = bool(r.returncode & 0x80000000)            # código 0xC0000xxx: o programa foi derrubado pelo Windows
    if linhas and any(k in linhas[-1] for k in ("Error", "Exception")):
        err = linhas[-1][:200]                        # o Python explicou o erro
    elif caiu and etapa:                              # abriu e caiu no meio de um import: diz qual
        err = f"travou ao carregar o {etapa} — o programa fechou sozinho, código {explica_codigo(r.returncode)}"
    else:
        err = (linhas[-1][:200] if linhas else f"saiu com código {explica_codigo(r.returncode)}")
    if ver:
        mm = tuple(int(x) for x in ver.split(".")[:2])
        if bits and bits != 64:
            err = f"Python {ver} de {bits} bits: o recorte avançado precisa de Python de 64 bits"
        elif mm not in VERSOES:
            err = f"Python {ver}: o Pascal traz os pacotes só para Python " + ", ".join("%d.%d" % v for v in VERSOES) + f" ({err})"
    return False, err, ver, bits


if __name__ == "__main__":            # teste rápido: python pacotes.py
    print("pasta:", ativar())
    import numpy, onnxruntime          # noqa: E401
    print("numpy", numpy.__version__, "| onnxruntime", onnxruntime.__version__)
