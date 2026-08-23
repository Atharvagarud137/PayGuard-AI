from pathlib import Path

from playwright.sync_api import Playwright


BASE_DIR = Path(__file__).resolve().parent

FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://localhost:8000"


def pytest_configure(config):
    """Configure Playwright test settings."""
    config.option.base_url = FRONTEND_URL