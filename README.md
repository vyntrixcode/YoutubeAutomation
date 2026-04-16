# 🎬 Vyntrix Automation

> **Fully automated YouTube content generation pipeline** — from script to polished video assets in minutes.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Selenium](https://img.shields.io/badge/selenium-4.0+-green.svg)](https://www.selenium.dev/)

---

## ✨ Features

🤖 **AI-Powered Script Processing**
- Automatically converts YouTube scripts into scene-by-scene breakdowns
- Uses ChatGPT or Kimi AI via web automation
- Generates detailed image prompts for each scene

📊 **Google Sheets Integration**
- Auto-creates organized spreadsheets for each project
- Stores scene numbers, timestamps, narration, and image prompts
- Reliable clipboard-based data filling (handles UTF-8 correctly)

🎨 **Image Generation (Google Flow AI)**
- Batch image generation with 30-second intervals
- Smart image detection and filtering
- Reverse-order download (last generated = 001.png)
- Character consistency via reference prompts

🎵 **Text-to-Speech (Coming Soon)**
- ElevenLabs API integration
- Automatic audio generation for narration

📁 **Smart Asset Organization**
- Automatic project folder creation
- Organized image and audio storage
- Sequential file naming (001.png, 002.png, etc.)

---

## 🚀 Quick Start

### 1️⃣ Prerequisites

- **Python 3.8+** installed
- **Google Chrome** browser
- **Active Google account** (for Sheets and Flow AI)
- **ChatGPT or Kimi AI account**

### 2️⃣ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/vyntrix-automation.git
cd vyntrix-automation

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ Run

```bash
python main.py
```

**That's it!** The tool will:
1. Display the Vyntrix logo
2. Prompt you for project name and script
3. Let you choose a visual style (6 options)
4. Auto-login to ChatGPT/Kimi
5. Generate scene prompts
6. Save to Google Sheets
7. Generate images via Flow AI
8. Download and organize everything

---

## 🎨 Visual Styles

Choose from **6 professional styles**:

| # | Style | Description |
|---|-------|-------------|
| 1 | **Ultra Realistic B-Roll** | Photorealistic stock footage aesthetic |
| 2 | **Sloppy Handwritten Cartoon** | Messy, energetic marker doodle style |
| 3 | **Clean Vector Stickman** | Minimal corporate explainer graphics |
| 4 | **Minimal Flat Icon Infographic** | Modern flat design with bold icons |
| 5 | **3D Soft Clay Render** | Pixar-like smooth clay characters |
| 6 | **Cyanide & Happiness** | Simple, iconic webcomic style |

---

## 📂 Project Structure

```
vyntrix-automation/
├── main.py                      # 🚀 Main entry point
├── requirements.txt             # 📦 Python dependencies
├── chrome_profile/              # 🔐 Persistent browser session
├── core/
│   ├── script_processor.py      # 🤖 LLM integration
│   ├── sheets_manager.py        # 📊 Google Sheets automation
│   ├── flow_interface.py        # 🎨 Flow AI automation
│   ├── tts_engine.py            # 🎵 Text-to-speech (future)
│   └── asset_organizer.py       # 📁 File management
├── test_sheets.py               # 🧪 Test Sheets filling
├── test_flow_download.py        # 🧪 Test Flow AI downloads
└── projects/
    └── [project_name]/
        ├── images/              # 🖼️ Generated images
        │   ├── 001.png
        │   ├── 002.png
        │   └── ...
        └── audio/               # 🎵 Generated audio (future)
```

---

## 🛠️ How It Works

### **Step 1: Script → Scene Prompts**
```
Your Script → ChatGPT/Kimi AI → Structured CSV
```
The AI breaks your script into scenes with:
- Scene numbers
- Timestamps (0:00-0:05, 0:05-0:10, etc.)
- Narration text
- Detailed image prompts

### **Step 2: Save to Google Sheets**
```
CSV Data → Google Sheets (via clipboard paste)
```
Creates a new sheet named `[project]_prompts` with all data organized in columns.

### **Step 3: Generate Images**
```
Prompts → Google Flow AI → Batch Generation → Download
```
- Submits all prompts with 30s intervals
- Waits for generation to complete
- Auto-scrolls to load all images
- Downloads in reverse order (newest = 001.png)

---

## ⚙️ Advanced Configuration

### Character Consistency

Add a **reference prompt** for main characters:
```
Reference Prompt: "bald round-headed simple stick figure with dot eyes"
```
This gets appended to all main character scenes automatically.

### Custom Scene Duration

Default: 5 seconds per scene  
Modify in script or via prompt input.

### LLM Selection

Choose between:
- **ChatGPT** (default) - Better quality, stricter limits
- **Kimi AI** - More permissive, Chinese interface

---

## 🐛 Troubleshooting

### **Sheet stays empty after paste**
**Solution:** Install `pyperclip` for proper UTF-8 encoding
```bash
pip install pyperclip
```

### **Images download in wrong order**
The tool automatically downloads in **reverse order** (last generated = 001.png). This is intentional and correct.

### **"Prompt must be provided" error in Flow AI**
The tool simulates proper mouse clicks and input events. If this persists, Flow AI's UI may have changed.

### **Login issues**
- Complete 2FA manually when prompted
- The tool uses a **persistent Chrome profile** to save sessions
- First run may require manual login

### **Character encoding issues (â€™ instead of ')**
Install `pyperclip`:
```bash
pip install pyperclip
```

---

## 📋 Requirements

See `requirements.txt`:
- `selenium` - Browser automation
- `webdriver-manager` - Auto ChromeDriver setup
- `python-dotenv` - Environment variables
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `Pillow` - Image processing
- `pyperclip` - Clipboard operations (recommended)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a pull request

---

## 📜 License

MIT License - feel free to use for personal or commercial projects.

---

## 🙏 Credits

Built with:
- **Selenium** - Web automation
- **Google Flow AI** - Image generation
- **ChatGPT/Kimi** - Script processing
- **Google Sheets** - Data organization

---

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check `USER_GUIDE.md` for detailed instructions
- Review `GITHUB_SETUP.md` for deployment tips

---

**Made with ❤️ by the Vyntrix Team**
