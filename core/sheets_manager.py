"""
Google Sheets Manager
Uses Selenium to interact with Google Sheets via logged-in session
"""

import time
import re
from typing import List, Dict
import time
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from core.script_processor import Scene


class SheetsManager:
    """Manages Google Sheets via Selenium automation"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)
        self.sheet_url = None
        
    def create_or_open_sheet(self, sheet_name: str) -> str:
        """Create new Google Sheet or open existing one"""
        print(f"Creating/accessing Google Sheet: {sheet_name}")
        
        # Go to Google Sheets
        self.driver.get("https://sheets.new")
        time.sleep(2)
        
        # Wait for sheet to load - minimal wait, rename ASAP
        print("  Waiting for sheet to load...")
        try:
            # Wait for title input to be available (means sheet is interactive)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[id='docs-title-widget'] input"))
            )
            print("  ✓ Sheet ready")
        except Exception as e:
            print(f"  ⚠ Waiting extra time: {e}")
            time.sleep(2)
        
        # Rename the sheet to project name
        try:
            # Click on the sheet name (usually "Untitled spreadsheet")
            title_element = self.driver.find_element(By.CSS_SELECTOR, "[id='docs-title-widget'] input, [aria-label*='Rename']")
            title_element.click()
            time.sleep(0.5)
            # Clear and type new name
            title_element.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.2)
            title_element.send_keys(sheet_name)
            time.sleep(0.5)
            title_element.send_keys(Keys.RETURN)
            time.sleep(0.3)
            print(f"  ✓ Renamed to: {sheet_name}")
            
            # Press ESCAPE to unfocus title
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.3)
        except Exception as e:
            print(f"  Could not rename sheet: {e}")
        
        # Store the sheet URL
        self.sheet_url = self.driver.current_url
        print(f"  Sheet URL: {self.sheet_url}")
        
        return self.sheet_url
    
    def setup_prompts_sheet(self):
        """Set up headers and add all data at once"""
        pass  # Will be done in add_scenes
    
    def add_scenes(self, scenes: List[Scene]):
        """Fill sheet using clipboard paste - ONLY method that works with Sheets data model"""
        try:
            print(f"Adding {len(scenes)} scenes to sheet...")
            
            def clean_cell(text: str) -> str:
                """Remove newlines and tabs that break TSV paste format"""
                return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
            
            # Build tab-separated rows
            rows = ["Scene #\tTime\tNarration\tPrompt"]
            
            for scene in scenes:
                time_range = f"{scene.time_start}-{scene.time_end}"
                narration = clean_cell(scene.narration)
                prompt = clean_cell(scene.prompt)
                
                rows.append(f"{scene.number}\t{time_range}\t{narration}\t{prompt}")
            
            csv_text = "\n".join(rows)
            
            print(f"  Filling {len(rows)} rows via clipboard paste...")
            
            # Copy to clipboard
            clipboard_success = False
            try:
                import pyperclip
                pyperclip.copy(csv_text)
                clipboard_success = True
                print("  ✓ Copied to clipboard (pyperclip)")
            except ImportError:
                # PowerShell fallback
                print("  pyperclip not available, trying PowerShell...")
                try:
                    import subprocess
                    # Use a temporary file approach with explicit UTF-8 encoding
                    temp_file = Path(__file__).parent.parent / "temp_clipboard.txt"
                    
                    # Write with UTF-8 BOM to ensure PowerShell reads correctly
                    with open(temp_file, 'w', encoding='utf-8-sig') as f:
                        f.write(csv_text)
                    
                    # PowerShell command with explicit UTF-8 encoding
                    ps_command = f'Get-Content -Path "{temp_file}" -Encoding UTF8 | Set-Clipboard'
                    result = subprocess.run(
                        ['powershell', '-NoProfile', '-Command', ps_command],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    # Clean up
                    temp_file.unlink()
                    clipboard_success = True
                    print("  ✓ Copied via PowerShell (UTF-8)")
                except Exception as ps_error:
                    print(f"  ✗ PowerShell failed: {ps_error}")
                    print("  ")
                    print("  ⚠ PowerShell has encoding issues with special characters!")
                    print("  RECOMMENDED: Install pyperclip for proper UTF-8 support")
                    print("  Run: pip install pyperclip")
            
            if not clipboard_success:
                raise Exception("Could not copy to clipboard. Install pyperclip: pip install pyperclip")
            
            # Navigate to A1 - CRITICAL: must be at A1 before paste
            print("  Navigating to cell A1...")
            time.sleep(2)  # Extra wait after sheet operations
            
            # Get current cell position before navigation
            def get_current_cell():
                try:
                    return self.driver.execute_script("""
                        var nameBox = document.querySelector('#docs-name-box-input, input[aria-label*=\"Name box\"]');
                        return nameBox ? nameBox.value : 'unknown';
                    """)
                except:
                    return 'unknown'
            
            current_pos = get_current_cell()
            print(f"  Current position: {current_pos}")
            
            # Method 1: Click A1 cell directly using JavaScript
            try:
                result = self.driver.execute_script("""
                    // Find A1 cell specifically
                    var cells = document.querySelectorAll('td.cell');
                    if (cells.length > 0) {
                        cells[0].click();
                        cells[0].focus();
                        return true;
                    }
                    return false;
                """)
                if result:
                    time.sleep(0.5)
                    print("  ✓ Clicked A1 cell")
            except Exception as e:
                print(f"  Could not click A1: {e}")
            
            # Method 2: Use name box to force A1
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.execute_script("""
                        var nameBox = document.querySelector('#docs-name-box-input, input[aria-label*=\"Name box\"]');
                        if (nameBox) {
                            nameBox.focus();
                            nameBox.select();
                            nameBox.value = 'A1';
                            
                            // Simulate Enter key press
                            var event = new KeyboardEvent('keypress', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true,
                                cancelable: true
                            });
                            nameBox.dispatchEvent(event);
                            
                            // Also try keydown
                            var event2 = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter', 
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            });
                            nameBox.dispatchEvent(event2);
                        }
                    """)
                    time.sleep(0.8)
                    
                    # Verify position
                    new_pos = get_current_cell()
                    print(f"  Position after navigation: {new_pos}")
                    
                    if new_pos == 'A1':
                        print(f"  ✓ Confirmed at A1")
                        break
                    else:
                        print(f"  ⚠ Still at {new_pos}, retrying...")
                        
                except Exception as e:
                    print(f"  Navigation attempt {attempt+1} failed: {e}")
                    
                if attempt == max_retries - 1:
                    print(f"  ⚠ Warning: Could not confirm A1 position")
            
            # Final check before paste
            final_pos = get_current_cell()
            if final_pos != 'A1':
                print(f"  ⚠ WARNING: Not at A1 (currently at {final_pos}), forcing one more time...")
                # Last resort: use keyboard navigation
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.CONTROL, Keys.HOME)
                time.sleep(0.5)
            
            # Paste
            print("  Pasting data...")
            body = self.driver.find_element(By.TAG_NAME, "body")
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL)
            actions.send_keys('v')
            actions.key_up(Keys.CONTROL)
            actions.perform()
            
            print(f"  ✓ Paste command sent")
            
            # Wait for Sheets to process (critical - sometimes lags)
            time.sleep(3)
            
            # Verify by checking if A1 has content
            try:
                first_cell_check = self.driver.execute_script("""
                    var cells = document.querySelectorAll('td.cell');
                    return cells.length > 0 && cells[0].textContent.trim() !== '';
                """)
                if first_cell_check:
                    print(f"  ✓ Verified: Data appears in sheet")
                else:
                    print(f"  ⚠ Warning: Sheet may still be empty")
            except:
                pass
            
            print(f"Added {len(scenes)} scenes to sheet")
            
        except Exception as e:
            print(f"✗ Error in add_scenes: {e}")
            import traceback
            traceback.print_exc()
    
    def read_prompts(self) -> List[Dict]:
        """Read prompts from sheet using clipboard copy (only reliable method)"""
        try:
            print("Reading prompts from sheet...")
            time.sleep(2)
            
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Select all
            body.send_keys(Keys.CONTROL, 'a')
            time.sleep(0.5)
            
            # Copy
            body.send_keys(Keys.CONTROL, 'c')
            time.sleep(0.5)
            
            # Get clipboard content
            try:
                import pyperclip
                raw = pyperclip.paste()
            except ImportError:
                # PowerShell fallback
                import subprocess
                result = subprocess.run(
                    ['powershell', '-command', 'Get-Clipboard'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                raw = result.stdout
            
            lines = raw.strip().split("\n")
            
            if len(lines) <= 1:
                print("  Sheet appears empty or only has headers")
                return []
            
            # Skip header row
            prompts = []
            
            for line in lines[1:]:
                cols = line.split("\t")
                
                if len(cols) < 4:
                    continue
                
                # Skip empty rows
                if not cols[0].strip():
                    continue
                
                prompts.append({
                    'scene_number': cols[0].strip(),
                    'time': cols[1].strip(),
                    'narration': cols[2].strip(),
                    'prompt': cols[3].strip()
                })
            
            print(f"Read {len(prompts)} prompts from sheet")
            return prompts
            
        except Exception as e:
            print(f"Error reading prompts: {e}")
            import traceback
            traceback.print_exc()
            return []
