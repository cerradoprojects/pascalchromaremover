"""Testes de diagnóstico do recorte avançado (rodado por Testar_Python.bat). Só biblioteca padrão.
Grava cache\\teste_python.txt com tudo que foi testado e uma conclusão em português simples."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import ctypes  # noqa: E402
import pacotes as PK  # noqa: E402

# autônomo: funciona mesmo com arquivos de uma versão antiga do Pascal na pasta
NOWIN = 0x08000000 if os.name == "nt" else 0
CRASH = {0xC0000005: "acesso inválido à memória", 0xC000001D: "instrução que o processador não tem", 0xC0000135: "falta uma DLL",
         0xC000007B: "DLL de outro tipo (32/64 bits)", 0xC0000142: "uma DLL não conseguiu iniciar", 0xC0000409: "falha interna de segurança",
         0xC0000374: "memória corrompida", 0xC0000022: "acesso negado pelo Windows"}


def explica_codigo(code: int) -> str:
    c = code & 0xFFFFFFFF
    return f"0x{c:08X}" + (f" ({CRASH[c]})" if c in CRASH else "")


def cpu_flags() -> str:
    try:
        f = ctypes.windll.kernel32.IsProcessorFeaturePresent
        return " · ".join(f"{n} {'sim' if f(c) else 'NÃO'}" for n, c in (("SSE4.2", 38), ("AVX", 39), ("AVX2", 40)))
    except (AttributeError, OSError):
        return "?"


def ps_exe() -> str:
    root = os.environ.get("SystemRoot") or r"C:\Windows"
    p = Path(root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    return str(p) if p.is_file() else "powershell"


def desbloquear() -> tuple:
    p = str(BASE).replace("'", "''")
    s = f"Get-ChildItem -LiteralPath '{p}' -Recurse -File -Force -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue"
    code, out, err = run([ps_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", s], 600)
    return code == 0, err[:200]

OUT: list[str] = []


def say(msg: str = "") -> None:
    OUT.append(msg)
    try:
        print(msg, flush=True)
    except (UnicodeEncodeError, OSError):
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


def run(cmd: list, timeout: int = 120) -> tuple:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout, creationflags=NOWIN)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return -999, "", "demorou mais de %d s" % timeout
    except OSError as e:
        return -998, "", f"não abriu: {e}"


PRE = f"import sys; sys.path.insert(0, {str(BASE)!r}); import pacotes; pacotes.ativar(); "
ETAPAS = [
    ("1. Carregar o numpy", PRE + "import numpy; print('numpy', numpy.__version__)"),
    ("2. Fazer uma conta com o numpy", PRE + "import numpy as n; print(n.ones(1000).sum())"),
    ("3. Abrir o arquivo onnxruntime.dll direto", PRE + "import ctypes, pathlib, numpy; import importlib.util as u; s=u.find_spec('onnxruntime'); "
     "d=pathlib.Path(list(s.submodule_search_locations)[0])/'capi'/'onnxruntime.dll'; ctypes.WinDLL(str(d)); print('dll ok', d)"),
    ("4. Carregar o onnxruntime", PRE + "import numpy, onnxruntime; print('onnxruntime', onnxruntime.__version__)"),
    ("5. Abrir o modelo do recorte", PRE + "import numpy, onnxruntime as o, pathlib; m=pathlib.Path(" + repr(str(BASE / 'bin' / 'rvm' / 'rvm_resnet50_fp32.onnx')) +
     "); s=o.InferenceSession(str(m), providers=['CPUExecutionProvider']); print('modelo ok', len(s.get_inputs()), 'entradas')"),
]


def bateria(cmd: list, titulo: str) -> dict:
    """Roda as etapas num Python. Devolve {etapa: (ok, texto)}."""
    say(f"--- {titulo}: {' '.join(cmd)}")
    res = {}
    code, out, err = run(cmd + ["-c", "import sys,struct; print(sys.version.split()[0], struct.calcsize('P')*8, 'bits')"], 60)
    say(f"    versão: {out or err or code}")
    if code != 0:
        say(f"    NÃO ABRIU (código {explica_codigo(code) if code > 0 else code})")
        return {"abre": (False, err or str(code))}
    res["abre"] = (True, out)
    for nome, codigo in ETAPAS:
        if nome.startswith("5") and not res.get("4. Carregar o onnxruntime", (False,))[0]:
            say(f"    {nome}: pulado (o passo 4 falhou)")
            continue
        t = time.time()
        code, out, err = run(cmd + ["-X", "faulthandler", "-c", codigo], 180)
        ok = code == 0
        det = (out.splitlines() or [""])[-1] if ok else (f"CAIU, código {explica_codigo(code)}" if code > 0 and code & 0x80000000 else (err.splitlines() or [str(code)])[-1][:200])
        say(f"    {nome}: {'ok' if ok else 'FALHOU'} ({time.time() - t:.1f}s) {det}")
        res[nome] = (ok, det)
        if not ok and err and code != -999:
            for ln in err.splitlines()[:6]:
                say("        | " + ln[:160])
    return res


def eventos() -> None:
    say("--- O que o Windows registrou quando o Python caiu (Visualizador de Eventos)")
    code, out, err = run(["wevtutil", "qe", "Application", "/q:*[System[(EventID=1000)]]", "/c:12", "/rd:true", "/f:text"], 40)
    blocos = [b for b in out.split("Event[") if "python" in b.lower()]
    if not blocos:
        say("    nenhum registro de queda do python.exe encontrado" + (f" ({err[:80]})" if err else ""))
    for b in blocos[:3]:
        for ln in b.splitlines():
            if any(k in ln for k in ("Date:", "Faulting application name", "Faulting module name", "Exception code", "Fault offset", "Description")):
                say("    " + ln.strip()[:170])
        say("    ·")


def seguranca() -> None:
    say("--- Antivírus / segurança instalados")
    ps = ps_exe()
    code, out, err = run([ps, "-NoProfile", "-Command",
                          "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | ForEach-Object { $_.displayName }"], 40)
    say("    " + (out.replace("\n", " | ") if out else "não consegui listar (sem permissão ou sem Central de Segurança)"))
    code, out, err = run([ps, "-NoProfile", "-Command",
                          "try { (Get-AppLockerPolicy -Effective -ErrorAction Stop).RuleCollections.Count } catch { 'sem acesso' }"], 40)
    say(f"    regras de controle de aplicativos (AppLocker): {out or 'não consegui ler'}")
    code, out, err = run([ps, "-NoProfile", "-Command", "Get-Process | Where-Object { $_.Name -match 'Falcon|CSFalcon|Defender|MsMpEng|Sophos|McAfee|mfe|Symantec|Cylance|Carbon|Trend|ESET|Kaspersky|Crowd|Sentinel|Tanium|Zscaler' } | Select-Object -ExpandProperty Name -Unique"], 40)
    say("    programas de segurança em execução: " + (out.replace("\n", ", ") if out else "nenhum reconhecido"))


def marcas() -> list:
    achou = []
    for f in (BASE / "python" / "python.exe", BASE / "bin" / "ffmpeg.exe", BASE / "python" / "python312.dll"):
        try:
            with open(str(f) + ":Zone.Identifier", "rb"):
                achou.append(f.name)
        except OSError:
            pass
    return achou


def main() -> int:
    say("Pascal — testes do recorte avançado")
    say(time.strftime("%Y-%m-%d %H:%M:%S"))
    say(f"Pasta: {BASE}")
    say(f"Computador: {os.environ.get('COMPUTERNAME', '?')} · processador: {cpu_flags()}")
    say("")
    portable = BASE / "python" / "python.exe"
    antes = bateria([str(portable)], "Python do Pascal (ANTES de desbloquear)")
    say("")
    mar = marcas()
    say(f"--- Arquivos marcados como \"baixados da internet\": {', '.join(mar) if mar else 'nenhum'}")
    depois = None
    if mar:
        say("    Tirando a marca de todos os arquivos do Pascal e testando de novo…")
        ok, msg = desbloquear()
        say(f"    desbloqueio: {'feito' if ok else 'falhou ' + msg}; marcas que sobraram: {', '.join(marcas()) or 'nenhuma'}")
        say("")
        depois = bateria([str(portable)], "Python do Pascal (DEPOIS de desbloquear)")
    say("")
    fora = [c for c in (PK.candidatos(BASE) if hasattr(PK, 'candidatos') else []) if Path(c[0]) != portable and Path(c[0]).resolve() != Path(sys.executable).resolve()]
    if Path(sys.executable).resolve() != portable.resolve():
        fora.insert(0, [sys.executable])
    outros = {}
    for c in fora[:4]:
        outros[c[0]] = bateria(c, "Python instalado no computador")
        say("")
    eventos()
    say("")
    seguranca()
    say("")
    say("=" * 60)
    say("CONCLUSÃO")
    say("=" * 60)
    ok_antes = antes.get("5. Abrir o modelo do recorte", (False,))[0]
    ok_depois = depois is not None and depois.get("5. Abrir o modelo do recorte", (False,))[0]
    ok_outro = [c for c, r in outros.items() if r.get("5. Abrir o modelo do recorte", (False,))[0]]
    if ok_antes:
        say("O Python do Pascal funciona. O recorte avançado deve estar disponível: abra o Pascal normalmente.")
    elif ok_depois:
        say("RESOLVIDO pelo desbloqueio: o Windows bloqueava os arquivos por serem \"baixados da internet\". Abra o Pascal de novo.")
    elif ok_outro:
        say(f"O Python do Pascal não serve neste computador, mas este funciona: {ok_outro[0]}")
        say("O Pascal já usa esse Python sozinho: abra o Pascal normalmente.")
    else:
        falhas = [n for n, (ok, _t) in antes.items() if not ok]
        say("Nenhum Python funcionou com o recorte avançado." + (f" Primeira etapa que falhou: {falhas[0]}." if falhas else ""))
        say("Envie este arquivo inteiro (cache\\teste_python.txt) para quem fez o Pascal: ele mostra onde trava e quem derrubou o programa.")
    try:
        (BASE / "cache").mkdir(exist_ok=True)
        (BASE / "cache" / "teste_python.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
        print("\nRelatório gravado em: " + str(BASE / "cache" / "teste_python.txt"))
    except OSError as e:
        print("Não consegui gravar o relatório:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
