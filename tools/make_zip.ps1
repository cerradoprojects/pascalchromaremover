# Builds Pascal.zip (the portable folder) next to the repository folder.
# Run it from a folder that already has python\ and bin\ filled in (see the README, "Run from source / build the portable folder").
# Right-click > Run with PowerShell.
$raiz = Split-Path -Parent $PSScriptRoot
$destino = Join-Path (Split-Path -Parent $raiz) "Pascal.zip"
$tmp = Join-Path $env:TEMP "pascal_zip"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Path "$tmp\Pascal" | Out-Null

# not part of the portable folder: repository files, and anything created while using the program
$excluir = @("tools", ".git", ".gitignore", ".gitattributes", "logs", "cache", "input", "output", "presets_usuario", "__pycache__", "pascal_config.json")
Get-ChildItem $raiz -Force | Where-Object { $excluir -notcontains $_.Name } |
    ForEach-Object { Copy-Item $_.FullName "$tmp\Pascal\$($_.Name)" -Recurse -Force }
foreach ($d in @("input", "output", "presets_usuario", "cache", "logs")) { New-Item -ItemType Directory -Path "$tmp\Pascal\$d" | Out-Null }
Get-ChildItem "$tmp\Pascal" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

if (Test-Path $destino) { Remove-Item $destino -Force }
Compress-Archive -Path "$tmp\Pascal" -DestinationPath $destino -CompressionLevel Optimal
Remove-Item $tmp -Recurse -Force
"Done: $destino  ($([math]::Round((Get-Item $destino).Length / 1MB)) MB)"
