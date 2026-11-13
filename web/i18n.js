"use strict";
// Pascal — tradução leve PT/EN.
// O HTML e o app.js continuam em português (é a língua-base). Quando o idioma é inglês, este arquivo troca os textos na tela:
//   - texto exato -> PAIRS (português, inglês);
//   - texto com números ou que vem do servidor -> RX (expressão, tradução);
//   - bloco com marcas (negrito, código) -> atributo data-en no próprio HTML.
// O que não estiver aqui simplesmente fica em português. Os relatórios técnicos (pasta logs) não são traduzidos.
(function () {
  const PAIRS = [
    // ---- cabeçalho e passo 1
    ["Pascal, o camaleão", "Pascal, the chameleon"],
    ["◧ Painel", "◧ Panel"],
    ["Esconde ou mostra o painel da esquerda para dar mais espaço ao vídeo", "Hides or shows the left panel to give the video more room"],
    ["Ajuda e perguntas", "Help & FAQ"],
    ["Fechar programa", "Close program"],
    ["Fecha o programa", "Closes the program"],
    ["Escolha o vídeo", "Choose the video"],
    ["Cole o caminho do vídeo ou clique em Escolher", "Paste the video path or click Choose"],
    ["Escolher…", "Choose…"],
    ["Nenhum vídeo escolhido.", "No video chosen."],
    ["— ou escolha um vídeo da pasta input —", "— or pick a video from the input folder —"],
    // ---- passo 2
    ["O que o Pascal faz", "What Pascal does"],
    ["Recortar o fundo verde", "Cut out the green background"],
    ["tira o verde e deixa só a pessoa", "removes the green and keeps only the person"],
    ["Fundo transparente", "Transparent background"],
    ["arquivo .MOV para o Premiere (sem isto, o fundo é preto de estúdio)", ".MOV file for Premiere (without this, the background is studio black)"],
    ["Luz e cor de estúdio", "Studio light and color"],
    ["tom quente, brilho do rosto e contraste", "warm tone, face brightness and contrast"],
    ["Nitidez e tamanho Full HD", "Sharpness and Full HD size"],
    ["sempre 1080p, vídeo vertical ou horizontal", "always 1080p, vertical or horizontal video"],
    ["Áudio de estúdio", "Studio audio"],
    ["só ajusta o volume (mexer mais piora o som)", "only adjusts the volume (doing more makes the sound worse)"],
    // ---- passo 3
    ["Onde salvar", "Where to save"],
    ["Escolher pasta…", "Choose folder…"],
    ["Abrir pasta", "Open folder"],
    ["Usar a pasta do próprio vídeo", "Use the video's own folder"],
    ["Se você não escolher, o Pascal salva na mesma pasta do vídeo original.", "If you don't choose one, Pascal saves to the same folder as the original video."],
    ["Digitar o caminho da pasta", "Type the folder path"],
    ["Usar", "Use"],
    // ---- passo 4
    ["Gerar", "Generate"],
    ["Testar 5 segundos", "Test 5 seconds"],
    ["Renderizar o vídeo completo", "Render the full video"],
    ["Cancelar", "Cancel"],
    ["🔒 Enquanto o vídeo é gerado, o Pascal pede ao Windows para não dormir nem desligar. Se você mandar desligar, o Windows avisa que o Pascal está trabalhando.", "🔒 While the video is being generated, Pascal asks Windows not to sleep or shut down. If you tell Windows to shut down, it warns you that Pascal is working."],
    // ---- ajustes salvos e rodapé
    ["Meus ajustes salvos", "My saved settings"],
    ["Voltar ao padrão Pascal", "Back to Pascal defaults"],
    ["nome do meu ajuste", "name of my setting"],
    ["Salvar", "Save"],
    ["Abrir", "Open"],
    ["Baixar .json", "Download .json"],
    ["Abrir .json", "Open .json"],
    // (o slogan do topo e a assinatura do rodapé são sempre em inglês: ficam direto no HTML, sem tradução)
    // ---- visualizador
    ["Quadro ao vivo", "Live frame"],
    ["Vídeo de teste", "Test video"],
    ["Dividido", "Split"],
    ["Tela", "Fit"],
    ["Cor de fundo por trás da pessoa (só aparece quando a saída é transparente)", "Background color behind the person (only shows when the output is transparent)"],
    ["Fundo", "Background"],
    ["Preto", "Black"], ["Grafite", "Graphite"], ["Cinza", "Gray"], ["Branco", "White"], ["Azul", "Blue"], ["Verde", "Green"],
    ["Vermelho", "Red"], ["Âmbar", "Amber"], ["Xadrez", "Checkerboard"],
    ["Escolher qualquer outra cor", "Pick any other color"],
    ["Tela cheia (tecla F)", "Full screen (F key)"],
    ["⛶ Tela cheia", "⛶ Full screen"],
    ["✕ Sair da tela cheia", "✕ Exit full screen"],
    ["Escolha um vídeo para ver o quadro aqui.", "Choose a video to see the frame here."],
    ["Atualizando…", "Updating…"],
    ["Preparando o quadro…", "Preparing the frame…"],
    ["Role o mouse para dar zoom · arraste para mover", "Scroll the mouse to zoom · drag to move"],
    ["Quadro:", "Frame:"],
    ["Original (para comparar)", "Original (to compare)"],
    ["troca imagem e som, no mesmo ponto", "switches picture and sound, at the same point"],
    ["Abrir pasta de relatórios", "Open reports folder"],
    ["Relatório do teste", "Test report"],
    ["Arraste para aumentar ou diminuir o vídeo. Dois cliques escondem ou mostram os ajustes.", "Drag to make the video bigger or smaller. Double-click hides or shows the settings."],
    ["Ajustes", "Settings"],
    ["tudo muda no quadro ao vivo, na hora", "everything changes in the live frame, instantly"],
    ["▾ Esconder ajustes", "▾ Hide settings"],
    ["▴ Mostrar ajustes", "▴ Show settings"],
    ["Esconde os ajustes para o vídeo ocupar tudo", "Hides the settings so the video fills everything"],
    ["Dê dois cliques para voltar ao valor padrão", "Double-click to return to the default value"],
    // ---- ajuda
    ["Perguntas frequentes", "FAQ"],
    ["Passo a passo", "Step by step"],
    ["Fechar ✕", "Close ✕"],
    ["Carregando…", "Loading…"],
    ["Não consegui abrir o texto de ajuda.", "Couldn't open the help text."],
    // ---- abas e controles
    ["⭐ Essencial", "⭐ Essentials"],
    ["Recorte e fundo", "Cutout and background"],
    ["Luz e cor", "Light and color"],
    ["Nitidez e tamanho", "Sharpness and size"],
    ["Áudio", "Audio"],
    ["Automático", "Automatic"],
    ["Medir agora", "Measure now"],

    ["Modo de saída do fundo", "Background output mode"],
    ["Fundo Preto de Estúdio (.MP4)", "Studio Black Background (.MP4)"],
    ["Fundo Transparente para Premiere (.MOV ProRes 4444)", "Transparent Background for Premiere (.MOV ProRes 4444)"],
    ["Fundo Transparente Leve (.MOV QTRLE)", "Light Transparent Background (.MOV QTRLE)"],
    ["ProRes 4444 é o melhor para o Premiere; QTRLE gera arquivo menor.", "ProRes 4444 is the best for Premiere; QTRLE makes a smaller file."],
    ["Estilo do fundo de estúdio (modo MP4)", "Studio background style (MP4 mode)"],
    ["Preto de estúdio liso (natural, recomendado)", "Plain studio black (natural, recommended)"],
    ["Preto com feixe de luz diagonal (estilo do alvo)", "Black with a diagonal light beam (target style)"],
    ["Preto com brilho suave atrás da pessoa (pode parecer auréola)", "Black with a soft glow behind the person (may look like a halo)"],
    ["Só vale quando a saída é MP4 com fundo de estúdio.", "Only applies when the output is MP4 with a studio background."],
    ["Motor de recorte", "Cutout engine"],
    ["Recorte avançado — cabelo natural, fio a fio (mais lento)", "Advanced cutout — natural hair, strand by strand (slower)"],
    ["Recorte clássico (rápido)", "Classic cutout (fast)"],
    ["Reconhece a pessoa quadro a quadro e recorta o cabelo fio a fio, sem depender da cor do fundo. Leva de 0,2 a 1 segundo por quadro. Se este recurso não estiver completo nesta cópia, o Pascal usa o recorte clássico e avisa.", "Recognizes the person frame by frame and cuts out the hair strand by strand, without relying on the background color. Takes 0.2 to 1 second per frame. If this feature isn't complete in this copy, Pascal uses the classic cutout and warns you."],
    ["Estilo da borda do cabelo", "Hair edge style"],
    ["Simples (novo): contorno limpo e cabelo escuro sem buracos", "Simple (new): clean outline and dark hair without holes"],
    ["Por partes do corpo (versão anterior)", "By body part (previous version)"],
    ["Troque e compare no quadro ao vivo (leva 1 a 2 segundos). Nos dois estilos o vídeo final segura as piscadas claras do cabelo.", "Switch and compare in the live frame (takes 1 to 2 seconds). In both styles the final video holds back the light flickers in the hair."],
    ["Recorte: cor original na borda do cabelo", "Cutout: original color on the hair edge"],
    ["0 = cor estimada pelo recorte (fios mais marcados, risco de tom oliva); 1 = cor do vídeo (contorno mais liso). Padrão 0,3.", "0 = color estimated by the cutout (more defined strands, risk of an olive tint); 1 = video color (smoother outline). Default 0.3."],
    ["Recorte: força do tira-verde", "Cutout: green-removal strength"],
    ["Tira o verde que sobra nas pontas do cabelo e em sombras. Não mexe em pele nem em roupa clara.", "Removes the green left on hair tips and in shadows. Doesn't touch skin or light clothing."],
    ["Cor do verde (chroma)", "Green color (chroma)"],
    ["Automático mede o verde de cada vídeo (recomendado). Desmarque para escolher uma cor.", "Automatic measures the green of each video (recommended). Uncheck to pick a color."],
    ["Similaridade", "Similarity"],
    ["Quanto some. Sobe se sobrar verde no fundo; desce se o sujeito ficar furado ou transparente.", "How much disappears. Raise it if green is left in the background; lower it if the subject gets holes or turns transparent."],
    ["Suavidade da borda", "Edge softness"],
    ["Transição suave entre o que some e o que fica.", "Smooth transition between what disappears and what stays."],
    ["Remoção de reflexo verde", "Green spill removal"],
    ["Age só na faixa estreita da borda. O rosto e a roupa não são tocados.", "Works only on the narrow edge band. The face and clothing are not touched."],
    ["Tirar verde do cabelo e das sombras verdes", "Remove green from hair and green shadows"],
    ["Neutraliza o tom esverdeado do cabelo (reflexo do fundo). A pele e a roupa clara/oliva não são tocadas. 0 desliga.", "Neutralizes the greenish tint of the hair (reflection of the background). Skin and light/olive clothing are not touched. 0 turns it off."],
    ["Sombra na borda do cabelo", "Shadow on the hair edge"],
    ["Escurece em degradê só o contorno (cabelo e ombros): some a bordinha clara. 0 desliga.", "Darkens only the outline (hair and shoulders) with a gradient: the light edge disappears. 0 turns it off."],
    ["Suavidade do contorno", "Outline softness"],
    ["Degradê de transparência na ponta do cabelo: menos \"recortado\". 0 = bem definido.", "Transparency gradient at the hair tips: less \"cut out\". 0 = sharply defined."],
    ["Apagar pontinhos claros no cabelo", "Erase light specks in the hair"],
    ["Escurece pixels claros soltos no meio do cabelo (entregam o chroma key). 0 desliga.", "Darkens stray light pixels in the middle of the hair (they give away the chroma key). 0 turns it off."],
    ["Largura da faixa de borda", "Edge band width"],
    ["Quão larga é a faixa onde o reflexo verde é corrigido (cabelo fino pede mais).", "How wide the band is where green spill is corrected (fine hair needs more)."],
    ["Encolher / limpar borda (choke)", "Shrink / clean edge (choke)"],
    ["Remove a linha verde fina ao redor de ombros e cabelo.", "Removes the thin green line around shoulders and hair."],
    ["Apagar o que estiver ligado às bordas do quadro (parede, caixa, rebatedor, suporte)", "Erase anything attached to the frame edges (wall, box, reflector, stand)"],
    ["Só apaga o que encosta nas laterais ou no topo. A pessoa não é tocada.", "Only erases what touches the sides or the top. The person is not touched."],
    ["Descartar itens isolados (microfone, suporte)", "Discard isolated items (microphone, stand)"],
    ["Apaga objetos finos soltos no quadro. Se sumirem dedos ou fios de cabelo, diminua. 0 desliga.", "Erases thin loose objects in the frame. If fingers or hair strands disappear, lower it. 0 turns it off."],
    ["Descartar cantos do quadro", "Discard frame corners"],
    ["Apaga uma faixa nas laterais e no topo (onde costumam aparecer suportes). A parte de baixo não é tocada.", "Erases a strip on the sides and top (where stands usually appear). The bottom is not touched."],

    ["Exposição automática (mede o rosto e ajusta o brilho)", "Automatic exposure (measures the face and adjusts the brightness)"],
    ["Luz de estúdio no sujeito", "Studio light on the subject"],
    ["Dá volume: um lado do corpo e a parte de baixo ficam mais escuros, o rosto fica em destaque. 0 desliga.", "Adds volume: one side of the body and the lower part get darker, and the face stands out. 0 turns it off."],
    ["Lado de onde vem a luz principal", "Side the main light comes from"],
    ["Esquerda (sombra à direita)", "Left (shadow on the right)"],
    ["Direita (sombra à esquerda)", "Right (shadow on the left)"],
    ["Luz de recorte (contorno)", "Rim light (outline)"],
    ["Brilho fino no contorno do lado oposto à luz. Se parecer artificial, deixe em 0.", "Thin glow on the outline, on the side opposite the light. If it looks artificial, leave it at 0."],
    ["Temperatura / aquecimento", "Temperature / warmth"],
    ["Tira o aspecto branco/azulado de escritório.", "Removes the white/bluish office look."],
    ["Contraste de estúdio", "Studio contrast"],
    ["Sombras (gamma)", "Shadows (gamma)"],
    ["Ajuste fino somado à exposição automática. Abaixo de 1 escurece.", "Fine adjustment added to the automatic exposure. Below 1 darkens."],
    ["Brilho geral", "Overall brightness"],
    ["Saturação de pele", "Skin saturation"],
    ["Brilho superior / highlights", "Upper brightness / highlights"],
    ["Ganho leve nos tons altos, sem estourar.", "Slight gain in the highlights, without blowing them out."],
    ["Densidade do preto (anti-lavado)", "Black density (anti-washed-out)"],
    ["Ancora o preto: cabelo e sombras ficam densos. Só escurece o preto; não clareia nada. 0 desliga.", "Anchors the black: hair and shadows get dense. Only darkens the black; never brightens anything. 0 turns it off."],
    ["Preto menos preto (níveis)", "Less-black black (levels)"],
    ["Levanta o preto do sujeito (cabelo) sem clarear o fundo. Como o \"níveis de saída\" do Photoshop.", "Lifts the subject's black (hair) without brightening the background. Like Photoshop's \"output levels\"."],
    ["Branco menos branco (níveis)", "Less-white white (levels)"],
    ["Abaixa o branco do sujeito.", "Lowers the subject's white."],
    ["Grão fino de cinema", "Fine cinema grain"],
    ["Evita faixas no fundo escuro. 0 desliga.", "Prevents banding in the dark background. 0 turns it off."],

    ["Resolução final", "Final resolution"],
    ["1080p Full HD (vertical ou horizontal)", "1080p Full HD (vertical or horizontal)"],
    ["Manter o tamanho original", "Keep the original size"],
    ["O sistema trabalha sempre em 1080p: o lado menor fica com 1080 px (1920x1080 na horizontal, 1080x1920 na vertical). Não existe 4K.", "The system always works at 1080p: the shorter side is 1080 px (1920x1080 horizontal, 1080x1920 vertical). There is no 4K."],
    ["Motor de upscaling", "Upscaling engine"],
    ["Rápido FFmpeg (lanczos + CAS + micro-nitidez)", "Fast FFmpeg (lanczos + CAS + micro-sharpness)"],
    ["Ampliação avançada — qualidade máxima, MUITO lenta", "Advanced upscaling — maximum quality, VERY slow"],
    ["A ampliação avançada só vale para saída MP4 (fundo de estúdio). Se este recurso não estiver completo nesta cópia, o Pascal usa o modo Rápido e avisa.", "Advanced upscaling only applies to MP4 output (studio background). If this feature isn't complete in this copy, Pascal uses Fast mode and warns you."],
    ["Estilo da ampliação avançada", "Advanced upscaling style"],
    ["Rápido (tende a alisar a pele — use a mistura)", "Fast (tends to smooth the skin — use the blend)"],
    ["Natural (foto real, mais fiel, bem mais lento)", "Natural (real photo, more faithful, much slower)"],
    ["Mistura da ampliação avançada", "Advanced upscaling blend"],
    ["Quanto da ampliação avançada entra no resultado; o resto é o original ampliado pelo modo Rápido. 60% devolve fios de cabelo, cílios e tecido sem a cara de plástico.", "How much of the advanced upscaling goes into the result; the rest is the original enlarged by Fast mode. 60% brings back hair strands, eyelashes and fabric without the plastic look."],
    ["Pegada / contraste local", "Punch / local contrast"],
    ["Realça textura e volume (tecido, cabelo, pele). Alto demais cria halos.", "Enhances texture and volume (fabric, hair, skin). Too high creates halos."],
    ["Tipo de nitidez", "Sharpening type"],
    ["CAS (adaptativa)", "CAS (adaptive)"],
    ["Unsharp (clássica)", "Unsharp (classic)"],
    ["Nitidez", "Sharpness"],
    ["0,45 melhora a definição sem ficar artificial.", "0.45 improves definition without looking artificial."],
    ["Redução de ruído de imagem", "Image noise reduction"],
    ["Desligada", "Off"], ["Leve", "Light"], ["Média", "Medium"], ["Forte", "Strong"],
    ["Roda antes do recorte: deixa a borda do recorte estável.", "Runs before the cutout: keeps the cutout edge stable."],

    ["Redução de ruído de fundo", "Background noise reduction"],
    ["Tira o chiado e o ruído constante da sala (filtro de wavelets). 0 desliga.", "Removes hiss and constant room noise (wavelet filter). 0 turns it off."],
    ["Reduzir eco / cauda de sala entre as palavras", "Reduce echo / room tail between words"],
    ["Intensidade da redução de eco", "Echo reduction strength"],
    ["Quanto mais alto, mais o som fraco entre as palavras (onde fica o eco) é abafado.", "The higher it is, the more the faint sound between words (where the echo sits) is muffled."],
    ["Corte de graves (rumble)", "Low cut (rumble)"],
    ["Corte de agudos (chiado)", "High cut (hiss)"],
    ["Corpo da voz (180 Hz)", "Voice body (180 Hz)"],
    ["Tirar som de sala pequena (380 Hz)", "Remove small-room sound (380 Hz)"],
    ["Presença e clareza (3,5 kHz)", "Presence and clarity (3.5 kHz)"],
    ["Brilho / ar (9 kHz)", "Brightness / air (9 kHz)"],
    ["Compressor dinâmico (nivela a voz)", "Dynamic compressor (evens out the voice)"],
    ["Normalizar volume (padrão broadcast)", "Normalize volume (broadcast standard)"],
    ["Volume final (LUFS)", "Final volume (LUFS)"],
    ["-14 é o padrão de internet; -16 é mais suave.", "-14 is the internet standard; -16 is softer."],

    // ---- ampliação avançada (caixa na aba Nitidez)
    ["A ampliação avançada não está instalada nesta cópia do Pascal. O modo Rápido será usado e já dá um bom resultado.", "Advanced upscaling isn't installed in this copy of Pascal. Fast mode will be used and already gives a good result."],
    ["Testar em 3 quadros", "Test on 3 frames"],
    ["Estimar o tempo do render", "Estimate render time"],
    ["Medindo a velocidade da sua placa (na primeira vez leva cerca de 1 minuto)…", "Measuring your graphics card speed (the first time takes about 1 minute)…"],
    ["Estimando o tempo da ampliação avançada…", "Estimating the advanced upscaling time…"],
    ["Processando 3 quadros…", "Processing 3 frames…"],
    ["Falhou.", "Failed."],

    // ---- mensagens da tela
    ["Escolha o vídeo primeiro.", "Choose the video first."],
    ["Digite um nome para o ajuste.", "Type a name for the setting."],
    ["Arquivo de ajustes inválido.", "Invalid settings file."],
    ["Fechar o Pascal?", "Close Pascal?"],
    ["Preparando…", "Preparing…"],
    ["Cancelado.", "Cancelled."],
    ["Abrir a pasta", "Open the folder"],
    ["Pronto!", "Done!"],
    ["Aguardando o teste/render terminar…", "Waiting for the test/render to finish…"],
    ["Não consegui carregar o quadro.", "Couldn't load the frame."],
    ["Não consegui abrir a janela de escolha. Cole o caminho do vídeo no campo ao lado.", "Couldn't open the chooser window. Paste the video path in the field next to it."],
    ["Não consegui abrir a janela de escolha. Digite o caminho em 'Digitar o caminho da pasta'.", "Couldn't open the chooser window. Type the path under 'Type the folder path'."],
    ["O Pascal parou de responder (foi fechado). Feche esta janela e abra o Iniciar_Pascal.bat de novo.", "Pascal stopped responding (it was closed). Close this window and open Iniciar_Pascal.bat again."],
    ["Fundo transparente: escolha a cor de fundo nos quadradinhos (ou em “colorido”) para ver o contorno do cabelo e dos ombros em cada cor.", "Transparent background: pick the background color in the swatches (or the color wheel) to see the outline of the hair and shoulders on each color."],
    ["Diagnóstico automático: sem alertas.", "Automatic diagnosis: no alerts."],
    ["Relatório do teste: sem alertas (clique para ver)", "Test report: no alerts (click to see)"],
    ["(vazio)", "(empty)"],
    ["O ProRes 4444 com transparência gera arquivos MUITO grandes (cerca de 2,5 GB por minuto de vídeo). Continuar?", "ProRes 4444 with transparency makes VERY large files (about 2.5 GB per minute of video). Continue?"],
    ["Vai usar o modo Rápido FFmpeg.", "It will use the Fast FFmpeg mode."],

    // ---- mensagens que vêm do servidor
    ["Processando…", "Processing…"],
    ["Analisando o resultado…", "Analyzing the result…"],
    ["Recortando a pessoa (recorte avançado)… leva alguns minutos por minuto de vídeo", "Cutting out the person (advanced cutout)… takes a few minutes per minute of video"],
    ["Aplicando cor, luz e fundo…", "Applying color, light and background…"],
    ["Medindo o vídeo (verde, luz, ruído de sala)…", "Measuring the video (green, light, room noise)…"],
    ["Salvando a amostra na pasta de destino…", "Saving the sample to the destination folder…"],
    ["Gerando o original para comparar…", "Generating the original to compare…"],
    ["Analisando o áudio…", "Analyzing the audio…"],
    ["Gravando quadros de comparação…", "Saving comparison frames…"],
    ["Gerando 3 quadros com a ampliação avançada…", "Generating 3 frames with advanced upscaling…"],
    ["Recortando este quadro… (cerca de 30 s; depois os ajustes são instantâneos)", "Cutting out this frame… (about 30 s; after that the adjustments are instant)"],
    ["Recortando este quadro… (cerca de 30 s)", "Cutting out this frame… (about 30 s)"],
    ["Refazendo a borda do recorte…", "Redoing the cutout edge…"],
    ["Arquivo não encontrado. Confira o caminho.", "File not found. Check the path."],
    ["ffprobe.exe não encontrado na pasta bin.", "ffprobe.exe not found in the bin folder."],
    ["ffmpeg.exe / ffprobe.exe não encontrados na pasta bin.", "ffmpeg.exe / ffprobe.exe not found in the bin folder."],
    ["Não achei verde nas bordas da imagem nesse ponto do vídeo.", "I couldn't find green on the image edges at this point of the video."],
    ["Já existe um trabalho rodando. Espere terminar ou cancele.", "A job is already running. Wait for it to finish or cancel it."],
    ["Já existe um trabalho rodando.", "A job is already running."],
    ["Digite o caminho da pasta.", "Type the folder path."],
    ["Um preview ou render está rodando; o quadro ao vivo volta quando terminar.", "A test or render is running; the live frame comes back when it finishes."],
    ["Não consegui ler o quadro do vídeo.", "Couldn't read the frame from the video."],
    ["A ampliação avançada não está instalada nesta cópia do Pascal. Enquanto isso o Pascal usa o modo Rápido, que já dá um bom resultado.", "Advanced upscaling isn't installed in this copy of Pascal. Meanwhile Pascal uses Fast mode, which already gives a good result."],
    ["O PowerShell não está disponível neste computador.", "PowerShell isn't available on this computer."],
    // ---- verificação da instalação e quadro de prévia
    ["Verificar instalação", "Check installation"],
    ["Ver detalhes", "See details"],
    ["O Pascal encontrou um problema nesta cópia:", "Pascal found a problem with this copy:"],
    ["Montando a prévia rápida…", "Building the quick preview…"],
    ["Prévia rápida (recorte clássico). O recorte avançado está em andamento; em computadores mais lentos pode levar alguns minutos.", "Quick preview (classic cutout). The advanced cutout is in progress; on slower computers it can take a few minutes."],
    ["Dica: em Ajuda e perguntas → Verificar instalação o Pascal mostra o que está faltando neste computador.", "Tip: Help & FAQ → Check installation shows what is missing on this computer."],
    ["Verificando…", "Checking…"],
    ["A verificação demorou demais. Tente de novo.", "The check took too long. Try again."],
    ["Copiar relatório", "Copy report"],
    ["Relatório copiado.", "Report copied."],
    ["Selecione o texto abaixo e copie.", "Select the text below and copy it."],
    ["Verificar de novo", "Check again"],
    ["Desbloquear arquivos", "Unblock files"],
    ["Desbloqueando…", "Unblocking…"],
    ["Relatório em texto", "Report as text"],
    ["ÁUDIO AUSENTE: o arquivo gerado não tem áudio legível.", "AUDIO MISSING: the generated file has no readable audio."],
    ["RUÍDO NÃO REDUZIDO: não achei uma pausa de silêncio de sala neste vídeo/trecho. Escolha um início de teste com uma pausa (ou grave 2 s de silêncio no começo).", "NOISE NOT REDUCED: I couldn't find a pause of room silence in this video/section. Pick a test start with a pause (or record 2 s of silence at the beginning)."],
    ["Não consegui salvar a amostra na pasta de destino (a pasta não aceita gravação).", "Couldn't save the sample to the destination folder (the folder doesn't accept writing)."],
  ];

  const EN = Object.create(null);
  PAIRS.forEach(([pt, en]) => { EN[pt] = en; });

  // Textos com números ou montados pelo programa/servidor. Cada item: [expressão que casa o texto inteiro, função ou modelo].
  let tt;   // definida abaixo
  const RX = [
    [/^(\d+)% — (.*?)( \([^)]*\))?$/s, (m, p, msg, sp) => p + "% — " + tt(msg) + (sp || "")],
    [/^(⚠ )([\s\S]+)$/, (m, a, b) => a + tt(b)],
    [/^Processando… faltam cerca de (.+)$/, "Processing… about $1 left"],
    [/^Erro (\d+)$/, "Error $1"],
    [/^(\d+×\d+) · (\d+),(\d+) fps · (.+) · com áudio$/, "$1 · $2.$3 fps · $4 · with audio"],
    [/^(\d+×\d+) · (\d+),(\d+) fps · (.+) · sem áudio$/, "$1 · $2.$3 fps · $4 · no audio"],
    [/^Amostra de 5 segundos salva em:\n([\s\S]*)$/, "5-second sample saved to:\n$1"],
    [/^Pronto! O vídeo foi salvo em:\n([\s\S]*)$/, "Done! The video was saved to:\n$1"],
    [/^O FFmpeg falhou:\n([\s\S]*)$/, "FFmpeg failed:\n$1"],
    [/^Relatório do teste: (\d+) aviso\(s\) — clique para ver$/, "Test report: $1 warning(s) — click to see"],
    [/^Relatório completo \(também salvo em (.*)\)$/, "Full report (also saved in $1)"],
    [/^Ampliação avançada disponível(?: · placa de vídeo: (.*?))?\. Estimativa de tempo e teste em 3 quadros abaixo\.$/, (m, g) => "Advanced upscaling available" + (g ? " · graphics card: " + g : "") + ". Time estimate and 3-frame test below."],
    [/^≈ ([\d.]+) s por quadro · (\d+) quadros · render completo ≈ (.*)\.$/, "≈ $1 s per frame · $2 frames · full render ≈ $3."],
    [/^Render com ampliação avançada: cerca de ([\d.]+) s por quadro × (\d+) quadros = (.*)\. Continuar\?$/, "Render with advanced upscaling: about $1 s per frame × $2 frames = $3. Continue?"],
    [/^(.*)\n\nVai usar o modo Rápido FFmpeg\.$/, (m, a) => tt(a) + "\n\nIt will use the Fast FFmpeg mode."],
    [/^Erro ao iniciar: (.*)$/, (m, a) => "Error starting: " + tt(a)],
    [/^([\s\S]*?)\n\n(Dica: em Ajuda e perguntas → Verificar instalação o Pascal mostra o que está faltando neste computador\.)$/, (m, a, b) => tt(a) + "\n\n" + tt(b)],
    [/^O Windows não abriu a janela de escolha([\s\S]*)$/, "Windows didn't open the chooser window$1"],
    [/^O recorte avançado não está disponível neste computador; usei o recorte clássico \(mais rápido, menos natural no cabelo\)\. Motivo: ([\s\S]*)$/,
      (m, r) => "The advanced cutout isn't available on this computer; I used the classic cutout (faster, less natural on hair). Reason: " +
        r.replace("nenhum Python com numpy + onnxruntime encontrado", "no Python with numpy + onnxruntime found").replace("modelo do RVM ausente em bin\\rvm", "RVM model missing in bin\\rvm")],
    [/^O recorte avançado não funcionou neste computador; o quadro mostra o recorte clássico\. Motivo: ([\s\S]*)$/,
      (m, r) => "The advanced cutout didn't work on this computer; the frame shows the classic cutout. Reason: " +
        r.replace("O recorte avançado do quadro falhou:", "The advanced cutout of the frame failed:").replace("O recorte avançado falhou:", "The advanced cutout failed:")],
    [/^Não consegui usar essa pasta: (.*)$/, "Couldn't use that folder: $1"],
    [/^O FFmpeg não conseguiu montar o quadro: (.*)$/, "FFmpeg couldn't build the frame: $1"],
    // alertas do diagnóstico
    [/^ÁUDIO QUASE MUDO: a fala está em (.+) dBFS \(deveria estar perto de -15\)\.$/, "AUDIO ALMOST SILENT: speech is at $1 dBFS (it should be close to -15)."],
    [/^ÁUDIO: (.+)% do tempo está em silêncio quase total\.$/, "AUDIO: $1% of the time is almost total silence."],
    [/^RUÍDO PIOROU: diferença voz x ruído caiu de (.+) para (.+) dB\.$/, "NOISE GOT WORSE: the voice-to-noise difference dropped from $1 to $2 dB."],
    [/^FALA PICOTADA: (\d+) quedas bruscas de volume \(original: (\d+)\)\. Reduza 'Redução de ruído' e 'Intensidade da redução de eco'\.$/, "CHOPPY SPEECH: $1 sudden volume drops (original: $2). Lower 'Background noise reduction' and 'Echo reduction strength'."],
    [/^CORTE \(clipping\): (\d+) amostras no limite máximo — o som estoura\.$/, "CLIPPING: $1 samples at the maximum limit — the sound distorts."],
    [/^VOLUME FORA DO ALVO: (.+) LUFS \(alvo (.+)\)\.$/, "VOLUME OFF TARGET: $1 LUFS (target $2)."],
    [/^DURAÇÃO DIFERENTE: áudio (.+)s x original (.+)s \(possível perda de sincronia\)\.$/, "DIFFERENT DURATION: audio $1s vs original $2s (possible loss of sync)."],
    [/^O arquivo gerado não abre no ffprobe: (.*)$/, "The generated file doesn't open in ffprobe: $1"],
    [/^TAMANHO FORA DO PADRÃO: origem (\S+), resultado (\S+) \(esperado lado menor = 1080\)\.$/, "SIZE OFF STANDARD: source $1, result $2 (expected shorter side = 1080)."],
    [/^DURAÇÃO DO VÍDEO: (.+)s, esperado (.+)s\.$/, "VIDEO DURATION: $1s, expected $2s."],
    [/^O diagnóstico automático falhou: (.*)$/, "The automatic diagnosis failed: $1"],
    [/^O FFmpeg falhou: (.*)$/, "FFmpeg failed: $1"],
    // número decimal solto (ex.: 0,30  ou  -3,5 dB): ponto em vez de vírgula
    [/^(-?\d+),(\d+)( ?[%A-Za-z]{1,4})?$/, (m, a, b, u) => a + "." + b + (u || "")],
  ];

  let lang = "pt";
  try {
    const v = localStorage.getItem("pascal.lang");
    lang = v === "en" || v === "pt" ? v : (/^pt/i.test(navigator.language || "pt") ? "pt" : "en");
  } catch (e) { lang = /^pt/i.test(navigator.language || "pt") ? "pt" : "en"; }

  // traduz um texto (só faz algo quando o idioma é inglês; sem tradução, devolve o próprio texto)
  tt = function (s) {
    if (lang !== "en" || typeof s !== "string" || !s) return s;
    const core = s.trim();
    if (!core) return s;
    let r = EN[core];
    if (r === undefined) {
      for (const [re, fn] of RX) {
        const m = core.match(re);
        if (m) { r = typeof fn === "string" ? core.replace(re, fn) : fn(...m); break; }
      }
    }
    return r === undefined ? s : s.replace(core, () => r);
  };

  // ---- troca dos textos na tela (guarda o original em português para poder voltar)
  const ATTRS = ["title", "placeholder", "alt", "aria-label"];
  const textRec = new WeakMap();   // nó de texto -> {pt, cur}
  const attrRec = new WeakMap();   // elemento -> {atributo: {pt, cur}}

  function skip(n) {
    const p = n.parentElement;
    return !p || !!p.closest("script,style,textarea,#docBody,#report pre,[data-en]");
  }
  function doText(n) {
    if (skip(n)) return;
    const r = textRec.get(n);
    const pt = r && n.nodeValue === r.cur ? r.pt : n.nodeValue;
    const cur = lang === "en" ? tt(pt) : pt;
    if (n.nodeValue !== cur) n.nodeValue = cur;
    if (cur !== pt || r) textRec.set(n, { pt, cur });
  }
  function doAttrs(el) {
    for (const a of ATTRS) {
      if (!el.hasAttribute(a)) continue;
      const m = attrRec.get(el) || {};
      const r = m[a];
      const v = el.getAttribute(a);
      const pt = r && v === r.cur ? r.pt : v;
      const cur = lang === "en" ? tt(pt) : pt;
      if (v !== cur) el.setAttribute(a, cur);
      if (cur !== pt || r) { m[a] = { pt, cur }; attrRec.set(el, m); }
    }
  }
  function doBlock(el) {
    if (el.__lang === undefined) { el.__ptHtml = el.innerHTML; el.__lang = "pt"; }
    if (el.__lang === lang) return;
    el.innerHTML = lang === "en" ? el.getAttribute("data-en") : el.__ptHtml;
    el.__lang = lang;
  }
  function apply(root) {
    root = root || document.body;
    if (root.nodeType === 3) { doText(root); return; }
    if (root.nodeType !== 1) return;
    if (root.matches("[data-en]")) doBlock(root);
    root.querySelectorAll("[data-en]").forEach(doBlock);
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const list = [];
    while (w.nextNode()) list.push(w.currentNode);
    list.forEach(doText);
    doAttrs(root);
    root.querySelectorAll("[title],[placeholder],[alt],[aria-label]").forEach(doAttrs);
  }

  // o que o programa cria depois (abas, mensagens, relatório) é traduzido na hora, só quando o idioma é inglês
  new MutationObserver((muts) => {
    if (lang !== "en") return;
    for (const m of muts) {
      if (m.type === "childList") m.addedNodes.forEach((n) => apply(n));
      else if (m.type === "characterData") doText(m.target);
      else if (m.type === "attributes") doAttrs(m.target);
    }
  }).observe(document.documentElement, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS });

  function show(save) {
    document.documentElement.lang = lang === "en" ? "en" : "pt-BR";
    document.querySelectorAll("#langSeg button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
    apply(document.body);
    if (save) {
      try { localStorage.setItem("pascal.lang", lang); } catch (e) { /* ignora */ }
      window.dispatchEvent(new Event("pascal-lang"));
    }
  }
  function set(l) { if ((l === "pt" || l === "en") && l !== lang) { lang = l; show(true); } }

  window.I18N = { tr: (s) => tt(s), set, get lang() { return lang; }, apply, EN, RX };
  document.querySelectorAll("#langSeg button").forEach((b) => { b.onclick = () => set(b.dataset.lang); });
  show(false);
})();
