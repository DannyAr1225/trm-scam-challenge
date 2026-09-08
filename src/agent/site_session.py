from playwright.async_api import (
    Browser,
    BrowserContext,
    Playwright,
    async_playwright,
)

from .settings import HEADLESS


class SiteSession:

    def __init__(self):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None

    async def start(self) -> None:

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-dev-shm-usage"
            ]
        )

    async def create_context(
        self
    ) -> BrowserContext:

        if self.browser is None:
            raise RuntimeError(
                "Browser session has not been started."
            )

        context = await self.browser.new_context(
            accept_downloads=False,
            ignore_https_errors=True,
            service_workers="block",
            java_script_enabled=True,
        )

        async def filter_requests(route):

            request_type = route.request.resource_type

            if request_type in {
                "media",
                "font"
            }:
                await route.abort()

            else:
                await route.continue_()

        await context.route(
            "**/*",
            filter_requests
        )

        return context

    async def close(self) -> None:

        if self.browser is not None:
            await self.browser.close()

        if self.playwright is not None:
            await self.playwright.stop()