"""
Script to Image Prompts Generator
Uses Selenium to interact with ChatGPT/Kimi/Gemini web interface
"""

import os
import time
import re
import emoji
import csv
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


@dataclass
class Scene:
    number: int
    time_start: str
    time_end: str
    narration: str  # The actual sentence/segment being narrated
    prompt: str     # The image generation prompt


class LLMInterface:
    """Selenium-based interface for ChatGPT/Kimi/Gemini"""
    
    def __init__(self, provider: str = "chatgpt", headless: bool = False):
        self.provider = provider.lower()
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def _setup_driver(self):
        """Initialize Chrome driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 30)
        
    def _get_login_url(self) -> str:
        if self.provider == "chatgpt":
            return "https://chat.openai.com/auth/login"
        elif self.provider == "kimi":
            return "https://kimi.moonshot.cn/"
        elif self.provider == "gemini":
            return "https://gemini.google.com/"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def login_with_google(self, email: str, password: str):
        """Login using Google OAuth"""
        self._setup_driver()
        
        print(f"Opening {self.provider} login page...")
        self.driver.get(self._get_login_url())
        
        # Wait for and click Google sign-in button
        try:
            if self.provider == "chatgpt":
                # ChatGPT specific login flow
                google_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Google')]"))
                )
                google_btn.click()
            elif self.provider == "kimi":
                # Kimi specific login flow
                google_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Google') or contains(@class, 'google')]"))
                )
                google_btn.click()
            elif self.provider == "gemini":
                # Gemini may already be logged in via Google account, check for sign in button
                try:
                    sign_in_btn = self.driver.find_element(By.XPATH, "//a[contains(., 'Sign in')]")
                    sign_in_btn.click()
                    time.sleep(2)
                    # Look for Google sign in on the next page
                    google_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Google')]"))
                    )
                    google_btn.click()
                except:
                    # Already logged in or different flow
                    pass
            
            # Handle Google OAuth popup
            time.sleep(2)
            
            # Switch to Google auth window if popup opened
            main_window = self.driver.current_window_handle
            for handle in self.driver.window_handles:
                if handle != main_window:
                    self.driver.switch_to.window(handle)
                    break
            
            # Enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_field.send_keys(email)
            email_field.send_keys(Keys.RETURN)
            
            time.sleep(2)
            
            # Enter password
            password_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            
            time.sleep(3)
            
            # Switch back to main window
            self.driver.switch_to.window(main_window)
            
            # Wait for login to complete
            time.sleep(5)
            
            print(f"Successfully logged into {self.provider}")
            
        except Exception as e:
            print(f"Login error: {e}")
            print("Please complete login manually in the browser...")
            input("Press Enter when logged in...")
    
    def send_prompt(self, prompt: str) -> str:
        """Send prompt and get response - strips emojis to avoid BMP error"""
        try:
            # Strip emojis and non-BMP characters from prompt (ChromeDriver limitation)
            clean_prompt = emoji.replace_emoji(prompt, replace='')
            # Also remove other potential non-BMP characters
            clean_prompt = clean_prompt.encode('utf-16', 'surrogatepass').decode('utf-16', 'ignore')
            clean_prompt = clean_prompt.encode('utf-8', 'ignore').decode('utf-8')
            
            # Find text input area based on provider
            if self.provider == "chatgpt":
                textarea = self.wait.until(
                    EC.presence_of_element_located((By.ID, "prompt-textarea"))
                )
            elif self.provider == "gemini":
                # Gemini uses a div contenteditable
                try:
                    textarea = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true']"))
                    )
                except:
                    textarea = self.wait.until(
                        EC.presence_of_element_located((By.TAG_NAME, "textarea"))
                    )
            else:  # kimi
                textarea = self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "textarea"))
                )
            
            # Clear the field
            textarea.clear()
            time.sleep(0.5)
            
            # For Gemini, use JavaScript to set value directly (faster, more reliable)
            if self.provider == "gemini":
                self.driver.execute_script("arguments[0].innerText = arguments[1]", textarea, clean_prompt)
                time.sleep(0.5)
                # Trigger input event
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }))", textarea)
            else:
                # Send in chunks only for non-Gemini providers
                if len(clean_prompt) > 1000:
                    for i in range(0, len(clean_prompt), 1000):
                        chunk = clean_prompt[i:i+1000]
                        textarea.send_keys(chunk)
                        time.sleep(0.1)
                else:
                    textarea.send_keys(clean_prompt)
            
            # Send with Ctrl+Enter for Gemini (sometimes needed)
            if self.provider == "gemini":
                from selenium.webdriver.common.action_chains import ActionChains
                print("  Submitting with Ctrl+Enter for Gemini...")
                time.sleep(0.5)
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.RETURN).key_up(Keys.CONTROL).perform()
                time.sleep(0.5)
                # Also try regular Enter as fallback
                try:
                    textarea.send_keys(Keys.RETURN)
                except:
                    pass
            else:
                print("  Pressing Enter to submit...")
                textarea.send_keys(Keys.RETURN)
                time.sleep(0.5)
                # Try again to make sure
                textarea.send_keys(Keys.RETURN)
            
            print("Prompt sent, waiting for response...")
            
            # Wait for response to complete
            time.sleep(5)
            
            # Wait for response to complete (check for stop button disappearing)
            max_wait = 180  # 3 minutes max
            waited = 5
            last_response_len = 0
            stable_count = 0
            
            while waited < max_wait:
                try:
                    # Check if still generating (stop button present)
                    stop_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'Stop')]")
                    # Still generating, wait
                    time.sleep(2)
                    waited += 2
                    if waited % 10 == 0:
                        print(f"  Still generating... ({waited}s)")
                except:
                    # No stop button - check if response is stable (done)
                    try:
                        # Get current response length
                        if self.provider == "chatgpt":
                            messages = self.driver.find_elements(By.CSS_SELECTOR, "[data-message-author-role='assistant']")
                            if messages:
                                current_len = len(messages[-1].text)
                            else:
                                current_len = 0
                        elif self.provider == "gemini":
                            # For Gemini, check response container
                            responses = self.driver.find_elements(By.CSS_SELECTOR, "[data-test-id='conversation-turn'], .response-container, .model-response")
                            if responses:
                                current_len = len(responses[-1].text)
                            else:
                                current_len = 0
                        else:
                            current_len = last_response_len + 1  # Force continue
                        
                        # If response length hasn't changed for 3 checks, it's done
                        if current_len == last_response_len:
                            stable_count += 1
                            if stable_count >= 3:
                                print(f"  Response complete (detected after {waited}s)")
                                break
                        else:
                            stable_count = 0
                            last_response_len = current_len
                            
                        time.sleep(2)
                        waited += 2
                        
                    except Exception as e:
                        # If we can't check, assume done after reasonable time
                        if waited >= 30:
                            print(f"  Assuming complete (waited {waited}s)")
                            break
                        time.sleep(2)
                        waited += 2
            
            print(f"Response generation complete (waited {waited}s)")
            
            # Get response based on provider
            if self.provider == "chatgpt":
                messages = self.driver.find_elements(By.CSS_SELECTOR, "[data-message-author-role='assistant']")
                if messages:
                    return messages[-1].text
            elif self.provider == "gemini":
                # Try multiple selectors for Gemini response
                selectors = [
                    ".response-content",
                    "[data-test-id='response-content']",
                    ".message-content",
                    ".chat-content",
                    "[role='presentation'] .markdown",
                    ".answer-content"
                ]
                for selector in selectors:
                    messages = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if messages:
                        text = messages[-1].text
                        if text and len(text) > 50:  # Make sure we got actual content
                            return text
                # Fallback: try to get all text from response area
                try:
                    response_area = self.driver.find_element(By.CSS_SELECTOR, ".conversation-container, .chat-container, main")
                    return response_area.text
                except:
                    pass
            else:  # kimi
                messages = self.driver.find_elements(By.CSS_SELECTOR, ".chat-message-content, .message-content, .markdown-body")
                if messages:
                    return messages[-1].text
            
            return ""
            
        except Exception as e:
            print(f"Error sending prompt: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()


class ScriptToPromptsConverter:
    """Converts YouTube scripts to image generation prompts"""
    
    # Visual styles mapping
    STYLES = {
        "1": {
            "name": "Ultra Realistic B-Roll",
            "prompt_prefix": "high-resolution photo of",
            "prompt_suffix": "natural lighting, real-world setting, detailed textures, documentary look"
        },
        "2": {
            "name": "Sloppy Handwritten Cartoon",
            "prompt_prefix": "messy hand-drawn doodle",
            "prompt_suffix": "black marker outline, white background, simple flat color fill, childlike doodle aesthetic, slightly uneven lines"
        },
        "3": {
            "name": "Clean Vector Stickman",
            "prompt_prefix": "minimal vector illustration",
            "prompt_suffix": "clean white background, simple black stick figure, flat design, minimal facial expressions, clean geometric shapes, no shading, corporate explainer look"
        },
        "4": {
            "name": "Minimal Flat Icon Infographic",
            "prompt_prefix": "flat infographic icon",
            "prompt_suffix": "white or light neutral background, modern minimal design, bold clean shapes, vector icon style, clean geometry, slight drop shadows"
        },
        "5": {
            "name": "3D Soft Clay Render Style",
            "prompt_prefix": "3D clay render",
            "prompt_suffix": "soft studio lighting, rounded smooth shapes, pastel color palette, Pixar-like softness, smooth surfaces, white studio background"
        },
        "6": {
            "name": "Cyanide & Happiness",
            "prompt_prefix": "Cyanide and Happiness style",
            "prompt_suffix": "bald round-headed character, simple black dot eyes, clean digital 2D cartoon, thick black outlines, subtle gradient shading, dramatic single-source lighting, exaggerated pose, muted color palette, webcomic aesthetic",
            "full_description": """- Bald round-headed characters with simple black dot eyes and minimal facial features
- Clean digital cartoon style with smooth outlines
- Slightly muted color palette (beige skin tones, navy blues, grays)
- Expressive body language and exaggerated poses
- Simple environmental details with subtle gradients
- Dark room settings with single light sources creating dramatic shadows
- Characters wear simple clothing (t-shirts, suits, hoodies)
- Webcomic aesthetic with thick clean black outlines
- Minimalist backgrounds that suggest location without clutter
- Characters show emotion through eyebrow angles and mouth shapes

Use phrasing like:
- "Cyanide and Happiness style"
- "bald round-headed character"
- "simple black dot eyes"
- "clean digital 2D cartoon"
- "thick black outlines"
- "subtle gradient shading"
- "dramatic single-source lighting"
- "exaggerated pose"
- "muted color palette"
- "webcomic aesthetic"""
        }
    }
    
    def __init__(self, llm_interface: LLMInterface, style_id: str = "6", scene_duration: int = 6):
        self.llm = llm_interface
        self.style = self.STYLES.get(style_id, self.STYLES["6"])
        self.scene_duration = scene_duration
        
    def create_system_prompt(self) -> str:
        """Generate the system prompt for LLM - requesting CSV format"""
        return f"""TASK: Convert the YouTube script below into a CSV table.

You are a visual breakdown engine for a {self.style['name']} style YouTube channel.

---

### WHAT YOU MUST DO:

1. Read the script carefully
2. Break it into segments of 8-15 words (about 6 seconds each)
3. For EACH segment, create ONE image generation prompt
4. Output as CSV with 4 columns

---

### CSV FORMAT (COPY THIS EXACTLY):

Scene #,Time,Narration,Image Prompt
1,0:00-0:06,"Exact narration text","Image prompt here with {self.style['prompt_prefix']} style"
2,0:06-0:12,"Exact narration text","Image prompt here"
3,0:12-0:18,"Exact narration text","Image prompt here"

RULES:
- Use COMMAS to separate columns
- Put narration text in DOUBLE QUOTES
- Time format: M:SS-M:SS
- Start Scene # at 1
- Do NOT add any text before or after the CSV
- Do NOT explain what you're doing
- Just output the CSV table immediately

---

### STYLE TO USE:

{self.style['name']}

Include these in every image prompt: {self.style['prompt_prefix']}, {self.style['prompt_suffix']}

---

### SCRIPT TO PROCESS:
"""
    
    def convert_script(self, script: str, reference_prompt: str = None) -> List[Scene]:
        """Convert full script to list of scene prompts"""
        
        # Find which style number was selected
        style_id = None
        for sid, sdata in self.STYLES.items():
            if sdata['name'] == self.style['name']:
                style_id = sid
                break
        
        full_prompt = f"""You are a visual breakdown engine for a white-background explainer YouTube channel.

Your task is to convert a full script into structured image generation prompts.

---

### INPUT:

Full Script:

{script}



Selected Visual Style (Choose One): {style_id} ({self.style['name']})

1. Ultra Realistic B-Roll
2. Sloppy Handwritten Cartoon
3. Clean Vector Stickman
4. Minimal Flat Icon Infographic
5. 3D Soft Clay Render Style
6. Cyanide & Happiness

---

### YOUR TASK:

1. Break the script into visual segments based on time.
2. Generate one visual prompt for every {self.scene_duration} seconds of narration.
3. Assume narration speed of ~150 words per minute.
4. Each visual prompt should represent only what is currently being said.
5. Do NOT include narration text in the prompt.
6. Do NOT summarize the entire paragraph into one image.
7. Maintain visual consistency across all prompts.

---

# 🔒 STRUCTURE RULES

- Label each prompt numerically.
- Format like this:

Scene 1 (0:00–0:06):

[Image Prompt]

Scene 2 (0:06–0:12):

[Image Prompt]

- Continue until the script is fully covered.
- No commentary.
- No explanation.
- Only scene labels + prompts.

---

# 🎨 VISUAL STYLE RULES

The visual tone MUST change based on selected style:

---

### 1️⃣ Ultra Realistic B-Roll

- Photorealistic
- Natural lighting
- Real-world environments
- Documentary look
- No text overlays
- No white background unless context demands it
- Feels like stock footage photography

Use phrasing like:

- "high-resolution photo of…"
- "natural lighting"
- "real-world setting"
- "detailed textures"

---

### 2️⃣ Sloppy Handwritten Cartoon

- White background
- Messy black marker outlines
- Childlike doodle aesthetic
- Slightly uneven lines
- Simple flat colors
- Minimal shading
- Looks hand-drawn

Use phrasing like:

- "messy hand-drawn doodle"
- "black marker outline"
- "white background"
- "simple flat color fill"

---

### 3️⃣ Clean Vector Stickman

- Pure white background
- Simple black stick figures
- Minimal facial expressions
- Clean geometric shapes
- Flat vector style
- Very minimal detail
- No shading
- Corporate explainer look

Use phrasing like:

- "minimal vector illustration"
- "clean white background"
- "simple black stick figure"
- "flat design"

---

### 4️⃣ Minimal Flat Icon Infographic

- White or light neutral background
- Flat design icons
- Bold simple colors
- Clean geometry
- Modern infographic style
- Slight drop shadows allowed
- No complex detail

Use phrasing like:

- "flat infographic icon"
- "modern minimal design"
- "bold clean shapes"
- "vector icon style"

---

### 5️⃣ 3D Soft Clay Render Style

- White studio background
- Soft lighting
- Rounded clay-like objects
- Pastel colors
- Subtle shadows
- Pixar-like softness
- Smooth surfaces

Use phrasing like:

- "3D clay render"
- "soft studio lighting"
- "rounded smooth shapes"
- "pastel color palette"

---

### 6️⃣ Cyanide & Happiness

- Bald round-headed characters with simple black dot eyes and minimal facial features
- Clean digital cartoon style with smooth outlines
- Slightly muted color palette (beige skin tones, navy blues, grays)
- Expressive body language and exaggerated poses
- Simple environmental details with subtle gradients
- Dark room settings with single light sources creating dramatic shadows
- Characters wear simple clothing (t-shirts, suits, hoodies)
- Webcomic aesthetic with thick clean black outlines
- Minimalist backgrounds that suggest location without clutter
- Characters show emotion through eyebrow angles and mouth shapes

Use phrasing like:

- "Cyanide and Happiness style"
- "bald round-headed character"
- "simple black dot eyes"
- "clean digital 2D cartoon"
- "thick black outlines"
- "subtle gradient shading"
- "dramatic single-source lighting"
- "exaggerated pose"
- "muted color palette"
- "webcomic aesthetic"

---

# 🧠 VISUAL CONSISTENCY RULE

- Keep characters consistent across scenes.
- Keep proportions consistent.
- Avoid style drift.
- No sudden changes in tone.
- No text inside images unless absolutely necessary.
- Each image must clearly represent what's being said in that {self.scene_duration}-second window.

# 📊 CSV OUTPUT FORMAT

Convert the scenes into this exact CSV format:

Scene #,Time,Narration,Image Prompt
1,0:00-0:{self.scene_duration:02d},"Exact narration text here","Full image prompt text here"
2,0:{self.scene_duration:02d}-0:{self.scene_duration*2:02d},"Exact narration text here","Full image prompt text here"
3,0:{self.scene_duration*2:02d}-0:{self.scene_duration*3:02d},"Exact narration text here","Full image prompt text here"

Rules:
- Use commas to separate the 4 columns
- Put narration text in double quotes
- Put image prompt in double quotes
- Time format: M:SS-M:SS
- Each scene is {self.scene_duration} seconds long
- Start Scene # at 1
- Include the CSV header line

---

# 🚫 OUTPUT RULES

- Output ONLY the CSV table.
- No commentary.
- No meta explanation.
- No emojis.
- No extra formatting.
- No text before or after the CSV.



BEGIN CSV OUTPUT:"""
        
        print(f"Sending script to {self.llm.provider.upper()} ({len(script)} chars, {len(script.split())} words)...")
        print(f"Selected style: {style_id} ({self.style['name']})")
        
        response = self.llm.send_prompt(full_prompt)
        
        # Debug: Save raw response
        if response:
            print(f"\nReceived response ({len(response)} chars)")
            # Save response for debugging
            debug_file = Path(__file__).parent.parent / "last_llm_response.txt"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(response)
            print(f"Raw response saved to: {debug_file}")
            
            # Show first 200 chars
            print(f"Response preview: {response[:200]}...")
        else:
            print("ERROR: No response received from LLM")
        
        return self._parse_scenes(response)
    
    def _get_style_rules(self) -> str:
        """Get the detailed style rules for the selected style"""
        style_rules = {
            "Ultra Realistic B-Roll": """### Ultra Realistic B-Roll
- Photorealistic
- Natural lighting
- Real-world environments
- Documentary look
- No text overlays
- No white background unless context demands it
- Feels like stock footage photography

Use phrasing like:
- "high-resolution photo of..."
- "natural lighting"
- "real-world setting"
- "detailed textures""",
            
            "Sloppy Handwritten Cartoon": """### Sloppy Handwritten Cartoon
- White background
- Messy black marker outlines
- Childlike doodle aesthetic
- Slightly uneven lines
- Simple flat colors
- Minimal shading
- Looks hand-drawn

Use phrasing like:
- "messy hand-drawn doodle"
- "black marker outline"
- "white background"
- "simple flat color fill""",
            
            "Clean Vector Stickman": """### Clean Vector Stickman
- Pure white background
- Simple black stick figures
- Minimal facial expressions
- Clean geometric shapes
- Flat vector style
- Very minimal detail
- No shading
- Corporate explainer look

Use phrasing like:
- "minimal vector illustration"
- "clean white background"
- "simple black stick figure"
- "flat design"
- "corporate explainer style"
- "no shading"
- "minimal detail""",
            
            "Minimal Flat Icon Infographic": """### Minimal Flat Icon Infographic
- White or light neutral background
- Flat design icons
- Bold simple colors
- Clean geometry
- Modern infographic style
- Slight drop shadows allowed
- No complex detail

Use phrasing like:
- "flat infographic icon"
- "modern minimal design"
- "bold clean shapes"
- "vector icon style""",
            
            "3D Soft Clay Render Style": """### 3D Soft Clay Render Style
- White studio background
- Soft lighting
- Rounded clay-like objects
- Pastel colors
- Subtle shadows
- Pixar-like softness
- Smooth surfaces

Use phrasing like:
- "3D clay render"
- "soft studio lighting"
- "rounded smooth shapes"
- "pastel color palette""",
            
            "Cyanide & Happiness": """### Cyanide & Happiness
- Bald round-headed characters with simple black dot eyes and minimal facial features
- Clean digital cartoon style with smooth outlines
- Slightly muted color palette (beige skin tones, navy blues, grays)
- Expressive body language and exaggerated poses
- Simple environmental details with subtle gradients
- Dark room settings with single light sources creating dramatic shadows
- Characters wear simple clothing (t-shirts, suits, hoodies)
- Webcomic aesthetic with thick clean black outlines
- Minimalist backgrounds that suggest location without clutter
- Characters show emotion through eyebrow angles and mouth shapes

Use phrasing like:
- "Cyanide and Happiness style"
- "bald round-headed character"
- "simple black dot eyes"
- "clean digital cartoon"
- "thick black outlines"
- "subtle gradient shading"
- "dramatic single-source lighting"
- "exaggerated pose"
- "muted color palette"
- "webcomic aesthetic"""
        }
        
        return style_rules.get(self.style['name'], style_rules["Clean Vector Stickman"])
    
    def _parse_scenes(self, response: str) -> List[Scene]:
        """Parse LLM CSV response into Scene objects"""
        scenes = []
        
        if not response or not response.strip():
            print("ERROR: Empty response from LLM")
            return scenes
        
        lines = response.split('\n')
        
        # Find header line
        header_idx = -1
        for i, line in enumerate(lines):
            if 'Scene #' in line or 'Scene' in line:
                header_idx = i
                break
        
        if header_idx == -1:
            print("ERROR: Could not find CSV header in response")
            print("First 500 chars of response:", response[:500])
            return scenes
        
        # Parse data rows (skip header)
        for line in lines[header_idx + 1:]:
            line = line.strip()
            if not line:
                continue
            
            # Skip markdown separators
            if line.startswith('|---') or line.startswith('|--') or line.startswith('```'):
                continue
            
            # Parse CSV row
            try:
                # Handle quoted fields with commas
                parts = self._parse_csv_line(line)
                
                if len(parts) >= 4:
                    scene_num = int(parts[0].strip())
                    time_range = parts[1].strip()
                    narration = parts[2].strip().strip('"')
                    prompt = parts[3].strip().strip('"')
                    
                    # Parse time range
                    time_range_clean = time_range.replace('–', '-').replace('—', '-')
                    time_parts = time_range_clean.split('-')
                    if len(time_parts) == 2:
                        time_start = time_parts[0].strip()
                        time_end = time_parts[1].strip()
                    else:
                        time_start = time_range
                        time_end = time_range
                    
                    scenes.append(Scene(
                        number=scene_num,
                        time_start=time_start,
                        time_end=time_end,
                        narration=narration,
                        prompt=prompt
                    ))
            except Exception as e:
                print(f"Warning: Could not parse line: {line[:80]}... Error: {e}")
                continue
        
        print(f"Parsed {len(scenes)} scenes from LLM CSV response")
        return scenes
    
    def _parse_csv_line(self, line: str) -> List[str]:
        """Parse a CSV line handling quoted fields"""
        result = []
        current = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                result.append(current.strip())
                current = ""
            else:
                current += char
        
        # Don't forget the last field
        if current.strip():
            result.append(current.strip())
        
        return result
    
    def _get_reference_prompt_note(self, reference_prompt: str = None) -> str:
        """Generate FINAL NOTE section for reference prompt if provided"""
        if reference_prompt:
            return f"""---

# FINAL NOTE

For scenes where the main character appears, include this reference in the image prompt:

"{reference_prompt}"

Use this reference to maintain character consistency across all character scenes."""
        return ""
