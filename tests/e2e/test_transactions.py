from playwright.sync_api import Page

from tests.e2e.pages.transactions_page import TransactionsPage


def test_transactions_page_loads(page: Page):
    """
    Verify that the Transactions page loads successfully
    and displays its core transaction interface.
    """

    page.goto("http://localhost:5173")

    transactions_page = TransactionsPage(page)

    transactions_page.open()

    transactions_page.expect_page_loaded()


def test_transactions_page_shows_empty_state(page: Page):
    """
    Verify that the Transactions page displays the expected
    empty state when no transactions are available.
    """

    page.goto("http://localhost:5173")

    transactions_page = TransactionsPage(page)

    transactions_page.open()

    transactions_page.expect_page_loaded()

    transactions_page.expect_empty_state()


def test_authorized_transaction_appears_in_transactions(
        page: Page,
        authorized_transaction: dict,
):
    """
    Verify that an authorized transaction created through the API
    appears correctly in the Transactions page.
    """

    page.goto("http://localhost:5173")

    transactions_page = TransactionsPage(page)

    transactions_page.open()

    transactions_page.expect_page_loaded()

    transaction_id = authorized_transaction[
        "transaction_id"
    ]

    transactions_page.expect_transaction_visible(
        transaction_id
    )

    transactions_page.expect_merchant_visible(
        "e2e-merchant-001"
    )

    transactions_page.expect_status_visible(
        "AUTHORIZED"
    )


def test_authorized_transaction_lifecycle_can_be_opened(
        page: Page,
        authorized_transaction: dict,
):
    """
    Verify that the lifecycle dialog can be opened for an
    authorized transaction.
    """

    page.goto("http://localhost:5173")

    transactions_page = TransactionsPage(page)

    transactions_page.open()

    transactions_page.expect_page_loaded()

    transaction_id = authorized_transaction[
        "transaction_id"
    ]

    transactions_page.expect_transaction_visible(
        transaction_id
    )

    transactions_page.open_transaction_lifecycle(
        transaction_id
    )

    transactions_page.expect_lifecycle_dialog()

    transactions_page.close_lifecycle()