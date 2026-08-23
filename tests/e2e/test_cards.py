from uuid import uuid4

from playwright.sync_api import Page

from tests.e2e.pages.cards_page import CardsPage


def test_issue_card_successfully(
        dashboard_page: Page,
):
    """
    Verify that a user can issue a new virtual card through
    the dashboard.
    """

    cardholder_name = (
        f"E2E Test User {uuid4().hex[:8]}"
    )

    cards_page = CardsPage(
        dashboard_page
    )

    cards_page.open()

    cards_page.open_issue_card_form()

    cards_page.fill_card_form(
        cardholder_name=cardholder_name,
        network="VISA",
        initial_balance="1000",
        expiry_date="2030-12-31",
    )

    cards_page.submit_card()

    cards_page.expect_success_message()

    cards_page.expect_cardholder(
        cardholder_name
    )