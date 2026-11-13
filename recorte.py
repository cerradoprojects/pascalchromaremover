r"""Recorte de chroma key como peça independente.

Uso pela linha de comando (PowerShell, dentro da pasta do projeto):
    python\python.exe recorte.py "C:\videos\gravacao.mp4" "C:\saida" --formato prores

Uso dentro de outro Python:
    from recorte import recortar
    arquivo = recortar("gravacao.mp4", "saida", formato="prores")

O que faz:
  * gera uma máscara de transparência suave a partir do verde (chroma key + proteção de roupa oliva);
  * NÃO mexe na cor do rosto/cabelo/roupa: o chroma key só gera a máscara, a cor original segue intacta;
  * aplica o despill (tirar reflexo verde) só na faixa estreita da borda;
  * descarta cantos do quadro e elementos finos isolados (microfone, suporte, cabo);
  * formato "prores"  -> .mov Apple ProRes 4444 com canal alfa (yuva444p10le), direto na timeline do Premiere
    formato "qtrle"   -> .mov QuickTime Animation com alfa (mais leve)
    formato "mp4"     -> .mp4 H.264 com fundo preto de estúdio (quando não precisa de transparência)
Nenhum módulo de cor, nitidez ou áudio é ligado aqui — só o recorte (o áudio original é preservado).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import pipeline as P  # noqa: E402
FORMATOS = {"prores": "alpha_prores", "qtrle": "alpha_qtrle", "mp4": "studio_mp4"}


def recortar(entrada: str | Path, pasta_saida: str | Path, formato: str = "prores",
             ajustes: dict | None = None, progresso=None, ffmpeg: str | None = None,
             ffprobe: str | None = None) -> Path:
    """Recorta o fundo verde de `entrada` e grava o arquivo final em `pasta_saida`. Devolve o caminho gravado."""
    if formato not in FORMATOS:
        raise ValueError("formato deve ser: " + ", ".join(FORMATOS))
    ff, fp = ffmpeg, ffprobe
    if not ff or not fp:
        ff, fp = P.find_binaries(BASE)
    if not ff or not fp:
        raise RuntimeError("ffmpeg/ffprobe não encontrados. Coloque ffmpeg.exe e ffprobe.exe na pasta bin.")
    entrada = str(Path(entrada))
    if not Path(entrada).is_file():
        raise FileNotFoundError(entrada)

    over = dict(ajustes or {})
    over.update(bg_mode=FORMATOS[formato], mod_chroma=True, mod_grade=False, mod_upscale=False,
                mod_audio=False, denoise=over.get("denoise", "off"))
    s = P.clean_settings(over)
    info = P.probe(fp, entrada)
    out_dir = Path(pasta_saida)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = P.unique_output(out_dir, entrada, P.output_kind(s))
    cmd = P.build_command(ff, entrada, s, info, str(out), preview=False)
    code, tail = P.run_ffmpeg(cmd, info["duration"], progresso)
    if code != 0:
        raise RuntimeError("O ffmpeg falhou:\n" + tail)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Recorta o fundo verde e grava o arquivo final.")
    ap.add_argument("entrada")
    ap.add_argument("pasta_saida")
    ap.add_argument("--formato", choices=list(FORMATOS), default="prores")
    a = ap.parse_args()

    def mostra(pct: float, speed: str, _done: float) -> None:
        print(f"\r{pct:5.1f}%  {speed}", end="", flush=True)

    try:
        print("Gravado em:", recortar(a.entrada, a.pasta_saida, a.formato, progresso=mostra))
    except Exception as e:  # noqa: BLE001
        print("\nErro:", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
