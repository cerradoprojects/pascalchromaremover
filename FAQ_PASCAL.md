# Pascal — perguntas frequentes

## O que é o Pascal?

É um programa para Windows que transforma uma gravação feita na frente de um fundo verde em um vídeo com cara de estúdio. Ele recorta a pessoa, coloca um fundo preto (ou deixa transparente), ajusta luz e cor, melhora a nitidez e nivela o volume do áudio. O nome é de um camaleão, que muda de cor conforme o ambiente.

## Quanto custa? Precisa de internet ou de conta?

Não custa nada, não precisa de conta e funciona sem internet. O vídeo nunca sai do seu computador. A internet só é usada uma vez, para baixar o arquivo zip do Pascal.

## Como baixo e instalo?

1. Baixe o arquivo zip do Pascal pelo link desta página (ou em **Releases**, no GitHub: github.com/cerradoprojects/pascalchromaremover).
2. Clique com o botão direito no zip e escolha **Extrair tudo**. Escolha uma pasta, por exemplo `C:\Pascal`, ou um pendrive.
3. Abra a pasta e dê dois cliques em **Iniciar_Pascal.bat**.

Não há instalação e não é preciso ser administrador. Para desinstalar, apague a pasta.

## O Windows mostrou "O Windows protegeu o computador". O que faço?

Clique em **Mais informações** e depois em **Executar assim mesmo**. O aviso aparece porque o programa não tem assinatura digital paga. O Pascal não instala nada e não altera o sistema.

## Que computador eu preciso?

Windows 10 ou 11, 8 GB de memória e uns 10 GB livres para trabalhar. Não precisa de placa de vídeo. Quanto mais livre estiver o computador, mais rápido o Pascal trabalha.

## Quanto tempo demora?

- **O quadro ao vivo** mostra primeiro, em 2 a 5 segundos, uma prévia rápida (recorte clássico) e depois troca pelo quadro com o recorte avançado: cerca de 30 segundos num computador bom e alguns minutos num computador mais lento (um contador de segundos aparece no alto do vídeo). Depois disso, cada ajuste aparece em 1 a 2 segundos, inclusive os de recorte do cabelo.
- **O teste de 5 segundos** leva de 1 a 5 minutos.
- **O vídeo completo** com recorte avançado leva de 0,2 a 1 segundo por quadro. Um vídeo de 1 minuto pode levar de 6 a 30 minutos, e um de 30 minutos pode levar várias horas. Deixe o computador ligado na tomada e sem outros programas pesados abertos.

## O computador pode dormir ou desligar no meio do vídeo?

Não enquanto o Pascal estiver trabalhando. Durante o teste de 5 segundos e durante o vídeo completo, o Pascal pede ao Windows para não entrar em repouso e para não desligar (a tela pode apagar normalmente). Se alguém mandar desligar ou reiniciar nessa hora, o Windows avisa que o Pascal está gerando um vídeo e deixa a pessoa escolher entre esperar ou desligar assim mesmo (nesse caso o vídeo em andamento é perdido). Quando o vídeo termina, dá erro ou você cancela, a proteção sai sozinha e o computador volta ao comportamento normal. Tem coisas que nenhum programa controla: deixe o notebook na tomada e com a tampa aberta (fechar a tampa pode suspender o notebook, conforme a configuração de energia do Windows) e evite o desligamento forçado.

## Como o Pascal recorta o cabelo tão bem?

O recorte clássico pela cor verde tende a comer fios de cabelo e deixar um contorno esverdeado. O recorte avançado do Pascal reconhece a pessoa quadro a quadro e recorta fio a fio, sem depender só da cor do fundo. Depois o Pascal tira o verde que sobrou nas pontas do cabelo. Tudo roda dentro do seu computador. Se esse recurso não estiver completo na sua cópia, o Pascal usa o recorte clássico e avisa.

## O Pascal envia meu vídeo para algum lugar?

Não. Tudo roda inteiro no seu computador. Nada é enviado para a internet.

## Posso usar vídeo vertical?

Pode. O Pascal reconhece a orientação sozinho e entrega 1080×1920 na vertical ou 1920×1080 na horizontal.

## Por que o vídeo sai sempre em 1080p e nunca em 4K?

Por decisão do projeto: 1080p (Full HD) é o tamanho que atende a quase todo uso, e 4K deixaria tudo muito mais lento sem mostrar mais detalhe, porque a gravação de origem já não tem essa resolução. O lado menor do vídeo fica sempre com 1080 pixels. Existe a opção **Manter o tamanho original**, em **Nitidez e tamanho**.

## Como uso o vídeo no Premiere?

1. Ligue **Fundo transparente** no passo 2.
2. Renderize. O arquivo sai em `.MOV` (ProRes 4444), com transparência.
3. Arraste o arquivo para a linha do tempo do Premiere. Coloque outro fundo na faixa de baixo.

Atenção: esse formato gera arquivos grandes, cerca de 2 GB por minuto.

## O Premiere disse "arquivo não suportado" e abriu só o áudio. E agora?

**Atualize para o Pascal 1.0.6 e gere o vídeo de novo.** A causa encontrada: vídeos de celular (iPhone e Android) gravam com uma taxa de quadros levemente variável (por exemplo 29,997 quadros por segundo) e as versões anteriores do Pascal copiavam esse número quebrado para o `.mov` transparente; o Premiere recusa esse arquivo. Desde a 1.0.6 todo arquivo sai com taxa padrão (29,97, 30, 25, 60…), e no fim de cada vídeo o Pascal confere sozinho se o arquivo abre (o resultado fica no relatório).

Se ainda assim o Premiere não abrir, há duas saídas que abrem em qualquer versão:

**MP4 da pessoa + MP4 da máscara (a mais leve e compatível):**

1. Na aba **Recorte e fundo**, em **Modo de saída do fundo**, escolha **Fundo Transparente — MP4 da pessoa + MP4 da máscara**.
2. Renderize. Saem dois arquivos: `nome_PESSOA.mp4` (a pessoa sobre preto, com o áudio) e `nome_MASCARA.mp4` (branco onde está a pessoa, preto no resto).
3. No Premiere, ponha o fundo que quiser na faixa **V1**, o `_PESSOA.mp4` na **V2** e o `_MASCARA.mp4` na **V3**, alinhados no mesmo ponto.
4. No painel **Efeitos**, procure **Fosco da faixa** (Track Matte Key) e arraste para o clipe `_PESSOA.mp4`.
5. Em **Controles de efeito**, escolha **Fosco: Vídeo 3** e **Composição usando: Luminância fosca**.
6. Clique no olho da faixa **V3** para escondê-la. A pessoa aparece recortada sobre o fundo da V1.

**Sequência de imagens PNG:**

1. Na aba **Recorte e fundo**, em **Modo de saída do fundo**, escolha **Fundo Transparente — sequência de imagens PNG + áudio .WAV**.
2. Renderize. O Pascal cria uma pasta `nome-do-video_ALPHA_PNG` com uma imagem por quadro (com transparência) e o áudio em `.wav`.
3. No Premiere, clique em **Arquivo > Importar** e abra essa pasta.
4. Clique no **primeiro** arquivo `.png`, marque **Sequência de imagens** e clique em **Abrir**.
5. Importe também o arquivo `.wav` da mesma pasta e coloque os dois lado a lado na linha do tempo.

Se a sequência tocar rápida ou lenta demais, clique com o botão direito no clipe, escolha **Modificar > Interpretar gravação** e digite a velocidade do vídeo original (por exemplo, 29,97). A pasta ocupa mais ou menos o mesmo espaço que o ProRes.

## Qual a diferença entre fundo preto e transparente?

Com o fundo preto, o Pascal já entrega o vídeo final em `.MP4`, pronto para publicar. Com o fundo transparente, ele entrega a pessoa recortada em `.MOV`, para você escolher o fundo depois no Premiere.

## Onde ficam os vídeos prontos?

Na pasta que você escolheu no passo 3. Se você não escolheu nenhuma, na mesma pasta do vídeo original (ou na pasta `output` do Pascal, se aquela pasta não aceitar gravação). O botão **Abrir pasta** leva até lá. O Pascal nunca apaga nem substitui o vídeo original.

## O teste de 5 segundos fica salvo?

Sim. Além de tocar na tela, o teste é salvo na pasta de destino como `nome-do-video_sample.mp4`, para você abrir em outro player ou mostrar a alguém. Com o **Fundo transparente** ligado, o arquivo salvo é um `.mp4` comum com a pessoa sobre a cor de fundo escolhida nos quadradinhos (um player comum não entende transparência); a transparência de verdade aparece só na tela do Pascal e no render completo.

Quando termina, aparece onde a amostra foi salva e o botão **Abrir a pasta**, que já mostra o arquivo selecionado. Se a pasta de destino não aceitar o arquivo (pasta protegida ou antivírus da empresa), o Pascal tenta de novo e, se não der, salva na pasta `output` do próprio Pascal e avisa. Se nem isso der certo, aparece em vermelho o motivo: escolha outra pasta no passo 3 (por exemplo, Documentos).

## Como aumento o vídeo na tela?

Arraste a barrinha cinza que fica entre o vídeo e os **Ajustes**: o vídeo cresce e os ajustes diminuem. Dois cliques nela (ou o botão **Esconder ajustes**) escondem os ajustes de vez. O botão **◧ Painel**, no alto, esconde a coluna da esquerda. E o botão **⛶ Tela cheia** (ou a tecla **F**) mostra só o vídeo na tela inteira; **Esc** volta. O Pascal lembra o tamanho que você deixou.

## Dá para dar zoom no vídeo de teste?

Dá. No **Vídeo de teste**, gire a rodinha do mouse sobre o vídeo (ou use os botões **Tela, 100%, 200%, 400%, 800%**) e arraste para mexer; dois cliques voltam para a tela inteira. O vídeo continua tocando ampliado. Um clique toca ou pausa, as setas do teclado (ou **◂ quadro / quadro ▸**) andam um quadro de cada vez e o botão **Original** troca para o vídeo sem tratamento no mesmo ponto e no mesmo zoom.

## Posso ver o fundo transparente em outras cores?

Pode. Com **Fundo transparente** ligado, escolha a cor atrás da pessoa nos quadradinhos de cima do vídeo (preto, grafite, cinza, branco, azul, verde, vermelho, âmbar, xadrez) ou clique no quadradinho colorido para escolher qualquer outra cor. Isso vale para o **Quadro ao vivo** e também para o **teste de 5 segundos**: ele sai com transparência de verdade e você troca a cor de fundo sem refazer o teste. A amostra salva na pasta (`_sample.mp4`) usa a cor que estava escolhida quando você gerou o teste.

## O teste de 5 segundos terminou, mas o vídeo não toca na tela. O que faço?

O Pascal tenta de novo sozinho e, no teste com fundo transparente, troca para a versão em `.mp4`. Se mesmo assim não tocar (acontece em computadores de empresa com antivírus que segura arquivos de vídeo), aparece em vermelho a mensagem com o botão **Abrir no player do Windows**: clique nele para ver o teste no player do computador. O arquivo também fica salvo na pasta de destino como `nome-do-video_sample.mp4`.

## O que faz o botão "Dividido"?

Mostra o vídeo original à esquerda e o resultado do Pascal à direita, com uma linha que você arrasta. Quando você mexe em um ajuste, o lado do Pascal se atualiza e pisca de leve para você saber que mudou. Se a pessoa estiver toda do lado do original, arraste a linha até ela.

## O cabelo "pisca" uma luz mais clara de vez em quando. O que é?

É o reflexo do fundo verde atrás dos fios do cabelo, que muda de um quadro para o outro. O Pascal já segura essas piscadas de 1 a 3 quadros no vídeo final (o quadro ao vivo mostra um quadro só e não consegue mostrar isso). Confira no **teste de 5 segundos**, não no quadro ao vivo.

## O contorno do cabelo ficou escuro ou com uma "auréola". Como resolvo?

1. Use o zoom do quadro ao vivo e escolha **Dividido** para comparar com o original.
2. Na aba **Recorte e fundo**, aumente **Recorte: força do tira-verde** se o contorno estiver esverdeado.
3. Aumente **Recorte: cor original na borda do cabelo** se o contorno estiver escuro demais, ou diminua se ficar liso demais.
4. Diminua **Sombra na borda do cabelo** se aparecer uma faixa escura em volta do rosto.

## O áudio ficou diferente do original. É normal?

O Pascal por padrão só nivela o volume, porque o som original das câmeras costuma ser bom e filtrar demais deixa a voz "dentro de um banheiro". Se quiser mexer, use a aba **Áudio**. Compare sempre com o botão **Original (para comparar)** depois do teste de 5 segundos.

## O teste de 5 segundos ficou lento ou travou. O que fazer?

1. Feche o navegador, o Premiere e outros programas pesados.
2. Espere o fim: a primeira etapa (o recorte avançado) é a mais demorada.
3. Se aparecer uma mensagem de erro em vermelho, ela diz o que aconteceu. A pasta `logs` guarda um relatório de cada teste e render, que você pode enviar para suporte.

## Dá para cancelar?

Sim. Durante o teste ou o render, clique em **Cancelar**. O arquivo incompleto é apagado.

## Posso mexer nos ajustes e guardar para a próxima vez?

Sim. Em **Meus ajustes salvos** (clique no título para abrir a caixa), escreva um nome e clique em **Salvar**. Para voltar ao padrão, clique em **Voltar ao padrão Pascal**. Dois cliques em qualquer controle voltam aquele controle ao valor padrão.

## O programa fechou sozinho. É normal?

Sim, quando você fecha a janela do Pascal o programa se encerra sozinho, alguns segundos depois. Para abrir de novo, dê dois cliques em **Iniciar_Pascal.bat**. Se aparecer "O Pascal parou de responder", ele foi fechado: abra o **Iniciar_Pascal.bat** outra vez.

## Posso usar no pendrive?

Pode. Descompacte o Pascal no pendrive e abra o **Iniciar_Pascal.bat** de lá. O desempenho depende da velocidade do pendrive; para vídeos longos, copie o vídeo para o computador.

## Posso processar vários vídeos?

Um de cada vez. Escolha o vídeo, renderize, e depois escolha o próximo. Os ajustes ficam como você deixou.

## Escolhi o vídeo e nenhum quadro aparece. O que faço?

1. **Espere um pouco.** Primeiro o Pascal mostra uma prévia rápida (recorte clássico) e depois a troca pela imagem com o recorte avançado. Em computadores mais lentos isso leva alguns minutos; o contador de segundos aparece no alto do vídeo.
2. **Leia a mensagem em vermelho** no meio do vídeo e no passo 1 (embaixo do botão Escolher). Ela diz o que aconteceu.
3. Abra **Ajuda e perguntas → Verificar instalação**. O Pascal mostra o que está faltando neste computador (programa bloqueado pelo Windows, pasta aberta de dentro do zip, pouca memória…). Clique em **Copiar relatório** para mandar o resultado para o suporte.
4. Se aparecer **Desbloquear arquivos**, clique nele: o Windows marca como "baixado da internet" tudo que vem de um zip e às vezes bloqueia os programas. Você também pode, antes de extrair, clicar com o botão direito no `Pascal.zip`, escolher **Propriedades** e marcar **Desbloquear**.
5. Baixe o **`Pascal.zip` da página Releases** do GitHub. O botão verde *Code → Download ZIP* só traz o código, sem o FFmpeg e o Python, e o Pascal não consegue ler o vídeo.
6. Extraia o zip antes de abrir (botão direito → **Extrair tudo**) e use o Google Chrome ou o Microsoft Edge.
7. Se o recorte avançado estiver indisponível, o Pascal usa o recorte clássico sozinho e avisa no vídeo, com o motivo. Ele funciona, só com o cabelo menos natural.

## Apareceu um aviso grande: "O recorte avançado não está funcionando neste computador". E agora?

Ao abrir, o Pascal testa sozinho se tudo que precisa está disponível. Se o recorte avançado não abrir, ele primeiro **tenta consertar sozinho** (tira o bloqueio de "baixado da internet", testa sem as cópias do C++ da pasta, procura outros Pythons no computador) e só então mostra o aviso, com **o motivo exato** e o **passo a passo**. Enquanto isso fica uma faixa vermelha no alto e o Pascal usa o recorte clássico (funciona, mas o cabelo fica menos natural).

1. Clique em **Tentar de novo**. O Pascal repete o teste e o conserto.
2. Se continuar, instale o **Python 3.13 ou 3.14 de 64 bits** (python.org/downloads, opção "Instalar só para mim", sem administrador; no computador corporativo, a pasta `X:\Python`). Feche o Pascal e abra de novo: ele acha o Python sozinho e já leva as bibliotecas.
3. Clique em **Desbloquear arquivos** e depois em **Tentar de novo**. Se um antivírus estiver bloqueando a pasta do Pascal, peça a quem cuida do computador para liberá-la.
4. Clique em **Copiar relatório** e envie para quem fez o Pascal. Para continuar trabalhando agora, clique em **Continuar com o recorte clássico**.

## Preciso instalar o C++ ou ser administrador?

Não. A partir da versão 1.0.2 o Pascal já leva dentro da própria pasta os arquivos do Microsoft Visual C++ de que o recorte avançado precisa, e roda em um login comum, sem administrador. Se você usa uma versão mais antiga e o computador não tem o C++, baixe o `Pascal.zip` mais recente.

## Uso o Pascal num computador do trabalho que bloqueia programas. O que faço?

Alguns computadores corporativos não deixam abrir programas de fora das pastas autorizadas, e aí o Python que vem dentro do Pascal não abre. A partir da versão 1.0.3 o Pascal resolve isso sozinho:

1. Instale o Python 3.13 ou 3.14 de 64 bits pelo caminho que a sua empresa libera (em muitos computadores corporativos o instalador fica na pasta `X:\Python`). Não precisa ser administrador.
2. Abra o Pascal de novo pelo **Iniciar_Pascal.bat**. Ele acha o Python instalado e mostra na janela preta a linha "Usando o Python instalado neste computador".

**Não precisa instalar mais nada.** As bibliotecas que o recorte avançado usa já vêm dentro do Pascal (pasta `pacotes`), prontas para o Python 3.12, 3.13 e 3.14. Se o Pascal não achar nenhum Python, a janela preta explica o que fazer e, se existir, abre a pasta `X:\Python`. Para conferir, abra **Ajuda e perguntas → Verificar instalação**: a linha "Recorte avançado disponível" mostra qual Python está sendo usado.

## Mesmo no máximo, um ajuste não resolve. Dá para ir além?

Desde a versão 1.0.5 vários controles vão mais longe que antes (o valor padrão não mudou). Para o verde que sobra no cabelo: **Recorte: força do tira-verde** vai até 2 (acima de 1 alcança cabelo mais claro e mais longe da borda) e, no recorte clássico, **Remoção de reflexo verde** e **Tirar verde do cabelo e das sombras verdes** também vão até 2. No máximo, uma roupa verde ou oliva pode ficar mais cinza: confira no **Quadro ao vivo** com o botão **Dividido**. Cor, luz, nitidez e os ajustes de áudio também ganharam faixa maior.

## Os ajustes "Recorte:" não mudam nada. Por quê?

Os ajustes que começam com "Recorte:" e o "Estilo da borda do cabelo" só valem no recorte avançado. Quando o recorte avançado não está funcionando no computador, o Pascal usa o recorte clássico e mostra, embaixo desses ajustes, o aviso "Sem efeito agora". Nesse caso, para tirar o verde do cabelo use **Tirar verde do cabelo e das sombras verdes** e **Remoção de reflexo verde**, e veja a pergunta anterior para fazer o recorte avançado funcionar.

## Posso usar o Pascal em inglês?

Pode. No alto da janela, à direita, clique em **EN** (e em **PT** para voltar ao português). As telas, as perguntas frequentes e o passo a passo mudam de idioma. Os relatórios técnicos da pasta `logs` ficam em português.

## O Pascal é gratuito mesmo? Posso ajudar a melhorar?

É, e sempre vai ser. O Pascal é um aplicativo livre da Cerrado Projects: livre para usar e livre para melhorar. O código e as versões para baixar estão em github.com/cerradoprojects/pascalchromaremover. Se você sabe programar, pode copiar, mudar e devolver as melhorias.

## Onde pego ajuda?

Abra **Ajuda e perguntas** dentro do Pascal ou use o contato do site. Se for relatar um problema, anexe o arquivo `resumo.txt` da pasta `logs` do teste que deu problema.
