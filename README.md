<p align="center">
  <img src="web/pascal.png" alt="Pascal, the chameleon" width="180">
</p>

<h1 align="center">Pascal</h1>

<p align="center">
  <b>A chameleon that fixes your green-screen videos.</b><br>
  Made for low-cost productions, poor illumination and offices pretending to be studios.
</p>

> Made by a lousy developer, so you will probably need to improve it.
> But it's very okay the way it is.

**Free to use, free to improve. Forever.** ([GPL-3.0](LICENSE))

---

## What it does

You filmed someone in an office, in front of a green sheet, under questionable light. Pascal hands back a video that looks like it was shot in a studio:

- **Cutout** — removes the green and keeps the person, hair strands included. Two engines: an advanced one (a neural matting model) and a classic, faster one (plain FFmpeg filters).
- **Studio light and color** — automatic exposure measured on the face, warm tone, contrast, a lighting gradient that gives volume, fine grain.
- **Sharpness and size** — always 1080p (vertical or horizontal), sharpened *after* compositing so the cutout edge doesn't get a halo.
- **Audio** — evens out the volume. That's it. (We tried doing more. It sounded like a bathroom.)
- **Output** — MP4 with a studio black background, or a ProRes 4444 / QTRLE `.mov` with real transparency for Premiere.
- **Live frame** — move any slider and see the result in seconds, with zoom, split view and background colors.
- **Bilingual interface** — Portuguese and English (the **PT | EN** button, top right).
- **Local and portable** — runs from a folder or a USB stick. No installer, no admin rights, no account, no internet. Your video never leaves your computer.
- **Won't let Windows fall asleep on your render** — while a video is being generated it asks Windows not to sleep or shut down.

## Download and run (Windows 10 / 11)

1. Open [**Releases**](https://github.com/cerradoprojects/pascalchromaremover/releases/latest) and download `Pascal.zip` (about 250 MB: it already carries FFmpeg, Python and the cutout model).
2. Right-click the zip → **Extract all**.
3. Double-click `Iniciar_Pascal.bat`.

If Windows says it "protected your PC": **More info → Run anyway**. There is no paid signature, no installer, and nothing touches your system.

The user guide is in [`PASSO_A_PASSO_PASCAL.en.md`](PASSO_A_PASSO_PASCAL.en.md) and [`FAQ_PASCAL.en.md`](FAQ_PASCAL.en.md) (Portuguese: [`PASSO_A_PASSO_PASCAL.md`](PASSO_A_PASSO_PASCAL.md), [`FAQ_PASCAL.md`](FAQ_PASCAL.md)). They also open inside the app, under **Help & FAQ**.

## Honest status

- Tested on a handful of office recordings (Canon cameras, one person on camera, Windows 11, an Intel integrated GPU).
- Barely tested: other cameras, lots of different skin tones and hair types, very long renders, and every possible Premiere setup. It will probably work. *Probably.*
- The advanced cutout takes roughly 0.2–1 second per frame on a regular CPU (a 1-minute video: about 6–30 minutes). Yes, it is slow. Make coffee. Close other heavy programs.
- There is no AI voice cleanup, no 4K, no cloud. On purpose.

## How it works (short version)

1. **Color first.** The video is normalized to BT.709 / limited range, and the person's color **never goes through a chroma key**: one branch only makes the mask, the other keeps the color in 10-bit 4:4:4.
2. **Mask.** *Advanced:* [Robust Video Matting](https://github.com/PeterL1n/RobustVideoMatting) (ONNX Runtime, on the CPU) gives color + alpha per frame; Pascal then cleans the edge: mixes in some of the original color, removes green spill (weighted by how dark/edgy the pixel is), heals holes in dark hair, and runs a small **temporal guard** that holds back 1–3-frame flickers caused by the green light behind the hair strands. *Classic:* soft alpha from "green dominance" (`g − max(r, b)`), a core + edge-band trimap, and spill removal.
3. **Studio look.** Auto exposure (measured on the skin), S-curve, color temperature, a luminance-only lighting gradient, fine grain against banding.
4. **Sharpen after composing.** Otherwise unsharp creates a light halo at the cutout edge.
5. **Audio.** High-pass, noise profile learned from a second of room silence (`afftdn`), soft expander, EQ, soft compressor, two-pass `loudnorm`. By default only the volume is touched.
6. **Logs.** Every test and render writes a folder in `logs/` with a plain-text summary, automatic alerts (muted audio, chopped speech, clipping, wrong duration…), the exact FFmpeg command and side-by-side frames.

Everything is FFmpeg + a local Python web server (`127.0.0.1`, session token) + plain HTML/CSS/JS. No frameworks, no build step.

## Run from source / build the portable folder

You need Windows, Python 3.12, FFmpeg and the cutout model. The final folder looks like this:

```
Pascal\
  Iniciar_Pascal.bat                   <- double-click to open
  Pascal_Arraste_o_Video_Aqui.bat      <- drag a video onto it: transparent .mov comes out
  app.py  pipeline.py  matte_ai.py  matte_worker.py  recorte.py  diag.py  keepawake.py  ...
  web\                                 <- the interface
  python\                              <- Step 1 (portable Python + numpy + onnxruntime)
  bin\                                 <- Step 2 (ffmpeg.exe, ffprobe.exe) and bin\rvm\ (the model)
  input\  output\  presets_usuario\  cache\  logs\     <- created on first run
```

**Step 1 — Python.** Any Python 3.12 with `pip install numpy onnxruntime` works (`python app.py`). For the portable folder, download the *Windows embeddable package (64-bit)* from python.org, extract it into `python\`, put `numpy` and `onnxruntime` inside `python\Lib\site-packages`, and in `python\python312._pth` keep `import site` uncommented and add the line `Lib\site-packages`.

**Step 2 — FFmpeg and the model.**
1. Get `ffmpeg-release-essentials.zip` from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and copy `ffmpeg.exe` and `ffprobe.exe` into `bin\`.
2. Get [`rvm_resnet50_fp32.onnx`](https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50_fp32.onnx) and put it in `bin\rvm\`.
3. *Optional:* [Real-ESRGAN ncnn Vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases) in `bin\realesrgan\` enables the "advanced upscaling" (very slow on integrated graphics; the FFmpeg upscaler is the default and it's fine).

Without the model, Pascal still runs and falls back to the classic cutout, telling you so on screen.

**Make the release zip:** `tools\make_zip.ps1` (PowerShell) builds `Pascal.zip` next to the folder, without logs, caches or personal settings.

## Project map

| File | What it is |
|---|---|
| `app.py` | Local server, jobs, logs, window launcher (Chrome/Edge in `--app` mode) |
| `pipeline.py` | **All the FFmpeg**: settings and validation, probes, video/audio graphs, commands |
| `matte_worker.py` / `matte_ai.py` | Advanced cutout: model, edge cleanup, temporal guard / launcher |
| `diag.py` | Automatic diagnosis and alerts |
| `keepawake.py` | Keeps Windows awake and warns on shutdown while rendering |
| `ai_render.py` / `upscale_ai.py` | Optional advanced upscaling (Real-ESRGAN, in tiles) |
| `recorte.py` | Just the cutout, as a function / command line |
| `web/` | The interface; `web/i18n.js` holds the PT ⇄ EN dictionary |
| `FAQ_PASCAL*.md`, `PASSO_A_PASSO_PASCAL*.md` | User docs, PT and EN (the app reads them) |

Code comments and some docs are in Portuguese. Sorry. (Or: *desculpa*.)

## Contributing

Free to use, free to improve — that's the whole deal. Issues and pull requests are welcome, in English or Portuguese. Good first improvements: other cameras and skin tones, faster cutout, a macOS/Linux launcher, more languages (add a dictionary like the one in `web/i18n.js`), and anything that makes it less "lousy".

## Credits and licenses

Pascal is licensed under the **GNU GPL v3** ([`LICENSE`](LICENSE)). It stands on other people's work, listed with their licenses and where to get the source in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md): FFmpeg, Robust Video Matting, Real-ESRGAN ncnn Vulkan, Python, NumPy and ONNX Runtime.

*Free applications brought to life by a Brasília tuition-free public-university alumnus.* A [Cerrado Projects](https://github.com/cerradoprojects) application.

---

<details>
<summary><b>Português (BR)</b></summary>

**Pascal** é um programa para Windows que transforma gravações feitas na frente de um fundo verde (escritório, luz ruim, orçamento baixo) em vídeo com cara de estúdio: recorta a pessoa (até o fio de cabelo), ajusta luz e cor, melhora a nitidez e nivela o volume do áudio. Roda só no seu computador, sem internet, sem conta e sem instalar nada.

**Como usar:** baixe o `Pascal.zip` em [Releases](https://github.com/cerradoprojects/pascalchromaremover/releases/latest), extraia, dê dois cliques em `Iniciar_Pascal.bat`. O guia completo está em [`PASSO_A_PASSO_PASCAL.md`](PASSO_A_PASSO_PASCAL.md) e as dúvidas comuns em [`FAQ_PASCAL.md`](FAQ_PASCAL.md). O botão **PT | EN**, no alto da janela, troca o idioma.

Foi feito por um desenvolvedor meia-boca, então provavelmente vai precisar de melhorias. Mas do jeito que está já funciona bem. Livre para usar, livre para melhorar. Para sempre.

</details>
