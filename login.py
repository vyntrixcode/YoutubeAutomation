"""
Login Script - One-time Gmail authentication for all Google OAuth services
Run this once to login to Gmail, then all services (ChatGPT, Gemini, Kimi) will be authenticated
"""

import os
import sys
import pickle
import time
from pathlib import Path
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print("Error: .env file not found.")
    sys.exit(1)

# Paths
COOKIES_DIR = Path(__file__).parent / "cookies"
COOKIES_DIR.mkdir(exist_ok=True)


def setup_driver_with_profile() -> webdriver.Chrome:
    """Setup driver with persistent profile for cookie storage"""
    chrome_options = Options()
    
    # Create persistent profile directory
    profile_dir = Path(__file__).parent / "chrome_profile"
    profile_dir.mkdir(exist_ok=True)
    
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def login_to_gmail(driver: webdriver.Chrome, email: str, password: str) -> bool:
    """Login to Gmail - this authenticates Google account for all OAuth services"""
    print(f"\n{'='*60}")
    print("STEP 1: Logging into Gmail (Google Account)")
    print(f"{'='*60}")
    print("This will authenticate you for ChatGPT, Gemini, Kimi, and Sheets")
    
    try:
        # Go to Google account login
        driver.get("https://accounts.google.com/signin")
        time.sleep(3)
        
        # Check if already logged in
        if "myaccount.google.com" in driver.current_url or "mail.google.com" in driver.current_url:
            print("Already logged into Google account!")
            return True
        
        # Enter email
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_field.send_keys(email)
            email_field.send_keys(Keys.RETURN)
            print(f"Email entered: {email}")
            time.sleep(2)
        except Exception as e:
            print(f"Email field issue: {e}")
            print("You may already be on password screen or logged in")
        
        # Enter password
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            print("Password entered")
            time.sleep(3)
        except Exception as e:
            print(f"Password field issue: {e}")
            print("Checking login status...")
        
        # Wait for login to complete
        time.sleep(5)
        
        # Check if logged in
        if "accounts.google.com" not in driver.current_url:
            print("Gmail/Google login successful!")
            # Save Google cookies
            cookies_file = COOKIES_DIR / "google_cookies.pkl"
            pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
            print(f"Google cookies saved")
            return True
        else:
            print("Still on Google login page - may need 2FA or manual intervention")
            print("Please complete login manually in the browser...")
            input("Press Enter when done...")
            return True
            
    except Exception as e:
        print(f"Error during Gmail login: {e}")
        print("Please complete login manually...")
        input("Press Enter when done...")
        return True


def visit_service(driver: webdriver.Chrome, service_name: str, url: str, check_selector: str = None):
    """Visit a service to establish session cookies (already authenticated via Google)"""
    print(f"\n{'='*60}")
    print(f"STEP: Visiting {service_name.upper()}")
    print(f"{'='*60}")
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Check if logged in
        if check_selector:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, check_selector))
                )
                print(f"{service_name} is ready (authenticated via Google)")
            except:
                print(f"{service_name} may need manual login - check the browser")
                if input("Is login complete? (y/n): ").lower() != 'y':
                    print("Please complete login manually...")
                    input("Press Enter when done...")
        else:
            print(f"Visited {service_name}")
        
        # Save cookies for this service
        cookies_file = COOKIES_DIR / f"{service_name.lower().replace(' ', '_')}_cookies.pkl"
        pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
        print(f"{service_name} cookies saved")
        
        return True
        
    except Exception as e:
        print(f"Error visiting {service_name}: {e}")
        return False


def main():
    """Main login flow - Gmail first, then all services"""
    print("\n" + "="*60)
    print("LOGIN SCRIPT - Gmail -> All Services")
    print("="*60)
    print("\nThis script will:")
    print("1. Log you into Gmail (Google Account)")
    print("2. Visit ChatGPT, Gemini, Kimi (already authenticated)")
    print("3. Authorize Google Sheets and FLUX AI")
    print("\nYour session will be saved for main.py to reuse.")
    
    email = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_PASSWORD")
    
    if not email or not password:
        print("\nError: GMAIL_EMAIL and GMAIL_PASSWORD not found in .env")
        print("Please add them to your .env file:")
        print("  GMAIL_EMAIL=your.email@gmail.com")
        print("  GMAIL_PASSWORD=yourpassword")
        return
    
    driver = setup_driver_with_profile()
    
    try:
        # Step 1: Login to Gmail/Google (this authenticates all OAuth services)
        login_to_gmail(driver, email, password)
        
        # Step 2: Visit each service - they're already authenticated via Google OAuth
        services = [
            ("ChatGPT", "https://chat.openai.com", "#prompt-textarea"),
            ("Gemini", "https://gemini.google.com", "[contenteditable='true']"),
            ("Kimi", "https://kimi.moonshot.cn", "textarea"),
            ("Google Sheets", "https://sheets.new", None),
            ("Google Flow AI", "https://labs.google/fx/tools/flow/", None),
        ]
        
        for service_name, url, selector in services:
            visit_service(driver, service_name, url, selector)
            time.sleep(2)
        
        print("\n" + "="*60)
        print("ALL SERVICES READY!")
        print("="*60)
        print(f"\nCookies saved to: {COOKIES_DIR}")
        print("\nYou can now run: python main.py")
        print("It will reuse these authenticated sessions.")
        print("\nNote: Run this script again if cookies expire.")
        
        input("\nPress Enter to close the browser...")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
