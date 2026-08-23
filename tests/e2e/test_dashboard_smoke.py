from playwright.sync_api import Page, expect


def test_dashboard_loads(
        dashboard_page: Page,
):
    """
    Verify that the PayGuard dashboard loads successfully
    and displays its core operational information.
    """

    expect(
        dashboard_page.get_by_role(
            "heading",
            name="Overview",
            exact=True,
        )
    ).to_be_visible()

    expect(
        dashboard_page.get_by_text(
            "Monitor payment activity and gateway health.",
            exact=True,
        )
    ).to_be_visible()

    system_health = dashboard_page.get_by_test_id(
        "system-health"
    )

    expect(
        system_health
    ).to_be_visible()

    gateway_health = dashboard_page.get_by_test_id(
        "health-payment-gateway"
    )

    expect(
        gateway_health
    ).to_be_visible()

    expect(
        gateway_health.get_by_text(
            "Payment Gateway",
            exact=True,
        )
    ).to_be_visible()

    expect(
        dashboard_page.get_by_test_id(
            "health-payment-gateway-state"
        )
    ).to_have_text(
        "Operational"
    )