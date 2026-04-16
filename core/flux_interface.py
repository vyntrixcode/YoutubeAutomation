"""
FLUX AI Image Generator
Uses Selenium to interact with FLUX AI web interface
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


class FLUXInterface:
    """Selenium-based interface for FLUX AI (flux1.ai)"""
    
    def __init__(self, driver: webdriver.Chrome, max_retries: int = 3):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 60)
        self.max_retries = max_retries
        self.base_url = "https://flux1.ai"
        
    def open_flux(self):
        """Open FLUX AI website"""
        print("Opening FLUX AI...")
        self.driver.get(self.base_url)
        time.sleep(3)
        
        # Check if we need to log in (should already be logged in via Google if using same session)
        try:
            # Look for sign in button
            sign_in = self.driver.find_elements(By.XPATH, "//button[contains(., 'Sign in')]")
            if sign_in:
                print("Please sign in to FLUX AI with Google (same account)...")
                input("Press Enter after signing in...")
        except:
            pass
    
    def create_project(self, project_name: str, reference_image_path: str = None, 
                       reference_prompt: str = None):
        """Create new project with optional character reference"""
        try:
            print(f"Creating new project: {project_name}")
            
            # Look for Create/Start New Project button
            create_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Create') or contains(., 'New Project')]"))
            )
            create_btn.click()
            
            time.sleep(2)
            
            # Enter project name if field exists
            try:
                name_field = self.driver.find_element(By.XPATH, "//input[@placeholder*='project' or @placeholder*='name']")
                name_field.clear()
                name_field.send_keys(project_name)
            except:
                pass
            
            # Upload reference image if provided
            if reference_image_path and os.path.exists(reference_image_path):
                try:
                    upload_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                    upload_input.send_keys(os.path.abspath(reference_image_path))
                    print(f"Uploaded reference image: {reference_image_path}")
                    time.sleep(3)
                except Exception as e:
                    print(f"Could not upload reference image: {e}")
            
            # Add reference prompt if provided
            if reference_prompt:
                try:
                    prompt_field = self.driver.find_element(By.XPATH, "//textarea[@placeholder*='character' or @placeholder*='reference']")
                    prompt_field.send_keys(reference_prompt)
                except:
                    pass
            
            # Start/Create project
            try:
                start_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'Start') or contains(., 'Create')]")
                start_btn.click()
            except:
                pass
            
            time.sleep(3)
            print(f"Project '{project_name}' created")
            
        except Exception as e:
            print(f"Error creating project: {e}")
    
    def generate_image(self, prompt: str, output_path: str, attempt: int = 1) -> bool:
        """
        Generate single image with retry logic
        Returns True if successful
        """
        try:
            print(f"Generating image (attempt {attempt}/{self.max_retries}): {prompt[:50]}...")
            
            # Find prompt input
            prompt_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//textarea[@placeholder*='prompt' or @placeholder*='describe']"))
            )
            
            # Clear and enter prompt
            prompt_input.clear()
            prompt_input.send_keys(prompt)
            
            time.sleep(1)
            
            # Click generate button
            generate_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Generate') or contains(@aria-label, 'Generate')]"))
            )
            generate_btn.click()
            
            # Wait for generation (check for loading indicator or result)
            print("Waiting for image generation...")
            time.sleep(15)  # Base generation time
            
            # Wait for completion
            max_wait = 180
            waited = 15
            while waited < max_wait:
                try:
                    # Check if still generating
                    loading = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Generating') or contains(@class, 'loading')]")
                    if not loading:
                        break
                    time.sleep(3)
                    waited += 3
                except:
                    break
            
            # Find and download the generated image
            image_url = self._extract_image_url()
            
            if image_url:
                return self._download_image(image_url, output_path)
            else:
                raise Exception("Could not find generated image")
                
        except Exception as e:
            print(f"Generation failed: {e}")
            
            if attempt < self.max_retries:
                print(f"Retrying... (attempt {attempt + 1})")
                time.sleep(5)
                return self.generate_image(prompt, output_path, attempt + 1)
            else:
                print(f"Max retries reached for: {prompt[:50]}...")
                return False
    
    def _extract_image_url(self) -> str:
        """Extract image URL from generated result"""
        try:
            # Look for generated image
            # FLUX typically shows the image in an img tag or canvas
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='flux'], img[class*='result'], canvas")
            
            for img in img_elements:
                src = img.get_attribute("src")
                if src and (src.startswith("http") or src.startswith("data:image")):
                    return src
            
            # Try finding download button and get its href
            download_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'image') or contains(@download, '')]")
            for link in download_links:
                href = link.get_attribute("href")
                if href:
                    return href
            
            return None
            
        except Exception as e:
            print(f"Error extracting image URL: {e}")
            return None
    
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
    
    def generate_all_images(self, prompts: List[Dict], output_folder: str, 
                           reference_image: str = None, reference_prompt: str = None):
        """Generate all images from prompts list"""
        # Create project
        project_name = Path(output_folder).name
        self.create_project(project_name, reference_image, reference_prompt)
        
        successful = 0
        failed = 0
        
        for i, item in enumerate(prompts, 1):
            prompt = item.get("prompt", "")
            scene_num = item.get("scene_number", i)
            
            output_path = os.path.join(output_folder, f"{i:03d}.jpg")
            
            print(f"\n[{i}/{len(prompts)}] Scene {scene_num}")
            
            if self.generate_image(prompt, output_path):
                successful += 1
            else:
                failed += 1
            
            # Small delay between generations
            time.sleep(3)
        
        print(f"\n{'='*50}")
        print(f"Generation complete: {successful} successful, {failed} failed")
        print(f"{'='*50}")
        
        return successful, failed
