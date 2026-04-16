"""
Google Flow AI Image Generator
Uses Selenium to interact with Google Flow (flow.google.com) web interface
"""

import os
import time
import re
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import requests
from pathlib import Path


class FlowInterface:
    """Selenium-based interface for Google Flow AI (labs.google.com/fx/tools/flow)"""
    
    def __init__(self, driver: webdriver.Chrome, max_retries: int = 3):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 60)
        self.max_retries = max_retries
        self.base_url = "https://labs.google/fx/tools/flow/"
        
    def open_flow(self):
        """Open Google Flow AI website and create new project"""
        print("Opening Google Flow AI...")
        self.driver.get(self.base_url)
        time.sleep(10)  # Wait longer for initial load
        
        # Check if we need to log in
        try:
            sign_in_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Sign in') or contains(., 'Get started')]")
            if sign_in_buttons:
                print("Please sign in to Google Flow with Google...")
                input("Press Enter after signing in...")
        except:
            pass
        
        # Wait for the page to fully load
        time.sleep(5)
        
        # Create new project - look for "New" button or similar
        print("Creating new project...")
        try:
            # Try different selectors for new/create buttons
            new_selectors = [
                "//button[contains(., 'New')]",
                "//button[contains(., 'Create')]",
                "//button[contains(@aria-label, 'New')]",
                "//a[contains(., 'New')]",
                "//div[contains(., 'New')]",
            ]
            
            for selector in new_selectors:
                try:
                    new_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    new_btn.click()
                    print("Clicked New/Create button")
                    time.sleep(3)
                    break
                except:
                    continue
            
            # Look for Flow tool option
            time.sleep(3)
            
        except Exception as e:
            print(f"Could not create new project automatically: {e}")
            print("Please create a new Flow project manually...")
            input("Press Enter when project is created...")
        
        # Wait for interface to load
        time.sleep(5)
        
        print("Google Flow AI is ready")
        time.sleep(3)
    
    def submit_prompt(self, prompt: str) -> bool:
        """Submit a prompt to Flow AI (does NOT wait for generation or download)"""
        try:
            
            # Wait for interface to be ready
            time.sleep(2)
            
            
            # Find prompt input - try multiple selectors for Flow AI
            prompt_selectors = [
                "textarea[placeholder*='Describe']",
                "textarea[placeholder*='describe']",
                "textarea[placeholder*='prompt']",
                "input[placeholder*='Describe']",
                "input[placeholder*='describe']",
                "[contenteditable='true']",
                "textarea",
                "input[type='text']",
            ]
            
            prompt_input = None
            used_selector = None
            for selector in prompt_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        if el.is_displayed() and el.is_enabled():
                            # Check if it's in the main input area (not a search box)
                            prompt_input = el
                            used_selector = selector
                            break
                    if prompt_input:
                        break
                except:
                    continue
            
            if not prompt_input:
                print("Could not find prompt input field - trying manual mode")
                print("Please paste the prompt manually and press Enter...")
                input("Press Enter when ready...")
                return False
            
            # Simulate proper mouse click event on textbox
            print(f"  Found input field (using: {used_selector})")
            print(f"  Simulating mouse click on textbox...")
            
            # Get element position and simulate real mouse click
            location = prompt_input.location
            size = prompt_input.size
            x = location['x'] + size['width'] / 2
            y = location['y'] + size['height'] / 2
            
            # Move to element and click (simulates real mouse movement)
            ActionChains(self.driver).move_to_element(prompt_input).pause(0.3).click().pause(0.5).perform()
            
            # Alternative: use JavaScript to dispatch actual click events
            self.driver.execute_script("""
                const el = arguments[0];
                const clickEvent = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                el.dispatchEvent(clickEvent);
                el.focus();
            """, prompt_input)
            time.sleep(1)
            
            print(f"  Entering prompt...")
            
            # Clear existing content
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(0.3)
            
            # Type the prompt
            prompt_input.send_keys(prompt)
            time.sleep(1)
            
            print(f"  Typed {len(prompt)} characters, pressing Enter...")
            
            # Press Enter to submit
            prompt_input.send_keys(Keys.RETURN)
            time.sleep(2)
            
            return True
                
        except Exception as e:
            print(f"  ✗ Prompt submission failed: {e}")
            return False
    
    def _save_generated_image(self, output_path: str) -> bool:
        """Try to save the generated image with multiple methods"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Method 1: Look for download button and click it
            try:
                download_btns = self.driver.find_elements(By.XPATH, "//button[contains(., 'Download') or contains(@aria-label, 'Download')]")
                if download_btns:
                    print("  Clicking download button...")
                    download_btns[0].click()
                    time.sleep(3)
                    # Image downloaded to Downloads folder - need to move it
                    # For now, continue to other methods
            except:
                pass
            
            # Method 2: Find generated images in gallery (exclude profile pics in header)
            try:
                # Scroll page to load all images
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                # Get all images
                all_imgs = self.driver.find_elements(By.TAG_NAME, "img")
                gallery_imgs = []
                
                print(f"  Found {len(all_imgs)} total images, filtering...")
                
                for img in all_imgs:
                    try:
                        # Get actual displayed size
                        width = img.size.get('width', 0)
                        height = img.size.get('height', 0)
                        src = img.get_attribute("src")
                        
                        # Skip small images (profile pics, icons)
                        if width < 150 or height < 150:
                            continue
                        
                        # Skip images in header/nav (profile pics are usually in top area)
                        location = img.location
                        y_position = location.get('y', 0)
                        
                        # Profile pics are typically in top 100px, generated images are lower
                        if y_position < 100:
                            continue
                        
                        # Check if image is in main content area (not header)
                        if src and len(src) > 20:
                            gallery_imgs.append({
                                'area': width * height,
                                'width': width,
                                'height': height,
                                'y': y_position,
                                'img': img,
                                'src': src
                            })
                            print(f"    Candidate: {width}x{height} at y={y_position}")
                    except:
                        continue
                
                if gallery_imgs:
                    # Sort by Y position (top to bottom), then by area (largest first)
                    gallery_imgs.sort(key=lambda x: (x['y'], -x['area']))
                    
                    # Take the first gallery image (topmost large image in content area)
                    target = gallery_imgs[0]
                    src = target['src']
                    
                    print(f"  Selected image: {target['width']}x{target['height']} at y={target['y']}")
                    
                    if src.startswith("data:image"):
                        # Base64 image
                        import base64
                        header, encoded = src.split(",", 1)
                        data = base64.b64decode(encoded)
                        with open(output_path, "wb") as f:
                            f.write(data)
                        print(f"  Saved from base64 data")
                        return True
                    elif src.startswith("http"):
                        # Download from URL
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                        response = requests.get(src, headers=headers, timeout=30)
                        response.raise_for_status()
                        with open(output_path, "wb") as f:
                            f.write(response.content)
                        print(f"  Downloaded from URL")
                        return True
            except Exception as e:
                print(f"  Gallery image method failed: {e}")
            
            # Method 3: Screenshot the image element
            try:
                img_element = self.driver.find_element(By.CSS_SELECTOR, "img[src], canvas")
                img_element.screenshot(output_path)
                print(f"  Saved screenshot of image element")
                return True
            except:
                pass
            
            # Method 4: Right-click and inspect for image
            try:
                # Use JavaScript to find the largest image on page
                img_url = self.driver.execute_script("""
                    let imgs = Array.from(document.querySelectorAll('img'));
                    imgs = imgs.filter(img => img.src && img.naturalWidth > 100);
                    if (imgs.length > 0) {
                        imgs.sort((a, b) => (b.naturalWidth * b.naturalHeight) - (a.naturalWidth * a.naturalHeight));
                        return imgs[0].src;
                    }
                    return null;
                """)
                
                if img_url:
                    if img_url.startswith("http"):
                        response = requests.get(img_url, timeout=30)
                        with open(output_path, "wb") as f:
                            f.write(response.content)
                        print(f"  Downloaded largest image")
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"Error saving image: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_all_images(self, prompts: List[Dict], output_folder: str, reference_image: str = None, reference_prompt: str = None) -> List[str]:
        """Generate all images then download at end
        
        Workflow:
        1. Submit all prompts (30s between each)
        2. Wait 90s for final images to finish
        3. Refresh page
        4. Download ALL images in reverse order
        """
        print(f"\n{'='*60}")
        print(f"GENERATING {len(prompts)} IMAGES")
        print(f"{'='*60}")
        
        # Step 1: Submit all prompts
        for i, prompt_data in enumerate(prompts):
            scene_num = i + 1
            prompt_text = prompt_data.get('prompt', '')
            
            # Add reference prompt to main character scenes if provided
            if reference_prompt and self._is_main_character_scene(prompt_text):
                prompt_text = f"{prompt_text}. {reference_prompt}"
            
            print(f"\n[{scene_num}/{len(prompts)}] Submitting prompt for scene {scene_num}...")
            print(f"  Prompt: {prompt_text[:80]}...")
            
            success = self.submit_prompt(prompt_text)
            
            if not success:
                print(f"  ✗ Failed to submit prompt for scene {scene_num}")
            else:
                print(f"  ✓ Prompt submitted successfully")
            
            # Wait 30 seconds between prompts
            if scene_num < len(prompts):
                print(f"\n  ⏳ Waiting 30 seconds before next prompt...")
                for remaining in range(30, 0, -5):
                    print(f"     {remaining}s remaining...", end="\r")
                    time.sleep(5)
                print("     Ready for next prompt!" + " " * 20)  # Clear line
        
        # Step 2: Wait for final generation to complete
        print(f"\n{'='*60}")
        print(f"All prompts submitted! Waiting 90s for final images...")
        print(f"{'='*60}")
        time.sleep(90)
        
        # Step 3: Refresh page to load all images
        print("\nRefreshing page to load all generated images...")
        current_project_url = self.driver.current_url
        print(f"  Current Flow project: {current_project_url}")
        self.driver.refresh()
        time.sleep(5)
        
        # Step 4: Download ALL images (automatically using current Flow URL)
        print(f"\n{'='*60}")
        print(f"AUTO-DOWNLOADING ALL IMAGES FROM CURRENT PROJECT")
        print(f"{'='*60}")
        print(f"Using project URL: {current_project_url}")
        saved_images = self.download_all_generated_images(output_folder, len(prompts))
        
        print(f"\n{'='*60}")
        print(f"COMPLETE: {len(saved_images)}/{len(prompts)} images downloaded")
        print(f"{'='*60}")
        
        return saved_images
    
    def download_all_generated_images(self, output_folder: str, total_expected: int) -> List[str]:
        """Download all already-generated images from Flow AI project
        Downloads in REVERSE order: last generated image = 001.png
        """
        saved_images = []
        
        print(f"\nDownloading {total_expected} generated images...")
        
        # Scroll gradually to load all lazy-loaded images
        print("  Scrolling to load all images...")
        
        # Scroll down in steps to trigger lazy loading
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        scroll_step = 300  # pixels per step
        
        while current_position < total_height:
            current_position += scroll_step
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(0.3)  # Small delay to let images load
        
        # Final scroll to absolute bottom
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Scroll back to top gradually
        current_position = total_height
        while current_position > 0:
            current_position -= scroll_step
            self.driver.execute_script(f"window.scrollTo(0, {max(0, current_position)});")
            time.sleep(0.2)
        
        # Final scroll to absolute top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Find all generated images in gallery
        all_imgs = self.driver.find_elements(By.TAG_NAME, "img")
        gallery_imgs = []
        
        for img in all_imgs:
            try:
                width = img.size.get('width', 0)
                height = img.size.get('height', 0)
                location = img.location
                y_position = location.get('y', 0)
                
                # Filter: large images below header area
                if width > 150 and height > 150 and y_position > 100:
                    src = img.get_attribute("src")
                    if src and len(src) > 20:
                        gallery_imgs.append({
                            'y': y_position,
                            'img': img,
                            'src': src,
                            'width': width,
                            'height': height
                        })
            except:
                continue
        
        print(f"  Found {len(gallery_imgs)} generated images")
        
        # Sort by Y position (top to bottom)
        gallery_imgs.sort(key=lambda x: x['y'])
        
        # REVERSE ORDER: last image generated (at bottom) = 001
        gallery_imgs.reverse()
        
        # Download each image
        for i, img_data in enumerate(gallery_imgs[:total_expected]):
            scene_num = i + 1
            filename = f"{scene_num:03d}.png"
            output_path = os.path.join(output_folder, filename)
            
            src = img_data['src']
            print(f"  [{scene_num}/{total_expected}] Downloading {filename}... ({img_data['width']}x{img_data['height']})")
            
            try:
                if src.startswith("data:image"):
                    import base64
                    header, encoded = src.split(",", 1)
                    data = base64.b64decode(encoded)
                    with open(output_path, "wb") as f:
                        f.write(data)
                    saved_images.append(output_path)
                    print(f"    ✓ Saved from base64")
                    
                elif src.startswith("http"):
                    # Try downloading with browser cookies (for authenticated APIs)
                    try:
                        # Get browser cookies
                        cookies = self.driver.get_cookies()
                        session = requests.Session()
                        for cookie in cookies:
                            session.cookies.set(cookie['name'], cookie['value'])
                        
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": self.driver.current_url
                        }
                        response = session.get(src, headers=headers, timeout=30)
                        response.raise_for_status()
                        with open(output_path, "wb") as f:
                            f.write(response.content)
                        saved_images.append(output_path)
                        print(f"    ✓ Downloaded from URL")
                    except Exception as download_error:
                        # If download fails, use screenshot method
                        print(f"    Download failed ({str(download_error)[:50]}), using screenshot...")
                        img_data['img'].screenshot(output_path)
                        saved_images.append(output_path)
                        print(f"    ✓ Saved via screenshot")
                else:
                    # Screenshot fallback
                    img_data['img'].screenshot(output_path)
                    saved_images.append(output_path)
                    print(f"    ✓ Saved via screenshot")
                    
            except Exception as e:
                print(f"    ✗ Failed: {e}")
        
        return saved_images
    
    def _extract_image_url(self) -> str:
        """Extract image URL from generated result"""
        try:
            # Google Flow typically shows images in various ways
            # Try multiple selectors
            selectors = [
                "img[src*='googleusercontent']",
                "img[src*='flow']",
                "img[class*='image']",
                "img[class*='result']",
                "canvas",
                "img[alt*='generated']",
                "img[alt*='image']",
            ]
            
            for selector in selectors:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for img in img_elements:
                    src = img.get_attribute("src")
                    if src and (src.startswith("http") or src.startswith("data:image")):
                        return src
            
            # Try finding download links
            download_selectors = [
                "//a[contains(@href, 'image')]",
                "//a[contains(@download, '')]",
                "//button[contains(., 'Download')]",
            ]
            
            for selector in download_selectors:
                links = self.driver.find_elements(By.XPATH, selector)
                for link in links:
                    href = link.get_attribute("href")
                    if href and href.startswith("http"):
                        return href
            
            return None
            
        except Exception as e:
            print(f"Error extracting image URL: {e}")
            return None
    
    def _save_image_via_screenshot(self, output_path: str) -> bool:
        """Fallback: Save image by finding the image element and taking its screenshot"""
        try:
            # Find the main generated image
            img_selectors = [
                "img[src*='googleusercontent']",
                "img[class*='image']",
                "img[class*='result']",
                "canvas",
            ]
            
            for selector in img_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Take screenshot of the image element
                    elements[0].screenshot(output_path)
                    print(f"Image saved via screenshot: {output_path}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Screenshot fallback failed: {e}")
            return False
    
    def _download_image(self, image_url: str, output_path: str) -> bool:
        """Download and save image"""
        try:
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if image_url.startswith("data:image"):
                # Handle base64 encoded image
                import base64
                header, encoded = image_url.split(",", 1)
                data = base64.b64decode(encoded)
                with open(output_path, "wb") as f:
                    f.write(data)
            else:
                # Download from URL
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(image_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    f.write(response.content)
            
            print(f"Image saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False
    
    
    def _is_main_character_scene(self, prompt: str) -> bool:
        """Check if prompt likely contains main character"""
        character_keywords = ['character', 'person', 'man', 'woman', 'figure', 'protagonist', 'hero', 'stickman', 'stick figure']
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in character_keywords)
