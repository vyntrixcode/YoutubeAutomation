"""
Main orchestrator for YouTube automation workflow
"""

import os
import sys
import time
import pickle
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from core.script_processor import LLMInterface, ScriptToPromptsConverter
from core.sheets_manager import SheetsManager
from core.flow_interface import FlowInterface
from core.tts_engine import TTSEngine
from core.asset_organizer import AssetOrganizer


def setup_driver(headless: bool = False, use_profile: bool = True) -> webdriver.Chrome:
    """Initialize Chrome driver with optional persistent profile"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Use persistent profile for cookie/session persistence
    if use_profile:
        profile_dir = Path(__file__).parent / "chrome_profile"
        profile_dir.mkdir(exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def load_cookies(driver: webdriver.Chrome, service_name: str):
    """Load saved cookies for a service"""
    cookies_file = Path(__file__).parent / "cookies" / f"{service_name}_cookies.pkl"
    if cookies_file.exists():
        try:
            cookies = pickle.load(open(cookies_file, "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass  # Some cookies may fail to add
            print(f"Loaded cookies for {service_name}")
            return True
        except Exception as e:
            print(f"Could not load cookies: {e}")
    return False


def step1_script_to_prompts(script: str, driver: webdriver.Chrome, style_id: str, scene_duration: int = 6, reference_prompt: str = None) -> list:
    """Convert script to image prompts via LLM using existing driver with profile"""
    print("\n" + "="*60)
    print("STEP 1: Converting Script to Image Prompts")
    print("="*60)
    
    # Initialize LLM interface with existing driver
    llm_provider = os.getenv("LLM_PROVIDER", "chatgpt")
    llm = LLMInterface(provider=llm_provider, headless=False)
    
    # Use existing driver (already has profile loaded)
    llm.driver = driver
    llm.wait = WebDriverWait(driver, 30)
    
    # Navigate to the LLM site
    driver.get(llm._get_login_url())
    time.sleep(3)
    
    # Check if already logged in (profile persists)
    try:
        # Try to find input area - if found, we're logged in
        if llm.provider == "chatgpt":
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "prompt-textarea"))
            )
        elif llm.provider == "gemini":
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true'], textarea"))
            )
        else:  # kimi
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "textarea"))
            )
        print(f"Already logged into {llm_provider} (session persisted)")
    except:
        print(f"Not logged into {llm_provider} - please run: python login.py")
        print("Or complete login manually in the browser...")
        input("Press Enter when logged in...")
    
    # Convert script with scene duration and reference prompt
    converter = ScriptToPromptsConverter(llm, style_id=style_id, scene_duration=scene_duration)
    scenes = converter.convert_script(script, reference_prompt=reference_prompt)
    
    print(f"\nGenerated {len(scenes)} scene prompts")
    return scenes


def step2_save_to_sheets(scenes: list, project_name: str, driver: webdriver.Chrome) -> str:
    """Save prompts to Google Sheets"""
    print("\n" + "="*60)
    print("STEP 2: Saving to Google Sheets")
    print("="*60)
    
    sheets = SheetsManager(driver)
    sheet_url = sheets.create_or_open_sheet(f"{project_name}_prompts")
    sheets.setup_prompts_sheet()
    sheets.add_scenes(scenes)
    
    return sheet_url


def step3_generate_images(project_name: str, prompts: list, driver: webdriver.Chrome,
                          reference_image: str = None, reference_prompt: str = None):
    """Generate images from prompts via Google Flow AI"""
    print("\n" + "="*60)
    print("STEP 3: Generating Images via Google Flow AI")
    print("="*60)
    
    # Create folders
    organizer = AssetOrganizer()
    folders = organizer.create_project(project_name)
    
    # Initialize Flow AI
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    flow = FlowInterface(driver, max_retries=max_retries)
    flow.open_flow()
    
    # Generate all images
    flow.generate_all_images(
        prompts=prompts,
        output_folder=str(folders["images"]),
        reference_image=reference_image,
        reference_prompt=reference_prompt
    )


def step4_generate_audio(script: str, project_name: str, words_per_segment: int = 150):
    """Generate audio segments via ElevenLabs"""
    print("\n" + "="*60)
    print("STEP 4: Generating Audio (TTS)")
    print("="*60)
    
    # Initialize TTS
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    if not api_key or not voice_id:
        print("Error: ElevenLabs credentials not found in .env")
        return
    
    tts = TTSEngine(api_key, voice_id)
    
    # Get/create project folder
    organizer = AssetOrganizer()
    folders = organizer.create_project(project_name)
    
    # Segment script
    segments = tts.segment_script(script, words_per_segment)
    
    # Generate audio
    tts.generate_all_audio(segments, str(folders["audio"]))


def step5_show_summary(project_name: str):
    """Display final asset summary"""
    print("\n" + "="*60)
    print("STEP 5: Asset Summary")
    print("="*60)
    
    organizer = AssetOrganizer()
    print(organizer.get_summary(project_name))


def print_logo():
    """Display stylish Vyntrix Automation logo"""
    logo = r"""
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
║                                                              ║
║           YouTube Content Generation Workflow                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print("\033[96m" + logo + "\033[0m")  # Cyan color
    print()


def main():
    """Main workflow orchestrator"""
    print_logo()
    # Load environment variables
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print("Error: .env file not found. Please copy .env.example to .env and fill in your credentials.")
        return
    
    # Get user input
    print("\n" + "="*60)
    print("YouTube Automation Tool")
    print("="*60)
    
    project_name = input("\nEnter project name: ").strip()
    if not project_name:
        print("Project name is required.")
        return
    
    # Get script - improved input handling
    print("\nEnter your YouTube script.")
    print("Type your script and press Enter twice (blank line) when done:")
    print("-" * 60)
    
    script_lines = []
    empty_line_count = 0
    
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_line_count += 1
                if empty_line_count >= 2:  # Two empty lines = end
                    break
                script_lines.append(line)
            else:
                empty_line_count = 0
                script_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    script = "\n".join(script_lines).strip()
    
    if not script.strip():
        print("Script is required.")
        return
    
    # Select LLM Provider
    print("\nSelect LLM Provider for Script-to-Prompts:")
    print("1. ChatGPT (chat.openai.com)")
    print("2. Gemini (gemini.google.com)")
    print("3. Kimi (kimi.moonshot.cn)")
    
    llm_choice = input("\nEnter LLM choice (1-3) [default: 1]: ").strip() or "1"
    llm_providers = {"1": "chatgpt", "2": "gemini", "3": "kimi"}
    llm_provider = llm_providers.get(llm_choice, "chatgpt")
    
    # Store in environment for later use
    os.environ["LLM_PROVIDER"] = llm_provider
    
    # Select visual style
    print("\nSelect Visual Style:")
    print("1. Ultra Realistic B-Roll")
    print("2. Sloppy Handwritten Cartoon")
    print("3. Clean Vector Stickman")
    print("4. Minimal Flat Icon Infographic")
    print("5. 3D Soft Clay Render Style")
    print("6. Cyanide (Cartoon like Cyanide & Happiness)")
    
    style_choice = input("\nEnter style number (1-6) [default: 6]: ").strip() or "6"
    
    # Scene duration setting
    print("\nScene Duration (seconds per scene):")
    print("This affects how the script is segmented.")
    scene_duration = input("Enter seconds per scene [default: 6]: ").strip() or "6"
    try:
        scene_duration = int(scene_duration)
    except:
        scene_duration = 6
    print(f"Using {scene_duration} seconds per scene")
    
    # Optional reference
    print("\nOptional: Reference image path for consistent character (press Enter to skip):")
    reference_image = input("Path: ").strip() or None
    
    print("\nOptional: Reference character prompt (press Enter to skip):")
    reference_prompt = input("Prompt: ").strip() or None
    
    # Voice generation toggle
    print("\nGenerate Voice Over (ElevenLabs TTS)?")
    voice_choice = input("Enter yes/no [default: yes]: ").strip().lower()
    generate_voice = voice_choice in ("", "yes", "y", "true")
    
    words_per_segment = 150
    if generate_voice:
        # Get words per segment
        default_words = os.getenv("WORDS_PER_SEGMENT", "150")
        words_input = input(f"\nWords per audio segment [default: {default_words}]: ").strip()
        words_per_segment = int(words_input) if words_input.isdigit() else int(default_words)
    
    # Confirm workflow
    print("\n" + "="*60)
    print("WORKFLOW SUMMARY")
    print("="*60)
    print(f"Project: {project_name}")
    print(f"LLM: {llm_provider.upper()}")
    print(f"Style: {style_choice}")
    print(f"Scene duration: {scene_duration} seconds")
    print(f"Script length: {len(script.split())} words")
    print(f"Reference image: {reference_image if reference_image else 'None'}")
    print(f"Generate voice: {'Yes' if generate_voice else 'No'}")
    if generate_voice:
        print(f"Words per segment: {words_per_segment} (~{words_per_segment/150:.1f} min)")
    
    confirm = input("\nProceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return
    
    # Initialize driver with persistent profile
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    driver = setup_driver(headless=False, use_profile=True)  # Always use profile for auth persistence
    
    print("\n" + "="*60)
    print("NOTE: If login is required, run: python login.py")
    print("="*60)
    
    try:
        # Execute workflow
        scenes = step1_script_to_prompts(script, driver, style_choice, scene_duration, reference_prompt)
        
        if not scenes:
            print("Error: No scenes generated.")
            return
        
        sheet_url = step2_save_to_sheets(scenes, project_name, driver)
        print(f"\nPrompts saved to: {sheet_url}")
        
        # Read prompts from the sheet (not from scenes directly)
        from core.sheets_manager import SheetsManager
        sheets = SheetsManager(driver)
        # Navigate to the sheet first
        driver.get(sheet_url)
        time.sleep(2)
        prompts = sheets.read_prompts()
        
        if not prompts:
            print("Warning: Could not read prompts from sheet, falling back to scenes data")
            prompts = [
                {"scene_number": s.number, "prompt": s.prompt}
                for s in scenes
            ]
        
        step3_generate_images(project_name, prompts, driver, reference_image, reference_prompt)
        
        if generate_voice:
            step4_generate_audio(script, project_name, words_per_segment)
        else:
            print("\n" + "="*60)
            print("STEP 4: Skipping Audio Generation (user opted out)")
            print("="*60)
        
        step5_show_summary(project_name)
        
        print("\n" + "="*60)
        print("ALL DONE! Your assets are ready for editing.")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == "__main__":
    main()
