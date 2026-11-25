# Pascal — passo a passo

O Pascal pega o vídeo gravado na frente do fundo verde e entrega o vídeo pronto: pessoa recortada, fundo preto de estúdio (ou transparente), luz e cor ajustadas, imagem nítida e volume do áudio nivelado. Tudo roda no seu computador, sem internet e sem conta.

## Antes de começar

- Computador com Windows 10 ou 11. Não precisa ser administrador.
- A pasta do Pascal descompactada (pode ficar no computador ou em um pendrive).
- Um vídeo gravado com fundo verde. Pode ser horizontal ou vertical.
- O botão **PT | EN**, no alto da janela à direita, troca o idioma do programa (português ou inglês).

## 1. Abrir o Pascal

1. Descompacte o arquivo zip do Pascal em uma pasta qualquer. Exemplo: `C:\Pascal`.
2. Abra a pasta e dê dois cliques em **Iniciar_Pascal.bat**.
3. Uma janela do Pascal abre, com o camaleão no canto. Uma janela preta também aparece: deixe-a aberta e ignore. Ela fecha sozinha quando você fecha o Pascal.

> Se o Windows mostrar o aviso "O Windows protegeu o computador", clique em **Mais informações** e depois em **Executar assim mesmo**. O Pascal não instala nada.

> **Computador do trabalho que bloqueia programas?** Se a janela preta disser "NAO CONSEGUI ABRIR O PYTHON", instale o Python 3.13 ou 3.14 de 64 bits (em computador corporativo o instalador costuma ficar na pasta `X:\Python`) e abra o Pascal de novo. As bibliotecas já vêm com o Pascal: não precisa instalar mais nada.

## 2. Escolher o vídeo (passo 1 na tela)

1. Clique em **Escolher…** e selecione o vídeo.
2. Abaixo do campo aparecem o tamanho, os quadros por segundo e a duração. Se aparecer isso, o vídeo foi lido.
3. No painel da direita, o **Quadro ao vivo** mostra um quadro do vídeo já tratado. Na primeira vez, aparece logo uma prévia rápida (recorte clássico) e, quando o recorte avançado termina, ela é trocada pela imagem final: cerca de 30 segundos num computador bom, alguns minutos num mais lento (um contador de segundos aparece no alto do vídeo). Depois disso, cada ajuste aparece na hora.
4. Se nada aparecer ou surgir uma mensagem em vermelho, abra **Ajuda e perguntas → Verificar instalação**: o Pascal mostra o que está faltando neste computador.

## 3. Olhar de perto

1. Gire a rodinha do mouse sobre a imagem para dar zoom. Arraste a imagem para mexer.
2. Os botões **Tela, 100%, 200%, 400%, 800%** ajustam o zoom de uma vez. Dois cliques na imagem voltam para a tela inteira.
3. **Original** mostra o vídeo sem tratamento. **Dividido** mostra metade de cada lado, com uma barra que você arrasta.
4. A barra **Quadro** escolhe qual momento do vídeo aparece. Escolha um momento em que a pessoa mexe a cabeça: é onde o recorte mais aparece.
5. Para ver o vídeo maior: arraste a barrinha cinza entre o vídeo e os **Ajustes**; use **Esconder ajustes** ou **◧ Painel** para dar mais espaço; ou clique em **⛶ Tela cheia** (tecla **F**; **Esc** volta).
6. Com **Fundo transparente** ligado, escolha a cor de fundo nos quadradinhos acima do vídeo (ou no quadradinho colorido, para qualquer cor). Vale também para o teste de 5 segundos.
7. No **Vídeo de teste** o zoom funciona igual: rodinha do mouse, arrastar, botões **Tela/100%/200%/400%/800%** e dois cliques para voltar. Um clique no vídeo toca ou pausa (ou a **barra de espaço**); as setas **◂ quadro / quadro ▸** (ou as setas do teclado) andam um quadro de cada vez; **⟲ Repetir** deixa o teste tocando sem parar.

## 4. Escolher o que o Pascal faz (passo 2 na tela)

Cada chave liga ou desliga uma parte:

- **Recortar o fundo verde**: tira o verde e deixa só a pessoa.
- **Fundo transparente**: só ligue se for editar no Premiere. Sem isso, o fundo fica preto de estúdio.
- **Luz e cor de estúdio**: deixa o tom mais quente e o rosto mais iluminado.
- **Nitidez e tamanho Full HD**: o vídeo sai sempre em 1080p, na horizontal (1920×1080) ou na vertical (1080×1920).
- **Áudio de estúdio**: só ajusta o volume. O som original já costuma ser bom, e mexer mais pode piorar.

## 5. Ajustar o visual

1. Abaixo do quadro, use as abas: **Essencial**, **Recorte e fundo**, **Luz e cor**, **Nitidez e tamanho**, **Áudio**.
2. Mova um controle e olhe o quadro: ele muda na hora.
3. Dê dois cliques em um controle para voltar ao valor padrão dele.
4. Se não gostou do que fez, clique em **Voltar ao padrão Pascal**, na coluna da esquerda.
5. Quando gostar do resultado, clique no título **Meus ajustes salvos** (na coluna da esquerda, embaixo) para abrir a caixa, escreva um nome e clique em **Salvar**. Da próxima vez é só abrir.

> Dica: os ajustes **Recorte: cor original na borda do cabelo** e **Recorte: força do tira-verde** refazem a borda do recorte e levam alguns segundos para atualizar. Os demais são instantâneos.

## 6. Escolher onde salvar (passo 3 na tela)

1. Clique em **Escolher pasta…** e selecione a pasta onde os vídeos prontos serão gravados.
2. Se você não escolher nenhuma, o Pascal salva na mesma pasta do vídeo original. O botão **Usar a pasta do próprio vídeo** volta a esse padrão.
3. Se você escolheu uma pasta, o Pascal lembra dela na próxima vez.
4. Se a janela de escolha não abrir, abra **Digitar o caminho da pasta**, escreva o caminho (exemplo: `D:\Videos\Prontos`) e clique em **Usar**.

## 7. Testar 5 segundos (passo 4 na tela)

1. Clique em **Testar 5 segundos**. O Pascal processa 5 segundos do vídeo, a partir do momento escolhido na barra Quadro.
2. Quando terminar, o vídeo toca na tela. Use **Original (para comparar)** para ouvir e ver a diferença. Se o fundo for transparente, escolha a cor de fundo nos quadradinhos acima do vídeo: o teste sai com transparência de verdade e a cor muda na hora.
3. O teste também é salvo na pasta de destino com o nome **nome-do-video_sample.mp4**. Assim você pode abrir em outro player ou mostrar a um colega. Com o fundo transparente, esse arquivo mostra a pessoa sobre a cor de fundo escolhida nos quadradinhos. Se o vídeo não tocar na tela do Pascal, clique em **Abrir no player do Windows**.
4. Embaixo do vídeo aparece um relatório. Se houver avisos em vermelho, leia: eles dizem o que olhar.

## 8. Renderizar o vídeo completo

1. Clique em **Renderizar o vídeo completo**.
2. Acompanhe a barra de progresso. Você pode cancelar a qualquer momento.
3. Ao terminar, aparece **Pronto!** e o caminho do arquivo. Clique em **Abrir a pasta**.
4. Pode sair de perto: enquanto o Pascal gera o vídeo, ele pede ao Windows para não dormir nem desligar (aparece um aviso com um cadeado embaixo da barra de progresso). Se alguém mandar desligar, o Windows avisa que o Pascal está trabalhando. Deixe o notebook na tomada e com a tampa aberta.

> O recorte avançado leva tempo: com o computador livre, cerca de 0,2 a 1 segundo por quadro. Um vídeo de 1 minuto pode levar de 6 a 30 minutos. Feche o navegador e outros programas pesados enquanto o Pascal trabalha. Para vídeos longos, comece por um teste de 5 segundos.

## 9. Fechar

Clique em **Fechar programa**. Os vídeos prontos ficam na pasta que você escolheu.
