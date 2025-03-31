import re
from playwright.sync_api import Page, expect

# Base URL configuration
BASE_URL = "http://localhost:5000"  # Adjust to your Flask app's URL


def test_homepage_loads(page: Page):
    """Test that the temperature monitor homepage loads successfully"""
    page.goto(BASE_URL)

    # Check that the page title contains expected text
    expect(page).to_have_title(re.compile(".*Temperature Monitor.*"))

    # Check for important elements
    expect(page.locator(".dashboard-header")).to_be_visible()
    expect(page.locator("#temperature-chart")).to_be_visible()


def test_navigation(page: Page):
    """Test navigation between temperature data views"""
    page.goto(BASE_URL)

    # Find and click navigation links for different time periods
    page.click("text=Daily View")
    expect(page).to_have_url(re.compile(".*daily.*"))
    expect(page.locator("#daily-temperature-data")).to_be_visible()

    page.click("text=Weekly View")
    expect(page).to_have_url(re.compile(".*weekly.*"))
    expect(page.locator("#weekly-temperature-data")).to_be_visible()

    page.click("text=Monthly View")
    expect(page).to_have_url(re.compile(".*monthly.*"))
    expect(page.locator("#monthly-temperature-data")).to_be_visible()

    page.click("text=Yearly View")
    expect(page).to_have_url(re.compile(".*yearly.*"))
    expect(page.locator("#yearly-temperature-data")).to_be_visible()


def test_temperature_data_loading(page: Page):
    """Test that temperature data loads correctly"""
    page.goto(f"{BASE_URL}/dashboard")

    # Wait for temperature data to load
    page.wait_for_selector(".temperature-table")

    # Verify temperature data is present
    expect(page.locator(".temperature-table tbody tr")).to_have_count.greater_than(0)
    expect(page.locator(".temperature-table")).to_contain_text("Temperature")
    expect(page.locator(".temperature-table")).to_contain_text("Date")


def test_date_range_selection(page: Page):
    """Test custom date range selection for temperature data"""
    page.goto(f"{BASE_URL}/custom-range")

    # Fill the date range form
    page.fill("#start-date", "2023-01-01")
    page.fill("#end-date", "2023-01-31")

    # Submit the form
    page.click("#submit-date-range")

    # Verify custom range data is displayed
    page.wait_for_selector("#custom-range-results")
    expect(page.locator("#custom-range-results")).to_be_visible()
    expect(page.locator(".temperature-chart")).to_be_visible()
    expect(page.locator(".date-range-info")).to_contain_text("Jan 01, 2023 - Jan 31, 2023")


def test_temperature_visualization(page: Page):
    """Test temperature visualization features"""
    page.goto(f"{BASE_URL}/visualizations")

    # Test changing chart type
    page.select_option("#chart-type", "line")
    expect(page.locator(".line-chart")).to_be_visible()

    page.select_option("#chart-type", "bar")
    expect(page.locator(".bar-chart")).to_be_visible()

    # Test temperature unit toggle
    page.click("#toggle-celsius")
    expect(page.locator(".unit-indicator")).to_contain_text("°C")

    page.click("#toggle-fahrenheit")
    expect(page.locator(".unit-indicator")).to_contain_text("°F")


def test_data_download(page: Page):
    """Test temperature data download functionality"""
    page.goto(f"{BASE_URL}/data")

    # Select data format
    page.select_option("#download-format", "csv")

    # Click download button
    download_promise = page.wait_for_download()
    page.click("#download-data-btn")
    download = download_promise.value

    # Verify download happened and has correct filename
    expect(download.suggested_filename).to_match(re.compile("temperature_data.*\\.csv"))


def test_responsive_design(page: Page):
    """Test responsive design at different viewport sizes"""
    # Test mobile view
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)

    # Check that mobile menu is visible
    expect(page.locator(".mobile-menu")).to_be_visible()

    # Test desktop view
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(BASE_URL)

    # Check that desktop navigation is visible
    expect(page.locator(".main-navigation")).to_be_visible()

    # Verify temperature chart resizes appropriately
    expect(page.locator("#temperature-chart")).to_have_css("width", re.compile(".*px"))


def test_alerts_configuration(page: Page):
    """Test temperature alerts configuration"""
    page.goto(f"{BASE_URL}/alerts")

    # Set temperature threshold
    page.fill("#max-temp-threshold", "30")
    page.fill("#min-temp-threshold", "0")

    # Select alert method
    page.check("#email-alert")

    # Save configuration
    page.click("#save-alerts-config")

    # Verify success message
    expect(page.locator(".alert-success")).to_be_visible()
    expect(page.locator(".alert-success")).to_contain_text("Alert configuration saved")


def test_temperature_trend_analysis(page: Page):
    """Test temperature trend analysis feature"""
    page.goto(f"{BASE_URL}/analysis")

    # Select analysis period
    page.select_option("#analysis-period", "last-30-days")
    page.click("#run-analysis")

    # Wait for analysis to complete
    page.wait_for_selector("#analysis-results")

    # Verify analysis components
    expect(page.locator("#trend-indicator")).to_be_visible()
    expect(page.locator("#temperature-statistics")).to_be_visible()
    expect(page.locator("#min-temperature")).to_be_visible()
    expect(page.locator("#max-temperature")).to_be_visible()
    expect(page.locator("#avg-temperature")).to_be_visible()


def test_dark_mode_toggle(page: Page):
    """Test dark mode toggle functionality"""
    page.goto(BASE_URL)

    # Check initial theme
    expect(page.locator("body")).not_to_have_class("dark-theme")

    # Toggle dark mode
    page.click("#theme-toggle")

    # Verify dark mode is active
    expect(page.locator("body")).to_have_class("dark-theme")

    # Check that chart colors adapt to dark mode
    expect(page.locator("#temperature-chart")).to_have_css("background-color", "rgba(40, 44, 52, 1)")
