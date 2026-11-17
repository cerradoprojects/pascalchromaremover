# Pascal — step by step

Pascal takes a video recorded in front of a green screen and delivers the finished video: person cut out, studio black background (or transparent), light and color adjusted, sharp image and audio volume evened out. Everything runs on your computer, with no internet and no account.

## Before you start

- A computer with Windows 10 or 11. You don't need to be an administrator.
- Pascal's folder unzipped (it can stay on the computer or on a USB stick).
- A video recorded with a green background. It can be horizontal or vertical.
- The **PT | EN** button, at the top right of the window, switches the program's language (Portuguese or English).

## 1. Open Pascal

1. Unzip Pascal's zip file into any folder. Example: `C:\Pascal`.
2. Open the folder and double-click **Iniciar_Pascal.bat**.
3. A Pascal window opens, with the chameleon in the corner. A black window also appears: leave it open and ignore it. It closes by itself when you close Pascal.

> If Windows shows the warning "Windows protected your PC", click **More info** and then **Run anyway**. Pascal installs nothing.

> **Work computer that blocks programs?** If the black window says "NAO CONSEGUI ABRIR O PYTHON" (couldn't open Python), install Python 3.13 or 3.14 64-bit (on corporate computers the installer is often in the `X:\Python` folder) and open Pascal again. The libraries already ship with Pascal: nothing else to install.

## 2. Choose the video (step 1 on screen)

1. Click **Choose…** and select the video.
2. Under the field you will see the size, the frames per second and the duration. If that shows up, the video was read.
3. In the right-hand panel, the **Live frame** shows one frame of the video already treated. The first time, a quick preview (classic cutout) shows up right away and, when the advanced cutout finishes, it is swapped for the final image: about 30 seconds on a good computer, a few minutes on a slower one (a seconds counter shows at the top of the video). After that, each adjustment shows up right away.
4. If nothing shows up or a red message appears, open **Help & FAQ → Check installation**: Pascal shows what is missing on this computer.

## 3. Look closely

1. Turn the mouse wheel over the image to zoom. Drag the image to move it.
2. The **Fit, 100%, 200%, 400%, 800%** buttons set the zoom in one go. Double-clicking the image goes back to the full screen.
3. **Original** shows the video without treatment. **Split** shows half of each side, with a bar you can drag.
4. The **Frame** bar chooses which moment of the video appears. Pick a moment when the person moves their head: that is where the cutout shows the most.
5. To see the video bigger: drag the little gray bar between the video and the **Settings**; use **Hide settings** or **◧ Panel** to give it more room; or click **⛶ Full screen** (key **F**; **Esc** goes back).
6. With **Transparent background** on, choose the background color in the squares above the video (or in the colorful square, for any color). It also works for the 5-second test.

## 4. Choose what Pascal does (step 2 on screen)

Each switch turns a part on or off:

- **Cut out the green background**: removes the green and keeps only the person.
- **Transparent background**: only turn it on if you will edit in Premiere. Without it, the background is studio black.
- **Studio light and color**: makes the tone warmer and the face brighter.
- **Sharpness and Full HD size**: the video always comes out at 1080p, horizontal (1920×1080) or vertical (1080×1920).
- **Studio audio**: only adjusts the volume. The original sound is usually already good, and doing more can make it worse.

## 5. Adjust the look

1. Under the frame, use the tabs: **Essentials**, **Cutout and background**, **Light and color**, **Sharpness and size**, **Audio**.
2. Move a control and look at the frame: it changes right away.
3. Double-click a control to return it to its default value.
4. If you didn't like what you did, click **Back to Pascal defaults**, in the left column.
5. When you like the result, click the **My saved settings** title (in the left column, at the bottom) to open the box, type a name and click **Save**. Next time, just open it.

> Tip: the **Cutout: original color on the hair edge** and **Cutout: green-removal strength** adjustments ask for a new cutout of the frame and take a few seconds to update. The others are instant.

## 6. Choose where to save (step 3 on screen)

1. Click **Choose folder…** and select the folder where the finished videos will be saved.
2. If you don't choose one, Pascal saves to the same folder as the original video. The **Use the video's own folder** button goes back to that default.
3. If you chose a folder, Pascal remembers it next time.
4. If the chooser window doesn't open, open **Type the folder path**, type the path (example: `D:\Videos\Prontos`) and click **Use**.

## 7. Test 5 seconds (step 4 on screen)

1. Click **Test 5 seconds**. Pascal processes 5 seconds of the video, starting at the moment chosen on the Frame bar.
2. When it finishes, the video plays on screen. Use **Original (to compare)** to hear and see the difference. If the background is transparent, choose the background color in the squares above the video: the test comes out with real transparency and the color changes instantly.
3. The test is also saved to the destination folder with the name **video-name_sample.mp4**. That way you can open it in another player or show it to a colleague. With the transparent background, that file shows the person over the background color chosen in the squares. If the video doesn't play on Pascal's screen, click **Open in the Windows player**.
4. A report appears under the video. If there are red warnings, read them: they say what to look at.

## 8. Render the full video

1. Click **Render the full video**.
2. Follow the progress bar. You can cancel at any time.
3. When it finishes, **Done!** and the file path appear. Click **Open the folder**.
4. You can walk away: while Pascal generates the video, it asks Windows not to sleep or shut down (a notice with a padlock shows under the progress bar). If someone tells Windows to shut down, it warns that Pascal is working. Keep the laptop plugged in with the lid open.

> The advanced cutout takes time: with the computer free, about 0.2 to 1 second per frame. A 1-minute video can take 6 to 30 minutes. Close the browser and other heavy programs while Pascal works. For long videos, start with a 5-second test.

## 9. Close

Click **Close program**. The finished videos stay in the folder you chose.
