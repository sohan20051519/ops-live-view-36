import re
import time
from playwright.sync_api import sync_playwright, Page, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Increase the default timeout
    page.set_default_timeout(15000)

    try:
        # --- 1. Verify Signup Page ---
        print("Navigating to signup page...")
        page.goto("http://localhost:3000/signup")
        expect(page.get_by_text("Create an Account")).to_be_visible()
        print("Signup page loaded correctly.")
        page.screenshot(path="jules-scratch/verification/01_signup_page.png")

        # --- 2. Verify Login Page ---
        print("Navigating to login page...")
        page.goto("http://localhost:3000/login")
        expect(page.get_by_text("Welcome Back")).to_be_visible()
        print("Login page loaded correctly.")
        page.screenshot(path="jules-scratch/verification/02_login_page.png")

        print("Verification of authentication pages complete.")

    except Exception as e:
        print(f"An error occurred during verification: {e}")
        page.screenshot(path="jules-scratch/verification/error.png")
    finally:
        print("Closing browser.")
        browser.close()

with sync_playwright() as playwright:
    run(playwright)