# 📖 Vyntrix Automation - Complete User Guide

**Welcome to Vyntrix!** This guide will walk you through every step of the automation process.

---

## 📑 Table of Contents

1. [First-Time Setup](#first-time-setup)
2. [Running Your First Project](#running-your-first-project)
3. [Understanding the Workflow](#understanding-the-workflow)
4. [Visual Style Guide](#visual-style-guide)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## 🚀 First-Time Setup

### Step 1: Install Python

Download and install Python 3.8 or higher from [python.org](https://www.python.org/downloads/)

**Verify installation:**
```bash
python --version
# Should show: Python 3.8.x or higher
```

### Step 2: Install Dependencies

Navigate to the project folder and run:
```bash
pip install -r requirements.txt
```

**Important:** Install `pyperclip` for proper UTF-8 support:
```bash
pip install pyperclip
```

### Step 3: Install Google Chrome

The tool requires Chrome for browser automation. Download from [google.com/chrome](https://www.google.com/chrome/)

### Step 4: Prepare Your Accounts

You'll need:
- ✅ **Google Account** (for Sheets and Flow AI)
- ✅ **ChatGPT or Kimi AI account**
- ⏳ **ElevenLabs account** (optional, for TTS in future)

---

## 🎬 Running Your First Project

### Step 1: Launch the Tool

```bash
python main.py
```

You'll see the **Vyntrix logo**:
```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██╗   ██╗██╗   ██╗███╗   ██╗████████╗██████╗ ██╗██╗  ██╗   ║
║   ██║   ██║╚██╗ ██╔╝████╗  ██║╚══██╔══╝██╔══██╗██║╚██╗██╔╝   ║
║   ██║   ██║ ╚████╔╝ ██╔██╗ ██║   ██║   ██████╔╝██║ ╚███╔╝    ║
║   ╚██╗ ██╔╝  ╚██╔╝  ██║╚██╗██║   ██║   ██╔══██╗██║ ██╔██╗    ║
║    ╚████╔╝    ██║   ██║ ╚████║   ██║   ██║  ██║██║██╔╝ ██╗   ║
║     ╚═══╝     ╚═╝   ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝   ║
║                                                              ║
║              A U T O M A T I O N   S U I T E                 ║
╚══════════════════════════════════════════════════════════════╝
```

### Step 2: Enter Project Name

```
Enter project name: my_first_video
```

**Tip:** Use lowercase with underscores (e.g., `financial_tips`, `productivity_hacks`)

### Step 3: Paste Your Script

```
Enter/paste your YouTube script (press Ctrl+D when done):
```

**Example script:**
```
Have you ever wondered why some people seem to get rich while others stay broke? 
It's not about working harder—it's about avoiding these financial traps.

First, subscription services. You sign up for one thing, then another, and suddenly 
your bank account is bleeding money from every direction.

Second, food delivery apps. That $15 order three times a week? That's $180 a month. 
You're basically paying extra to avoid doing dishes.

Third, car payments. You convince yourself you deserve that nice car, but it loses 
value the second you drive it off the lot.
```

**Press Ctrl+D (or Ctrl+Z on Windows) when done**

### Step 4: Choose LLM Provider

```
Choose LLM provider:
1. ChatGPT (default)
2. Kimi AI

Enter choice (1-2):
```

**Recommendation:** Use ChatGPT for better English prompts.

### Step 5: Select Visual Style

```
Available visual styles:
1. Ultra Realistic B-Roll
2. Sloppy Handwritten Cartoon
3. Clean Vector Stickman
4. Minimal Flat Icon Infographic
5. 3D Soft Clay Render Style
6. Cyanide & Happiness

Enter style number (1-6):
```

See [Visual Style Guide](#visual-style-guide) below for details.

### Step 6: Add Reference Prompt (Optional)

```
Do you want to add a reference character prompt for consistency? (y/n):
```

**Example reference prompt:**
```
bald round-headed simple stick figure with dot eyes, minimalist design
```

This ensures your main character looks the same across all scenes.

### Step 7: Sit Back and Watch

The automation will now:

1. ✅ **Open ChatGPT/Kimi** (auto-login via persistent Chrome profile)
2. ✅ **Generate scene prompts** (converts script to structured CSV)
3. ✅ **Create Google Sheet** (saves prompts with timestamps)
4. ✅ **Generate images** (submits all prompts to Flow AI)
5. ✅ **Download images** (reverse order, last = 001.png)

**Total time:** ~5-20 minutes depending on script length

---

## 🔄 Understanding the Workflow

### Phase 1: Script Processing

**What happens:**
- Browser opens ChatGPT/Kimi
- Your script is sent with detailed prompt engineering
- AI generates CSV with: Scene #, Time, Narration, Image Prompt

**Output example:**
```csv
Scene #,Time,Narration,Image Prompt
1,0:00-0:05,"Have you ever wondered why...","minimal vector illustration, simple black stick figure with question mark bubble..."
2,0:05-0:10,"First, subscription services...","minimal vector illustration, stick figure surrounded by floating app icons..."
```

### Phase 2: Google Sheets

**What happens:**
- Creates new sheet: `[project_name]_prompts`
- Navigates to cell A1
- Pastes CSV data via clipboard
- Verifies data appears correctly

**Sheet URL is saved for reference**

### Phase 3: Image Generation

**What happens:**
- Opens Google Flow AI project
- Submits prompts one by one (30s intervals to avoid rate limits)
- Waits 90s after last prompt for generation to complete
- Refreshes page

**Important:** Each prompt takes ~30-60 seconds to generate

### Phase 4: Image Download

**What happens:**
- Scrolls page to load all images
- Filters out profile pictures and UI elements
- Downloads in **reverse order** (last generated = 001.png)
- Saves to `projects/[project_name]/images/`

**Why reverse order?** Flow AI shows newest first. Reversing ensures scene 1 = 001.png.

---

## 🎨 Visual Style Guide

### 1. Ultra Realistic B-Roll
**Best for:** Finance, business, serious topics  
**Look:** Photorealistic stock footage style  
**Example:** Professional office scenes, real-looking products

### 2. Sloppy Handwritten Cartoon
**Best for:** Energetic, fun content  
**Look:** Messy marker doodles, hand-drawn feel  
**Example:** Animated explainer style like Casually Explained

### 3. Clean Vector Stickman
**Best for:** Corporate, educational  
**Look:** Minimal stick figures, flat colors  
**Example:** Professional infographics

### 4. Minimal Flat Icon Infographic
**Best for:** Data, statistics, comparisons  
**Look:** Bold icons, modern flat design  
**Example:** Kurzgesagt style graphics

### 5. 3D Soft Clay Render Style
**Best for:** Character-driven stories  
**Look:** Smooth Pixar-like clay renders  
**Example:** 3D animated shorts

### 6. Cyanide & Happiness
**Best for:** Comedy, dark humor  
**Look:** Simple webcomic style  
**Example:** Stick figures with minimal detail, bold outlines

---

## ⚙️ Advanced Features

### Character Consistency

For character-driven content, use a **reference prompt**:

```
Reference Prompt: "30-year-old businessman with glasses and blue suit, professional appearance"
```

The tool automatically detects "main character" scenes and appends your reference prompt.

**Detection keywords:**
- "character walks"
- "character sits"
- "character looks"
- "figure standing"
- "person holding"

### Custom Scene Duration

Default: **5 seconds per scene**

To customize, the tool will calculate timestamps automatically:
- Scene 1: 0:00-0:05
- Scene 2: 0:05-0:10
- Scene 3: 0:10-0:15

### Testing Individual Components

**Test Google Sheets only:**
```bash
python test_sheets.py
```
Paste CSV manually, test filling and reading.

**Test Flow AI downloads only:**
```bash
python test_flow_download.py
```
Enter Flow project URL, download all images.

---

## 🐛 Troubleshooting

### ❌ Problem: "Sheet stays empty after paste"

**Cause:** PowerShell clipboard encoding issue

**Solution:**
```bash
pip install pyperclip
```

**Verify:**
```bash
python -c "import pyperclip; print('✓ pyperclip installed')"
```

---

### ❌ Problem: "Character encoding issues (â€™ instead of ')"

**Cause:** Same as above - PowerShell UTF-8 issue

**Solution:**
```bash
pip install pyperclip
```

---

### ❌ Problem: "Could not find prompt input field"

**Cause:** Flow AI UI changed or page not loaded

**Solution:**
1. Manually check Flow AI interface
2. Wait for page to fully load
3. The tool will prompt for manual paste if needed

---

### ❌ Problem: "Images download in wrong order"

**Not a bug!** The tool downloads in reverse order intentionally.

Last generated image = 001.png (scene 1)  
This matches your script sequence.

---

### ❌ Problem: "Login required every time"

**Cause:** Chrome profile not persisting

**Solution:**
Check that `chrome_profile/` folder exists in project directory.  
The tool creates this automatically and reuses sessions.

---

### ❌ Problem: "ChromeDriver version mismatch"

**Cause:** Chrome updated, driver didn't

**Solution:**
The tool uses `webdriver-manager` which auto-updates.  
If it fails, manually install:
```bash
pip install --upgrade webdriver-manager
```

---

## ✅ Best Practices

### 📝 Script Writing

**Good script structure:**
- Clear narration for each scene
- Visual descriptions embedded
- 5-10 seconds per scene
- Total: 60-120 seconds (12-24 scenes)

**Example:**
```
❌ Bad: "Subscriptions are expensive."
✅ Good: "You sign up for one thing, then another, and suddenly your bank account 
         is getting charged from every direction."
```

### 🎨 Visual Style Selection

**Match your content:**
- **Serious topics** → Ultra Realistic or Vector Stickman
- **Fun/Comedy** → Sloppy Cartoon or Cyanide & Happiness
- **Data/Stats** → Flat Icon Infographic
- **Stories** → 3D Clay Render

### ⏱️ Timing Considerations

**Flow AI rate limits:**
- 30s between prompts (enforced by tool)
- ~60s generation time per image
- Total: ~20 scenes = ~40 minutes

**Plan accordingly** - don't start right before a deadline!

### 📁 Project Organization

**Keep projects clean:**
```
projects/
├── finance_tips_v1/
│   └── images/
├── finance_tips_v2/    ← Use version numbers
│   └── images/
└── productivity_hacks/
    └── images/
```

**Delete old attempts** to save disk space.

---

## 🎓 Example Workflow

Here's a complete example from start to finish:

### Input
```
Project: passive_income_myths
Script: "Everyone says passive income is easy. Just set it and forget it, right? Wrong. 
         Here are 3 myths that keep people broke..."
Style: Clean Vector Stickman (3)
Reference: "simple stick figure with briefcase"
```

### Output
```
projects/passive_income_myths/
└── images/
    ├── 001.png  ← "Everyone says passive income is easy..."
    ├── 002.png  ← "Just set it and forget it, right? Wrong."
    ├── 003.png  ← "Here are 3 myths that keep people broke..."
    └── ...
```

### Next Steps
1. Import images into video editor (DaVinci Resolve, Premiere, etc.)
2. Match images to narration timestamps
3. Add voiceover (ElevenLabs integration coming soon!)
4. Export final video

---

## 📞 Need Help?

**Check these resources:**
1. `README.md` - Quick reference
2. `GITHUB_SETUP.md` - Deployment guide
3. GitHub Issues - Report bugs
4. Test scripts - Isolate problems

**Common questions:**
- "How long does it take?" → 5-40 mins depending on script length
- "Can I edit prompts?" → Yes! Edit the Google Sheet before generation
- "Can I re-download images?" → Yes! Use `test_flow_download.py`

---

**Happy automating! 🚀**

*Made with ❤️ by the Vyntrix Team*
