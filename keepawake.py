"""Pascal — impede o Windows de dormir e de desligar enquanto um vídeo está sendo gerado.

Dois mecanismos, os dois sem administrador (só a biblioteca padrão do Python):
  1) SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED): o PC não entra em repouso por inatividade
     (a tela pode apagar; só o computador fica acordado).
  2) Bloqueio de desligamento: uma janela invisível do próprio programa responde "não" ao pedido de desligar, reiniciar ou sair
     da conta (WM_QUERYENDSESSION) e dá o motivo ao Windows (ShutdownBlockReasonCreate). O Windows mostra "Pascal está impedindo
     o desligamento" e a pessoa decide se desliga assim mesmo: nenhum programa consegue impedir um desligamento forçado
     (queda de energia, "desligar assim mesmo", reinício obrigatório de atualização).
Roda numa thread própria: enquanto is_busy() for verdadeiro, os dois ficam ligados; ao terminar (pronto, erro ou cancelado), soltam.
Fora do Windows não faz nada."""
from __future__ import annotations

import sys
import threading
import time

IS_WIN = sys.platform == "win32"
REASON = "O Pascal está gerando o seu vídeo. Se desligar agora, o trabalho será perdido."
CLASS_NAME = "PascalShutdownGuard"

# lido pela interface (/api/state): ligado/desligado e o último erro
STATE: dict = {"awake": False, "blocking": False, "error": "", "since": 0.0}
_W: dict = {"hwnd": None, "block": False, "ready": threading.Event(), "thread": None}

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    WM_DESTROY = 0x0002
    WM_QUERYENDSESSION = 0x0011
    WM_APP = 0x8000
    MSG_BLOCK, MSG_UNBLOCK = WM_APP + 1, WM_APP + 2
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                    ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HANDLE), ("hCursor", wintypes.HANDLE),
                    ("hbrBackground", wintypes.HANDLE), ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    user32.RegisterClassW.restype = wintypes.ATOM
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HANDLE, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = ctypes.c_int
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = LRESULT
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.ShutdownBlockReasonCreate.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
    user32.ShutdownBlockReasonCreate.restype = wintypes.BOOL
    user32.ShutdownBlockReasonDestroy.argtypes = [wintypes.HWND]
    user32.ShutdownBlockReasonDestroy.restype = wintypes.BOOL
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    kernel32.SetThreadExecutionState.argtypes = [wintypes.DWORD]
    kernel32.SetThreadExecutionState.restype = wintypes.DWORD

    def _wndproc(hwnd, msg, wparam, lparam):
        if msg == WM_QUERYENDSESSION:
            return 0 if _W["block"] else 1                  # 0 = "ainda não": o Windows mostra o motivo e pergunta à pessoa
        if msg == MSG_BLOCK:
            _W["block"] = True
            user32.ShutdownBlockReasonCreate(hwnd, REASON)
            return 0
        if msg == MSG_UNBLOCK:
            _W["block"] = False
            user32.ShutdownBlockReasonDestroy(hwnd)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    _WNDPROC_REF = WNDPROC(_wndproc)                        # precisa ficar vivo enquanto a janela existir

    def _window_thread() -> None:
        try:
            hinst = kernel32.GetModuleHandleW(None)
            wc = WNDCLASSW()
            wc.lpfnWndProc = _WNDPROC_REF
            wc.hInstance = hinst
            wc.lpszClassName = CLASS_NAME
            user32.RegisterClassW(ctypes.byref(wc))
            # janela de topo, invisível (nunca recebe ShowWindow): só ela recebe o pedido de desligamento
            _W["hwnd"] = user32.CreateWindowExW(0, CLASS_NAME, "Pascal", 0, 0, 0, 0, 0, None, None, hinst, None)
            if not _W["hwnd"]:
                STATE["error"] = f"janela de proteção não criada (erro {ctypes.get_last_error()})"
        except Exception as e:  # noqa: BLE001
            STATE["error"] = f"janela de proteção: {e!r}"
        finally:
            _W["ready"].set()
        if not _W["hwnd"]:
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _ensure_window() -> bool:
        if _W["thread"] is None:
            _W["thread"] = threading.Thread(target=_window_thread, name="pascal-shutdown-guard", daemon=True)
            _W["thread"].start()
        _W["ready"].wait(5)
        return bool(_W["hwnd"])

    def ask_end_session() -> int:
        """Teste: manda o mesmo pedido que o Windows manda ao desligar. 0 = bloqueado (o Pascal está gerando vídeo), 1 = liberado."""
        if not _W["hwnd"]:
            return 1
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.SendMessageW.restype = LRESULT
        return int(user32.SendMessageW(_W["hwnd"], WM_QUERYENDSESSION, 0, 0))

    def reason_text() -> str:
        """Teste: o motivo que o Windows exibiria agora ('' = nenhum)."""
        if not _W["hwnd"]:
            return ""
        user32.ShutdownBlockReasonQuery.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        user32.ShutdownBlockReasonQuery.restype = wintypes.BOOL
        n = wintypes.DWORD(0)
        user32.ShutdownBlockReasonQuery(_W["hwnd"], None, ctypes.byref(n))
        if n.value == 0:
            return ""
        buf = ctypes.create_unicode_buffer(n.value + 1)
        n2 = wintypes.DWORD(n.value + 1)
        return buf.value if user32.ShutdownBlockReasonQuery(_W["hwnd"], buf, ctypes.byref(n2)) else ""


def _apply(busy: bool, log) -> None:
    """Liga/desliga os dois mecanismos. Chamada SEMPRE pela mesma thread (o estado de execução é por thread)."""
    if not IS_WIN:
        return
    prev = kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if busy else 0))
    STATE["awake"] = bool(busy and prev)
    ok_win = _ensure_window() if busy or _W["hwnd"] else False
    if ok_win:
        _W["block"] = busy                                   # vale já para um pedido que chegue neste instante
        user32.PostMessageW(_W["hwnd"], MSG_BLOCK if busy else MSG_UNBLOCK, 0, 0)
    STATE["blocking"] = bool(busy and ok_win)
    STATE["since"] = time.time() if busy else 0.0
    if busy:
        log("PC protegido: sem repouso e com desligamento bloqueado enquanto o vídeo é gerado"
            + ("" if STATE["awake"] and STATE["blocking"] else f" (INCOMPLETO: awake={STATE['awake']} bloqueio={STATE['blocking']} {STATE['error']})"))
    else:
        log("PC liberado: o vídeo terminou, o Windows pode dormir e desligar normalmente")


def loop(is_busy, log=lambda m: None, every: float = 2.0) -> None:
    """Para rodar numa thread: enquanto is_busy() for verdadeiro mantém o PC acordado e o desligamento bloqueado."""
    if not IS_WIN:
        return
    held = False
    while True:
        try:
            busy = bool(is_busy())
            if busy != held:
                held = busy
                _apply(busy, log)
        except Exception as e:  # noqa: BLE001  (a proteção nunca derruba o programa)
            STATE["error"] = repr(e)
            log(f"ERRO na proteção contra desligamento: {e!r}")
        time.sleep(every)
