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

- **O quadro ao vivo** aparece em cerca de 30 segundos na primeira vez em cada momento do vídeo (é o tempo do recorte avançado daquele quadro). Depois, cada ajuste aparece em 1 a 2 segundos, inclusive os de recorte do cabelo.
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

Atenção: esse formato gera arquivos grandes, cerca de 2,5 GB por minuto. Para vídeos longos, escolha em **Recorte e fundo** o modo **Fundo Transparente Leve (QTRLE)**, que é menor.

## Qual a diferença entre fundo preto e transparente?

Com o fundo preto, o Pascal já entrega o vídeo final em `.MP4`, pronto para publicar. Com o fundo transparente, ele entrega a pessoa recortada em `.MOV`, para você escolher o fundo depois no Premiere.

## Onde ficam os vídeos prontos?

Na pasta que você escolheu no passo 3. Se você não escolheu nenhuma, na mesma pasta do vídeo original (ou na pasta `output` do Pascal, se aquela pasta não aceitar gravação). O botão **Abrir pasta** leva até lá. O Pascal nunca apaga nem substitui o vídeo original.

## O teste de 5 segundos fica salvo?

Depende do fundo. Com o **fundo preto de estúdio**, além de tocar na tela, o teste é salvo na pasta de destino como `nome-do-video_sample.mp4`, para você abrir em outro player ou mostrar a alguém. Com o **Fundo transparente** ligado, o teste só aparece na tela do Pascal e não vira arquivo: um player comum não entende a transparência e mostraria o verde original por trás da pessoa. Para ter o arquivo com transparência, renderize o vídeo completo.

## Como aumento o vídeo na tela?

Arraste a barrinha cinza que fica entre o vídeo e os **Ajustes**: o vídeo cresce e os ajustes diminuem. Dois cliques nela (ou o botão **Esconder ajustes**) escondem os ajustes de vez. O botão **◧ Painel**, no alto, esconde a coluna da esquerda. E o botão **⛶ Tela cheia** (ou a tecla **F**) mostra só o vídeo na tela inteira; **Esc** volta. O Pascal lembra o tamanho que você deixou.

## Posso ver o fundo transparente em outras cores?

Pode. Com **Fundo transparente** ligado, escolha a cor atrás da pessoa nos quadradinhos de cima do vídeo (preto, grafite, cinza, branco, azul, verde, vermelho, âmbar, xadrez) ou clique no quadradinho colorido para escolher qualquer outra cor. Isso vale para o **Quadro ao vivo** e também para o **teste de 5 segundos**: ele sai com transparência de verdade e você troca a cor de fundo sem refazer o teste. Esse teste fica só na tela do Pascal (não é salvo na pasta de destino).

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

## Posso usar o Pascal em inglês?

Pode. No alto da janela, à direita, clique em **EN** (e em **PT** para voltar ao português). As telas, as perguntas frequentes e o passo a passo mudam de idioma. Os relatórios técnicos da pasta `logs` ficam em português.

## O Pascal é gratuito mesmo? Posso ajudar a melhorar?

É, e sempre vai ser. O Pascal é um aplicativo livre da Cerrado Projects: livre para usar e livre para melhorar. O código e as versões para baixar estão em github.com/cerradoprojects/pascalchromaremover. Se você sabe programar, pode copiar, mudar e devolver as melhorias.

## Onde pego ajuda?

Abra **Ajuda e perguntas** dentro do Pascal ou use o contato do site. Se for relatar um problema, anexe o arquivo `resumo.txt` da pasta `logs` do teste que deu problema.
