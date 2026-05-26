from playwright.sync_api import sync_playwright

URL = "https://drinksretailingnews.co.uk/rtd-sales-grow-17-in-value/"

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    # BLOCK HEAVY ASSETS
    page.route(
        "**/*",
        lambda route: (
            route.abort()
            if route.request.resource_type in [
                "image",
                "media",
                "font"
            ]
            else route.continue_()
        )
    )

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=30000
    )

    article = page.locator(
        "article"
    ).inner_text()

    print(article[:10000])

    page.close()

    browser.close()
