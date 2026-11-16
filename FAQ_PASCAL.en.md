# Pascal — frequently asked questions

## What is Pascal?

It is a Windows program that turns a recording made in front of a green screen into a video with a studio look. It cuts out the person, puts a black background behind them (or leaves it transparent), adjusts light and color, improves sharpness and evens out the audio volume. The name comes from a chameleon, which changes color to match its surroundings.

## How much does it cost? Do I need internet or an account?

It costs nothing, needs no account and works without internet. Your video never leaves your computer. The internet is only used once, to download Pascal's zip file.

## How do I download and install it?

1. Download Pascal's zip file from the link on this page (or from **Releases** on GitHub: github.com/cerradoprojects/pascalchromaremover).
2. Right-click the zip and choose **Extract all**. Pick a folder, for example `C:\Pascal`, or a USB stick.
3. Open the folder and double-click **Iniciar_Pascal.bat**.

There is no installation and you don't need to be an administrator. To uninstall, delete the folder.

## Windows showed "Windows protected your PC". What do I do?

Click **More info** and then **Run anyway**. The warning appears because the program has no paid digital signature. Pascal installs nothing and doesn't change your system.

## What computer do I need?

Windows 10 or 11, 8 GB of memory and about 10 GB free to work. No graphics card needed. The freer the computer is, the faster Pascal works.

## How long does it take?

- **The live frame** first shows, in 2 to 5 seconds, a quick preview (classic cutout) and then swaps it for the frame with the advanced cutout: about 30 seconds on a good computer and a few minutes on a slower one (a seconds counter shows at the top of the video). After that, each adjustment shows in 1 to 2 seconds, including the hair cutout ones.
- **The 5-second test** takes 1 to 5 minutes.
- **The full video** with the advanced cutout takes 0.2 to 1 second per frame. A 1-minute video can take 6 to 30 minutes, and a 30-minute one can take several hours. Keep the computer plugged in and with no other heavy programs open.

## Can the computer sleep or shut down in the middle of a video?

Not while Pascal is working. During the 5-second test and during the full video, Pascal asks Windows not to go to sleep and not to shut down (the screen can turn off normally). If someone tells Windows to shut down or restart at that moment, Windows warns that Pascal is generating a video and lets the person choose between waiting or shutting down anyway (in that case the video in progress is lost). When the video finishes, fails or you cancel, the protection releases by itself and the computer goes back to normal behavior. Some things no program controls: keep the laptop plugged in with the lid open (closing the lid may suspend the laptop, depending on Windows power settings) and avoid forced shutdowns.

## How does Pascal cut out hair so well?

The classic cutout by green color tends to eat hair strands and leave a greenish outline. Pascal's advanced cutout recognizes the person frame by frame and cuts out strand by strand, without relying only on the background color. Then Pascal removes the green left on the hair tips. Everything runs inside your computer. If this feature isn't complete in your copy, Pascal uses the classic cutout and warns you.

## Does Pascal send my video anywhere?

No. Everything runs entirely on your computer. Nothing is sent to the internet.

## Can I use a vertical video?

Yes. Pascal recognizes the orientation by itself and delivers 1080×1920 for vertical or 1920×1080 for horizontal.

## Why does the video always come out at 1080p and never 4K?

By project decision: 1080p (Full HD) is the size that suits almost every use, and 4K would make everything much slower without showing more detail, because the source recording doesn't have that resolution anyway. The shorter side of the video is always 1080 pixels. There is an option called **Keep the original size**, under **Sharpness and size**.

## How do I use the video in Premiere?

1. Turn on **Transparent background** in step 2.
2. Render. The file comes out as `.MOV` (ProRes 4444), with transparency.
3. Drag the file onto the Premiere timeline. Put another background on the track below.

Note: this format makes large files, about 2.5 GB per minute. For long videos, choose the **Light Transparent Background (.MOV QTRLE)** mode under **Cutout and background**, which is smaller.

## What's the difference between a black and a transparent background?

With the black background, Pascal already delivers the final video as `.MP4`, ready to publish. With the transparent background, it delivers the cut-out person as `.MOV`, so you can pick the background later in Premiere.

## Where do the finished videos go?

To the folder you chose in step 3. If you didn't choose one, to the same folder as the original video (or to Pascal's `output` folder, if that folder doesn't accept writing). The **Open folder** button takes you there. Pascal never deletes or replaces the original video.

## Is the 5-second test saved?

It depends on the background. With the **studio black background**, besides playing on screen, the test is saved to the destination folder as `video-name_sample.mp4`, so you can open it in another player or show it to someone. With **Transparent background** on, the test only appears on Pascal's screen and doesn't become a file: an ordinary player doesn't understand transparency and would show the original green behind the person. To get the file with transparency, render the full video.

## How do I make the video bigger on screen?

Drag the little gray bar between the video and the **Settings**: the video grows and the settings shrink. Double-clicking it (or the **Hide settings** button) hides the settings completely. The **◧ Panel** button at the top hides the left column. And the **⛶ Full screen** button (or the **F** key) shows only the video on the whole screen; **Esc** goes back. Pascal remembers the size you left it at.

## Can I see the transparent background in other colors?

Yes. With **Transparent background** on, pick the color behind the person in the squares above the video (black, graphite, gray, white, blue, green, red, amber, checkerboard) or click the colorful square to pick any other color. This works for the **Live frame** and also for the **5-second test**: it comes out with real transparency and you change the background color without redoing the test. That test stays only on Pascal's screen (it isn't saved to the destination folder).

## What does the "Split" button do?

It shows the original video on the left and Pascal's result on the right, with a line you can drag. When you change a setting, the Pascal side updates and flashes lightly so you know it changed. If the person is entirely on the original side, drag the line over to them.

## The hair "flickers" a lighter light now and then. What is it?

It is the reflection of the green background behind the hair strands, which changes from one frame to the next. Pascal already holds back these 1-to-3-frame flickers in the final video (the live frame shows a single frame and can't show that). Check it in the **5-second test**, not in the live frame.

## The hair outline came out dark or with a "halo". How do I fix it?

1. Use the live frame zoom and choose **Split** to compare with the original.
2. In the **Cutout and background** tab, raise **Cutout: green-removal strength** if the outline looks greenish.
3. Raise **Cutout: original color on the hair edge** if the outline is too dark, or lower it if it gets too smooth.
4. Lower **Shadow on the hair edge** if a dark band shows up around the face.

## The audio is different from the original. Is that normal?

By default Pascal only evens out the volume, because the original camera sound is usually good and filtering too much leaves the voice sounding "inside a bathroom". If you want to tweak it, use the **Audio** tab. Always compare with the **Original (to compare)** button after the 5-second test.

## The 5-second test is slow or froze. What can I do?

1. Close the browser, Premiere and other heavy programs.
2. Wait for it to end: the first stage (the advanced cutout) is the slowest.
3. If an error message shows up in red, it says what happened. The `logs` folder keeps a report of each test and render, which you can send to support.

## Can I cancel?

Yes. During the test or the render, click **Cancel**. The incomplete file is deleted.

## Can I tweak the settings and keep them for next time?

Yes. Under **My saved settings** (click the title to open the box), type a name and click **Save**. To go back to the default, click **Back to Pascal defaults**. Double-clicking any control returns that control to its default value.

## The program closed by itself. Is that normal?

Yes, when you close Pascal's window the program shuts itself down a few seconds later. To open it again, double-click **Iniciar_Pascal.bat**. If "Pascal stopped responding" appears, it was closed: open **Iniciar_Pascal.bat** again.

## Can I use it from a USB stick?

Yes. Unzip Pascal onto the USB stick and open **Iniciar_Pascal.bat** from there. Performance depends on the USB stick speed; for long videos, copy the video to the computer.

## Can I process several videos?

One at a time. Choose the video, render, and then choose the next. The settings stay as you left them.

## I chose the video and no frame shows up. What do I do?

1. **Wait a little.** Pascal first shows a quick preview (classic cutout) and then swaps it for the image with the advanced cutout. On slower computers that takes a few minutes; a seconds counter shows at the top of the video.
2. **Read the red message** in the middle of the video and in step 1 (under the Choose button). It says what happened.
3. Open **Help & FAQ → Check installation**. Pascal shows what is missing on this computer (a program blocked by Windows, a folder opened from inside the zip, little memory…). Click **Copy report** to send the result to support.
4. If **Unblock files** shows up, click it: Windows marks everything that comes from a zip as "downloaded from the internet" and sometimes blocks the programs. You can also, before extracting, right-click `Pascal.zip`, choose **Properties** and tick **Unblock**.
5. Download **`Pascal.zip` from the Releases page** on GitHub. The green *Code → Download ZIP* button only brings the source code, without FFmpeg and Python, and Pascal can't read the video.
6. Extract the zip before opening it (right-click → **Extract all**) and use Google Chrome or Microsoft Edge.
7. If the advanced cutout is unavailable, Pascal uses the classic cutout by itself and warns you on the video, with the reason. It works, just with less natural hair.

## A big warning appeared: "The advanced cutout is not working on this computer". Now what?

When it opens, Pascal tests by itself whether everything it needs is available. If the advanced cutout doesn't start, it first **tries to fix it on its own** (removes the "downloaded from the internet" block, tests without the C++ copies in its folder, looks for other Pythons on the computer) and only then shows the warning, with **the exact reason** and **step-by-step instructions**. Meanwhile a red strip stays at the top and Pascal uses the classic cutout (it works, but hair looks less natural).

1. Click **Try again**. Pascal repeats the test and the repair.
2. If it persists, install **Python 3.13 or 3.14, 64-bit** (python.org/downloads, "Install for me only" option, no administrator; on a corporate computer, the `X:\Python` folder). Close Pascal and open it again: it finds Python by itself and already carries the libraries.
3. Click **Unblock files**, then **Try again**. If an antivirus is blocking Pascal's folder, ask whoever administers the computer to allow it.
4. Click **Copy report** and send it to whoever made Pascal. To keep working right now, click **Continue with the classic cutout**.

## Do I need to install C++ or be an administrator?

No. From version 1.0.2 on, Pascal carries the Microsoft Visual C++ files that the advanced cutout needs inside its own folder, and it runs on a regular login, without administrator rights. If you use an older version and the computer doesn't have C++, download the latest `Pascal.zip`.

## I use Pascal on a work computer that blocks programs. What do I do?

Some corporate computers don't let programs run from outside approved folders, so the Python that ships inside Pascal won't open. From version 1.0.3 on, Pascal handles this by itself:

1. Install Python 3.13 or 3.14 (64-bit) the way your company allows (on many corporate computers the installer is in the `X:\Python` folder). You don't need to be an administrator.
2. Open Pascal again with **Iniciar_Pascal.bat**. It finds the installed Python and the black window shows the line "Usando o Python instalado neste computador" (using the Python installed on this computer).

**Nothing else to install.** The libraries the advanced cutout uses already ship inside Pascal (`pacotes` folder), ready for Python 3.12, 3.13 and 3.14. If Pascal can't find any Python, the black window explains what to do and opens the `X:\Python` folder if it exists. To check, open **Help & FAQ → Check installation**: the line "Advanced cutout available" shows which Python is in use.

## The "Cutout:" settings don't change anything. Why?

The settings that start with "Cutout:" and the "Hair edge style" only work with the advanced cutout. When the advanced cutout isn't working on the computer, Pascal uses the classic cutout and shows "No effect right now" under those settings. In that case, to remove green from the hair use **Remove green from hair and green shadows** and **Green spill removal**, and see the previous question to get the advanced cutout working.

## Can I use Pascal in English?

Yes. At the top right of the window, click **EN** (and **PT** to go back to Portuguese). The screens, the FAQ and the step by step change language. The technical reports in the `logs` folder stay in Portuguese.

## Is Pascal really free? Can I help improve it?

It is, and it always will be. Pascal is a free application from Cerrado Projects: free to use and free to improve. The code and the downloadable versions are at github.com/cerradoprojects/pascalchromaremover. If you can code, you can copy it, change it and send the improvements back.

## Where do I get help?

Open **Help & FAQ** inside Pascal or use the contact on the website. If you are reporting a problem, attach the `resumo.txt` file from the `logs` folder of the test that had the problem.
