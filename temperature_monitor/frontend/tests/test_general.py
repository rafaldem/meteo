import re
from playwright.sync_api import Page, expect

# Base URL configuration
BASE_URL = "http://localhost:5000"  # Adjust to your Flask app's URL


def test_homepage_loads(page: Page):
    """Test that the homepage loads successfully"""
    page.goto(BASE_URL)

    # Check that the page title contains expected text
    expect(page).to_have_title(re.compile(".*Flask App.*"))

    # Check for important elements
    expect(page.locator("h1")).to_be_visible()


def test_navigation(page: Page):
    """Test navigation between pages"""
    page.goto(BASE_URL)

    # Find and click a navigation link
    page.click("text=About")

    # Verify navigation succeeded
    expect(page).to_have_url(re.compile(".*about.*"))
    expect(page.locator("h1")).to_contain_text("About")


def test_login_form(page: Page):
    """Test login form validation and submission"""
    page.goto(f"{BASE_URL}/login")

    # Test form validation
    page.click("button[type=submit]")
    expect(page.locator(".error-message")).to_be_visible()

    # Fill in the form
    page.fill("input[name=username]", "testuser")
    page.fill("input[name=password]", "password123")

    # Submit the form
    page.click("button[type=submit]")

    # Verify successful login
    expect(page).to_have_url(BASE_URL)
    expect(page.locator(".user-info")).to_contain_text("testuser")


def test_data_loading(page: Page):
    """Test that dynamic data loads correctly"""
    page.goto(f"{BASE_URL}/dashboard")

    # Wait for data to load
    page.wait_for_selector(".data-table")

    # Verify data is present
    expect(page.locator(".data-table tr")).to_have_count(5)
    expect(page.locator(".data-table")).to_contain_text("Sample Data")


def test_form_submission(page: Page):
    """Test creating a new item via form submission"""
    page.goto(f"{BASE_URL}/items/new")

    # Fill the form
    page.fill("input[name=item-name]", "Test Item")
    page.fill("textarea[name=description]", "This is a test description")
    page.select_option("select[name=category]", "Category 1")

    # Submit the form
    page.click("button[type=submit]")

    # Verify success message
    expect(page.locator(".success-message")).to_be_visible()
    expect(page.locator(".success-message")).to_contain_text("Item created successfully")


def test_responsive_design(page: Page):
    """Test responsive design at different viewport sizes"""
    # Test mobile view
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)

    # Check that mobile menu is visible
    expect(page.locator(".mobile-menu-button")).to_be_visible()

    # Test desktop view
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(BASE_URL)

    # Check that desktop navigation is visible
    expect(page.locator("nav.desktop-nav")).to_be_visible()


def test_dark_mode_toggle(page: Page):
    """Test dark mode toggle functionality"""
    page.goto(BASE_URL)

    # Check initial theme
    expect(page.locator("body")).not_to_have_class("dark-theme")

    # Toggle dark mode
    page.click(".theme-toggle")

    # Verify dark mode is active
    expect(page.locator("body")).to_have_class("dark-theme")
