# Third-party software

Pascal itself is licensed under the GNU General Public License v3 (see `LICENSE`).
The ready-to-run `Pascal.zip` also carries the programs below, **unmodified**, each under its own license.
Where a license requires it, the place to get the corresponding source code is given.

| Component | Where it lives | License | Source / project page |
|---|---|---|---|
| **FFmpeg** (build "essentials" from gyan.dev: `ffmpeg.exe`, `ffprobe.exe`) | `bin\` | GNU GPL v3 (the build is configured with `--enable-gpl --enable-version3`) | FFmpeg source: https://ffmpeg.org/download.html — build and source information: https://www.gyan.dev/ffmpeg/builds/ |
| **Robust Video Matting** — model file `rvm_resnet50_fp32.onnx` | `bin\rvm\` | GNU GPL v3 | https://github.com/PeterL1n/RobustVideoMatting — Shanchuan Lin et al., *Robust High-Resolution Video Matting with Temporal Guidance* (WACV 2022) |
| **Real-ESRGAN ncnn Vulkan** (`realesrgan-ncnn-vulkan.exe` and its models; optional "advanced upscaling") | `bin\realesrgan\` | MIT (program) / BSD-3-Clause (models); see `bin\realesrgan\README_windows.md` | https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan — https://github.com/xinntao/Real-ESRGAN |
| **Python** (Windows embeddable package 3.12) | `python\` | Python Software Foundation License (`python\LICENSE.txt`) | https://www.python.org |
| **NumPy** | `python\Lib\site-packages\numpy` | BSD-3-Clause (license file in the package's `*.dist-info`) | https://numpy.org |
| **ONNX Runtime** | `python\Lib\site-packages\onnxruntime` | MIT (license and third-party notices in the package's `*.dist-info`) | https://github.com/microsoft/onnxruntime |
| ONNX Runtime's own dependencies: **flatbuffers**, **protobuf**, **packaging** | `python\Lib\site-packages` | Apache-2.0 (flatbuffers), BSD-3-Clause (protobuf), Apache-2.0 or BSD-2-Clause (packaging); each package keeps its license in its `*.dist-info` | https://pypi.org/project/flatbuffers/ — https://pypi.org/project/protobuf/ — https://pypi.org/project/packaging/ |
| `vcomp140.dll`, `vcomp140d.dll` (Microsoft Visual C++ OpenMP runtime, needed by the Real-ESRGAN program) | `bin\realesrgan\` | Microsoft redistributable | https://learn.microsoft.com/cpp/windows/redistributing-visual-cpp-files |

If you want to rebuild Pascal from source, the README explains where to download each piece.

If any of the above is missing credit or has the wrong license listed, please open an issue: it will be fixed.
