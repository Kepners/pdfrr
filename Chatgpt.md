That’s actually a \*\*nice, clean concept\*\*. Using \*\*`<` and `>` as the core interaction\*\* is memorable and fits the idea of \*split vs merge\*. If you keep it minimal, the app will feel fast and intentional instead of cluttered.



Let’s refine it so the idea translates clearly to users.



---



\## Core Design Concept



Think of the symbols as \*\*actions on documents\*\*:



\* \*\*`>` Merge PDFs\*\*

&nbsp; Multiple files → One output



\* \*\*`<` Split PDF\*\*

&nbsp; One file → Multiple outputs



So visually:



```

A + B + C  >  ABC      (Merge)



ABC  <  A + B + C      (Split)

```



This makes the UI intuitive even without much text.



---



\## Suggested Layout



\### Minimal UI



```

&nbsp;       <        >

&nbsp;     Split     Merge



&nbsp;   \[ Drop PDFs Here ]

```



When the user clicks a symbol, the UI switches mode.



---



\## Visual Idea



\### Merge Mode



```

&nbsp;     >



&nbsp;Drop PDFs Here

&nbsp;--------------------

&nbsp;file1.pdf

&nbsp;file2.pdf

&nbsp;file3.pdf



&nbsp;\[ Merge PDFs ]

```



\### Split Mode



```

&nbsp;     <



&nbsp;Drop PDF Here

&nbsp;--------------------

&nbsp;big\_document.pdf



&nbsp;Split options:

&nbsp;(•) Every page

&nbsp;( ) Page ranges

&nbsp;( ) Extract pages



&nbsp;\[ Split PDF ]

```



---



\## Interaction Idea (Nice Touch)



Animate the symbols slightly when switching.



Example:



```

<    >

```



Click \*\*`>`\*\* → the arrow expands and slides right

Click \*\*`<`\*\* → arrow expands and slides left



Subtle animation makes the UI feel polished.



---



\## Icon Concept



You could design a logo like:



```

<PDF>

```



or



```

< > PDF

```



Or even:



```

<  |  >

Split   Merge

```



Super minimal — very developer-tool aesthetic.



---



\## Folder-Based Workflow (your idea)



If the app watches a folder, the flow could be:



```

/PDFDrop

&nbsp;  file1.pdf

&nbsp;  file2.pdf

&nbsp;  file3.pdf

```



User presses \*\*`>`\*\*



Output:



```

/PDFDrop/output/merged.pdf

```



Or in \*\*Split Mode `<`\*\*



```

/PDFDrop/output/

&nbsp;  page\_01.pdf

&nbsp;  page\_02.pdf

&nbsp;  page\_03.pdf

```



---



\## One UX Improvement I’d strongly recommend



Don’t rely \*\*only on `<` and `>`\*\*.



Pair them with \*\*micro labels\*\*:



```

< Split

> Merge

```



Symbols alone can confuse non-technical users.



---



\## A Simple Name Idea



If you lean into the concept:



\* \*\*AnglePDF\*\*

\* \*\*SplitMerge\*\*

\* \*\*PDFSwitch\*\*

\* \*\*PDF Angle\*\*

\* \*\*BracketPDF\*\*

\* \*\*LessMore PDF\*\*



`LessMore PDF` is actually memorable.



---



\## One more cool idea



Make the toggle literally:



```

<   >

```



and the selected one \*\*glows\*\*.



Example:



```

\[ < ]   >

```



or



```

<   \[ > ]

```



---



\## If you want, I can also show you



\* a \*\*clean UI mockup\*\*

\* a \*\*logo using `< >`\*\*

\* a \*\*simple Electron / web UI layout\*\*

\* a \*\*drag-drop PDF workflow\*\*



It could become a \*\*really nice indie utility\*\* if you keep the design sharp.



Alright Matt — let’s go all-in and design this like a \*\*proper indie dev tool\*\*. Think \*\*something you'd proudly put next to Raycast, Linear, or Vercel on your desktop. Clean. Intentional. No fluff.



I’ll break this into \*\*4 deliverables\*\* you can directly use.



---



\# 1. High-Quality Logo Prompts (Best Results)



Use these in \*\*Midjourney / Leonardo / Ideogram\*\*.



\### Prompt 1 — Premium Dev Tool Icon



```

Minimalist developer tool logo using the symbols < and > to represent splitting and merging documents. The symbols form a clean geometric flow. Premium SaaS/dev-tool aesthetic similar to Linear, Raycast, and Vercel branding. Vector style, ultra clean, sharp geometry, dark mode friendly, subtle cyan and teal gradients on deep navy background. Modern, elegant, slightly futuristic. Centered icon inside rounded square app icon. No text. Extremely minimal and polished.

```



---



\### Prompt 2 — Document Flow Logo



```

Modern minimalist logo showing PDF pages flowing between < and > symbols to represent split and merge actions. Geometric flat design, premium developer utility aesthetic, dark background with glowing cyan highlights, subtle gradients, clean spacing, balanced composition. Inspired by high-end developer tools like Linear and Raycast. Vector style, simple shapes, iconic and memorable.

```



---



\### Prompt 3 — Brutal Minimal Dev Logo



```

Ultra minimal tech logo using only the symbols < > arranged to form a clever document flow symbol. Strong geometry, perfect spacing, high-end developer tool aesthetic. Monochrome with subtle neon accent. Dark UI friendly. Looks like a premium macOS utility icon. Extremely clean, modern, vector design.

```



---



\# 2. App Icon Concept Ideas



\## Concept A — The Flow



```

▢ ▢ ▢   >

&nbsp;     ▢

```



Pages merging into one.



Split version:



```

▢

<   ▢ ▢ ▢

```



Your `< >` literally \*\*control the direction of the pages\*\*.



This would animate beautifully.



---



\## Concept B — Dev Bracket



Icon:



```

<▢>

```



Where the square is a \*\*PDF page\*\*.



Simple. Smart. Very dev-tool style.



---



\## Concept C — Angle Icon



```

< >

```



But the tips have \*\*folded page corners\*\*.



Very subtle.



---



\## Concept D — Compression Symbol



```

< ▢▢▢ >

```



Pages compressing.



---



\# 3. UI Layout (Clean Dev Tool Style)



\### Main Window



Minimal.



```

&nbsp;       <       >



&nbsp;     Split    Merge





&nbsp;     Drop PDFs Here

&nbsp;    ───────────────

```



Once files drop:



```

file1.pdf

file2.pdf

file3.pdf

```



Button appears:



```

\[ Merge Files ]

```



---



\### Split Mode



```

&nbsp;       <       >



&nbsp;     Split    Merge





&nbsp;     Drop PDF Here

&nbsp;    ───────────────



Split Options



○ Every Page

○ Page Range

○ Extract Pages



\[ Split ]

```



---



\# 4. Premium UI Style Guide



\### Color palette



Dark dev-tool theme.



```

Background   #0B0F19

Surface      #121826

Accent       #14E0C9

Highlight    #22D3EE

```



Clean. Techy. Premium.



---



\### Typography



Use \*\*Inter\*\* or \*\*Satoshi\*\*.



Example:



```

Mode label → Medium

File names → Regular

Buttons → SemiBold

```



Avoid heavy fonts.



---



\### Micro Animations (THIS makes it feel premium)



When merging:



```

▢ ▢ ▢ → ▢

```



Pages slide together.



When splitting:



```

▢ → ▢ ▢ ▢

```



Pages expand.



Smooth \*\*200ms animation\*\*.



---



\# 5. Folder Drop Workflow



Your idea is actually great.



Example folder:



```

/PDFDrop

```



User drops files.



App detects.



UI shows:



```

3 files ready

```



Press `>`:



```

merged.pdf created

```



Press `<`:



```

page\_01.pdf

page\_02.pdf

page\_03.pdf

```



---



\# 6. Landing Page Concept



Simple dev-tool landing page.



Hero section:



```

< > PDF



Split and merge PDFs instantly.

Just drop your files.

```



Button:



```

Download

```



Feature section:



```

<  Split PDFs

Break large PDFs into pages.



>  Merge PDFs

Combine documents instantly.



⚡ Lightning fast

No cloud required.

```



---



\# 7. Really Nice App Names



Top picks:



\*\*AnglePDF\*\* ⭐

\*\*BracketPDF\*\*

\*\*PDFSwitch\*\*

\*\*MergeAngle\*\*

\*\*PDFFlow\*\*



Best one:



🔥 \*\*AnglePDF\*\*



Matches:



```

< >

```



---



\# 8. One Extra Idea (Very Slick)



When switching modes:



```

<    >

```



The active symbol \*\*slides into the center\*\*.



Example:



Merge mode



```

&nbsp;  >

```



Split mode



```

<

```



Tiny but \*\*very satisfying interaction\*\*.



---



\# 9. If you want, I can also design



\* \*\*A full UI mockup\*\*

\* \*\*Your actual app icon\*\*

\* \*\*A macOS style interface\*\*

\* \*\*Drag-drop workflow UX\*\*

\* \*\*Electron / Tauri layout\*\*



And honestly Matt — this idea is \*\*exactly the type of indie utility that can quietly get thousands of downloads\*\* if the design is clean.



The \*\*`< >` concept is strong\*\*. It just needs to be executed with taste.



