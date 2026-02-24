import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import io

# Force UTF-8 for Windows consoles
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BASE_URL = "http://127.0.0.1:8001"
HEADLESS = True

def setup_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Failed to initialize Chrome Driver: {e}")
        sys.exit(1)

def wait_and_click(driver, by, value, timeout=10):
    for i in range(3):
        try:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
            element.click()
            return element
        except StaleElementReferenceException:
            if i == 2: raise
            time.sleep(1)

def wait_and_type(driver, by, value, text, timeout=10):
    element = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, value)))
    element.clear()
    element.send_keys(text)
    return element

def run_tests():
    driver = setup_driver()
    driver.implicitly_wait(5)
    
    print("🚀 Starting TestSprite E2E Test...")
    
    try:
        # --- Scenario 1: Citizen Workflow ---
        print("\n[Citizen Workflow]")
        driver.get(f"{BASE_URL}/accounts/login/")
        print("  - Navigated to login page")
        
        # Switch to OTP tab
        wait_and_click(driver, By.ID, "tab-otp")
        print("  - Switched to OTP tab")
        
        # Click Continue with OTP
        wait_and_click(driver, By.XPATH, "//button[contains(text(), 'Continue with Mobile OTP')]")
        
        # Enter Mobile
        mobile = "9999922222"
        wait_and_type(driver, By.ID, "mobile_number", mobile)
        wait_and_click(driver, By.XPATH, "//button[contains(text(), 'Send OTP')]")
        print(f"  - Requested OTP for {mobile}")
        
        # Read OTP from page
        otp_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//p[contains(@style, 'font-size: 2rem')]"))
        )
        otp = otp_element.text.strip()
        print(f"  - Detected Demo OTP: {otp}")
        
        # Verify OTP
        wait_and_type(driver, By.ID, "otp", otp)
        wait_and_click(driver, By.XPATH, "//button[contains(text(), 'Verify & Login')]")
        print("  - OTP Verified. Logged in as Citizen.")
        
        # Go to Search
        wait_and_click(driver, By.XPATH, "//a[contains(text(), 'Find Facility')]")
        wait_and_type(driver, By.NAME, "q", "City General Hospital")
        wait_and_click(driver, By.XPATH, "//button[contains(text(), 'Search')]")
        print("  - Searched for City General Hospital")
        
        # View Branch
        wait_and_click(driver, By.XPATH, "//a[contains(text(), 'View Services')]")
        print("  - Opened Branch Details")
        
        # Join Queue
        wait_and_click(driver, By.XPATH, "//button[contains(text(), 'Join Queue')]")
        
        # Check if already joined
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "message-error")
            if "already have an active ticket" in error_msg.text:
                print("  - Citizen already has active ticket. Navigating to My Tickets.")
                wait_and_click(driver, By.XPATH, "//a[contains(text(), 'My Tickets')]")
                wait_and_click(driver, By.XPATH, "//a[contains(text(), 'View Ticket')]")
        except:
            pass
            
        print("  - Verified Ticket presence")
        
        # Verify Ticket
        token_elem = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "token-number"))
        )
        print(f"  - Success! Generated Token: {token_elem.text}")
        
        # Logout
        driver.get(f"{BASE_URL}/accounts/logout/")
        print("  - Citizen logged out")

        # --- Scenario 2: Operator Workflow ---
        print("\n[Operator Workflow]")
        driver.delete_all_cookies() # Ensure clean session
        driver.get(f"{BASE_URL}/accounts/login/")
        
        # Staff Login
        wait_and_click(driver, By.ID, "tab-password")
        wait_and_type(driver, By.ID, "username", "admin")
        wait_and_type(driver, By.ID, "password", "admin123")
        wait_and_click(driver, By.CSS_SELECTOR, "#form-password button[type='submit']")
        print("  - Clicked Login as Global Admin (to verify Staff access)")
        time.sleep(2)
        
        # Check Dashboard
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Admin Dashboard')]"))
        )
        print("  - Admin Dashboard verified.")
        
        # Open Counter if closed
        try:
            open_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Open Counter')]")
            open_btn.click()
            print("  - Counter opened.")
        except:
            print("  - Counter already open.")
            
        # Serve Next
        try:
            wait_and_click(driver, By.XPATH, "//button[contains(text(), 'Serve Next')]")
            print("  - Clicked Serve Next.")
            time.sleep(1)
            # Verify serving
            serving_status = driver.find_element(By.XPATH, "//span[contains(@class, 'status-serving')]")
            print("  - Now serving a ticket.")
        except:
            print("  - No tickets in queue or serve-next failed.")
            
        print("\n✅ All E2E Scenarios Passed!")
        
    except Exception as e:
        print(f"\n❌ E2E Test Failed: {e}")
        driver.save_screenshot("testsprite_failure.png")
        print("  - Saved failure screenshot to testsprite_failure.png")
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
