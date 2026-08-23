import re

from playwright.sync_api import Page, expect


class CardsPage:
    def __init__(self, page: Page):
        self.page = page

        # -------------------------------------------------------------------
        # Navigation
        # -------------------------------------------------------------------

        self.cards_navigation = (
            page.locator(
                "aside.sidebar .sidebar-navigation"
            ).get_by_role(
                "button",
                name="Cards",
            )
        )

        # -------------------------------------------------------------------
        # Cards Page
        # -------------------------------------------------------------------

        self.page_heading = (
            page.locator(
                ".cards-page-header"
            ).get_by_role(
                "heading",
                name="Cards",
                exact=True,
            )
        )

        # Scope all card-list assertions to the actual Issued Cards panel.
        self.cards_list_panel = (
            page.locator(
                ".cards-list-panel"
            )
        )

        # -------------------------------------------------------------------
        # Issue Card
        # -------------------------------------------------------------------

        self.open_issue_card_button = (
            page.locator(
                ".cards-header-actions"
            ).get_by_role(
                "button",
                name="+ Issue Card",
                exact=True,
            )
        )

        self.card_form = page.locator(
            "form.card-form"
        )

        self.submit_issue_card_button = (
            self.card_form.get_by_role(
                "button",
                name="Issue Card",
                exact=True,
            )
        )

        # -------------------------------------------------------------------
        # Card Form Fields
        # -------------------------------------------------------------------

        self.cardholder_name_input = page.get_by_label(
            "Cardholder Name",
            exact=True,
        )

        self.network_select = page.get_by_label(
            "Network",
            exact=True,
        )

        self.initial_balance_input = page.get_by_label(
            "Initial Balance",
            exact=True,
        )

        self.expiry_date_input = page.get_by_label(
            "Expiry Date",
            exact=True,
        )

        # -------------------------------------------------------------------
        # Verification
        # -------------------------------------------------------------------

        self.success_message = page.get_by_text(
            "Card issued successfully.",
            exact=True,
        )

    # =========================================================================
    # Navigation
    # =========================================================================

    def open(self) -> None:
        """Open the Cards page from the dashboard navigation."""

        expect(
            self.cards_navigation
        ).to_be_visible()

        self.cards_navigation.click()

        expect(
            self.page_heading
        ).to_be_visible()

    # =========================================================================
    # Card Issuance
    # =========================================================================

    def open_issue_card_form(self) -> None:
        """Open the card issuance form."""

        expect(
            self.open_issue_card_button
        ).to_be_visible()

        self.open_issue_card_button.click()

        expect(
            self.page.get_by_role(
                "heading",
                name="Issue New Card",
                exact=True,
            )
        ).to_be_visible()

        expect(
            self.card_form
        ).to_be_visible()

    def fill_card_form(
            self,
            cardholder_name: str,
            network: str,
            initial_balance: str,
            expiry_date: str,
    ) -> None:
        """Fill the card issuance form."""

        self.cardholder_name_input.fill(
            cardholder_name
        )

        self.network_select.select_option(
            network
        )

        self.initial_balance_input.fill(
            initial_balance
        )

        self.expiry_date_input.fill(
            expiry_date
        )

    def submit_card(self) -> None:
        """Submit the card issuance form."""

        expect(
            self.submit_issue_card_button
        ).to_be_visible()

        expect(
            self.submit_issue_card_button
        ).to_be_enabled()

        self.submit_issue_card_button.click()

    # =========================================================================
    # Assertions
    # =========================================================================

    def expect_success_message(self) -> None:
        """Verify that the card was successfully issued."""

        expect(
            self.success_message
        ).to_be_visible()

    def expect_cardholder(
            self,
            cardholder_name: str,
    ) -> None:
        """
        Verify that the issued card appears in the
        Issued Cards section.
        """

        expect(
            self.cards_list_panel.get_by_text(
                cardholder_name,
                exact=True,
            )
        ).to_be_visible()