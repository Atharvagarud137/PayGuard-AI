import re

from playwright.sync_api import Page, expect


class TransactionsPage:
    """
    Page Object for the PayGuard AI Transactions page.

    Selectors prefer accessible roles and application semantics over
    brittle CSS structure.
    """

    def __init__(self, page: Page):
        self.page = page

        # =====================================================================
        # Navigation
        # =====================================================================

        self.sidebar_navigation = page.get_by_role(
            "navigation"
        )

        self.transactions_navigation = (
            self.sidebar_navigation.get_by_role(
                "button",
                name=re.compile(r"Transactions$"),
            )
        )

        # =====================================================================
        # Page Header
        # =====================================================================

        self.page_header = page.locator(
            ".transactions-page-header"
        )

        self.page_heading = (
            self.page_header.get_by_role(
                "heading",
                name="Transactions",
                exact=True,
            )
        )

        self.page_description = self.page_header.get_by_text(
            "Inspect payment activity and follow each transaction through its lifecycle.",
            exact=True,
        )

        # =====================================================================
        # Transactions Section
        # =====================================================================

        self.transactions_list_panel = page.locator(
            ".transactions-list-panel"
        )

        self.transaction_table = page.locator(
            "table.transaction-table"
        )

        self.transaction_rows = self.transaction_table.locator(
            "tbody tr"
        )

        # =====================================================================
        # Empty State
        # =====================================================================

        self.empty_state = page.get_by_role(
            "heading",
            name="No transactions yet",
            exact=True,
        )

        # =====================================================================
        # Refresh
        # =====================================================================

        self.refresh_button = (
            self.page_header.get_by_role(
                "button",
                name=re.compile(r"^Refresh"),
            )
        )

        # =====================================================================
        # Lifecycle Dialog
        # =====================================================================

        self.lifecycle_dialog = page.get_by_role(
            "dialog",
            name="Transaction lifecycle",
        )

        self.close_lifecycle_button = (
            self.lifecycle_dialog.get_by_role(
                "button",
                name="Close transaction details",
                exact=True,
            )
        )

    # =========================================================================
    # Navigation
    # =========================================================================

    def open(self) -> None:
        """
        Navigate from the dashboard to the Transactions page.
        """

        expect(
            self.transactions_navigation
        ).to_be_visible()

        self.transactions_navigation.click()

        expect(
            self.page_heading
        ).to_be_visible()

    # =========================================================================
    # Page Assertions
    # =========================================================================

    def expect_page_loaded(self) -> None:
        """
        Verify that the Transactions page has loaded successfully.
        """

        expect(
            self.page_heading
        ).to_be_visible()

        expect(
            self.page_description
        ).to_be_visible()

        expect(
            self.transactions_list_panel
        ).to_be_visible()

    # =========================================================================
    # Empty State
    # =========================================================================

    def expect_empty_state(self) -> None:
        """
        Verify that the Transactions page displays its empty state.
        """

        expect(
            self.empty_state
        ).to_be_visible()

    # =========================================================================
    # Transaction Lookup
    # =========================================================================

    @staticmethod
    def _short_transaction_id(
            transaction_id: str,
    ) -> str:
        """
        Convert a full transaction UUID into the representation rendered
        by the Transactions UI.

        The frontend uses:

            first 8 characters + "..." + last 6 characters

        Example:

            b8cd34da-d6f8-48d1-933a-74bcc919aea4

        becomes:

            b8cd34da...19aea4
        """

        if not transaction_id:
            return transaction_id

        if len(transaction_id) <= 16:
            return transaction_id

        return (
            f"{transaction_id[:8]}"
            f"..."
            f"{transaction_id[-6:]}"
        )

    def get_transaction_row(
            self,
            transaction_id: str,
    ):
        """
        Return the table row containing the supplied transaction ID.

        The backend provides the full transaction UUID, while the frontend
        intentionally displays a shortened identifier. Therefore the Page
        Object converts the full ID into the exact representation rendered
        by the UI before locating the row.
        """

        visible_transaction_id = (
            self._short_transaction_id(
                transaction_id
            )
        )

        return self.transaction_table.locator(
            "tbody tr"
        ).filter(
            has_text=visible_transaction_id
        )

    def expect_transaction_visible(
            self,
            transaction_id: str,
    ) -> None:
        """
        Verify that a specific transaction is visible in the table.
        """

        row = self.get_transaction_row(
            transaction_id
        )

        expect(
            row
        ).to_be_visible()

    # =========================================================================
    # Transaction Data Assertions
    # =========================================================================

    def expect_merchant_visible(
            self,
            merchant_id: str,
    ) -> None:
        """
        Verify that the specified merchant is visible in the transaction
        table.

        This assertion is intentionally scoped to the transaction list
        panel so that unrelated occurrences elsewhere on the page cannot
        satisfy the assertion.
        """

        expect(
            self.transactions_list_panel.get_by_text(
                merchant_id,
                exact=True,
            )
        ).to_be_visible()

    def expect_status_visible(
            self,
            status: str,
    ) -> None:
        """
        Verify that the specified transaction status is visible in the
        transaction table.

        The assertion is scoped to the transaction list panel.
        """

        expect(
            self.transactions_list_panel.get_by_text(
                status,
                exact=True,
            )
        ).to_be_visible()

    def expect_transaction_status(
            self,
            transaction_id: str,
            status: str,
    ) -> None:
        """
        Verify the status of a specific transaction.
        """

        row = self.get_transaction_row(
            transaction_id
        )

        expect(
            row
        ).to_be_visible()

        expect(
            row.get_by_text(
                status,
                exact=True,
            )
        ).to_be_visible()

    def expect_transaction_amount(
            self,
            transaction_id: str,
            amount: str,
    ) -> None:
        """
        Verify the displayed amount of a specific transaction.

        Example:

            "$100.00"
        """

        row = self.get_transaction_row(
            transaction_id
        )

        expect(
            row
        ).to_be_visible()

        expect(
            row.get_by_text(
                amount,
                exact=True,
            )
        ).to_be_visible()

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def open_transaction_lifecycle(
            self,
            transaction_id: str,
    ) -> None:
        """
        Open the lifecycle dialog for a specific transaction.
        """

        row = self.get_transaction_row(
            transaction_id
        )

        expect(
            row
        ).to_be_visible()

        lifecycle_button = row.get_by_role(
            "button",
            name=re.compile(r"View Lifecycle"),
        )

        expect(
            lifecycle_button
        ).to_be_visible()

        expect(
            lifecycle_button
        ).to_be_enabled()

        lifecycle_button.click()

        expect(
            self.lifecycle_dialog
        ).to_be_visible()

    def expect_lifecycle_dialog(self) -> None:
        """
        Verify that the transaction lifecycle dialog is visible.
        """

        expect(
            self.lifecycle_dialog
        ).to_be_visible()

    def close_lifecycle(self) -> None:
        """
        Close the transaction lifecycle dialog.
        """

        expect(
            self.close_lifecycle_button
        ).to_be_visible()

        self.close_lifecycle_button.click()

        expect(
            self.lifecycle_dialog
        ).not_to_be_visible()