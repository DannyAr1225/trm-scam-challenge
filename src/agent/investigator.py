import asyncio
import hashlib

from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from .classifier import (
    classify_site,
    fallback_classification,
)

from .extractor import extract_addresses

from .page_signals import (
    collect_page_signals,
)

from .schemas import (
    CryptoAddress,
    SiteResult,
)

from .settings import (
    ACTION_TIMEOUT_MS,
    MAX_EXPLORATION_STEPS,
    NAVIGATION_TIMEOUT_MS,
    SCREENSHOT_DIR,
)

from .site_explorer import (
    action_key,
    perform_action,
    rank_actions,
)

from .site_session import SiteSession


def result_status_from_http(
    status_code: int | None
) -> str:

    if status_code is None:
        return "success"

    if status_code in {
        404,
        410
    }:
        return "inactive"

    if status_code in {
        401,
        403,
        429
    }:
        return "blocked"

    if status_code >= 400:
        return "error"

    return "success"


def wallet_key(
    wallet: CryptoAddress
) -> tuple[str, str]:

    value = wallet.address

    if wallet.network == "ETH/ERC20":
        value = value.lower()

    return (
        wallet.network,
        value
    )


def merge_addresses(
    address_map: dict[
        tuple[str, str],
        CryptoAddress
    ],
    discovered: list[CryptoAddress]
) -> int:

    new_count = 0

    for wallet in discovered:

        key = wallet_key(wallet)

        if key not in address_map:

            address_map[key] = wallet
            new_count += 1

    return new_count


async def capture_screenshot(
    page,
    target_url: str,
    step: int
) -> str | None:

    SCREENSHOT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    fingerprint = hashlib.sha256(
        target_url.encode("utf-8")
    ).hexdigest()[:12]

    filename = (
        f"{fingerprint}_step_{step}.png"
    )

    path = SCREENSHOT_DIR / filename

    try:

        await page.screenshot(
            path=str(path),
            full_page=True
        )

        return str(
            path.relative_to(
                SCREENSHOT_DIR.parent
            )
        )

    except Exception:
        return None


async def investigate_site(
    url: str,
    session: SiteSession
) -> SiteResult:

    context = await session.create_context()

    page = await context.new_page()

    page.set_default_timeout(
        ACTION_TIMEOUT_MS
    )

    page.on(
        "dialog",
        lambda dialog: asyncio.create_task(
            dialog.dismiss()
        )
    )

    pages = []

    address_map: dict[
        tuple[str, str],
        CryptoAddress
    ] = {}

    visited_urls = set()

    attempted_actions = set()

    screenshots = []

    status = "success"

    error = None

    try:

        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=NAVIGATION_TIMEOUT_MS
        )

        status_code = (
            response.status
            if response is not None
            else None
        )

        status = result_status_from_http(
            status_code
        )

        signals = await collect_page_signals(
            page,
            status_code
        )

        pages.append(signals)

        visited_urls.add(
            signals.url
        )

        found = extract_addresses(
            signals
        )

        new_count = merge_addresses(
            address_map,
            found
        )

        if new_count:

            screenshot = await capture_screenshot(
                page,
                url,
                0
            )

            if screenshot:
                screenshots.append(
                    screenshot
                )

        for step in range(
            1,
            MAX_EXPLORATION_STEPS + 1
        ):

            actions = rank_actions(
                signals,
                visited_urls,
                attempted_actions
            )

            if not actions:
                break

            action = actions[0]

            attempted_actions.add(
                action_key(
                    signals.url,
                    action
                )
            )

            successful = await perform_action(
                page,
                action
            )

            if not successful:
                continue

            new_signals = (
                await collect_page_signals(
                    page
                )
            )

            pages.append(
                new_signals
            )

            visited_urls.add(
                new_signals.url
            )

            found = extract_addresses(
                new_signals
            )

            new_count = merge_addresses(
                address_map,
                found
            )

            if new_count:

                screenshot = (
                    await capture_screenshot(
                        page,
                        url,
                        step
                    )
                )

                if screenshot:
                    screenshots.append(
                        screenshot
                    )

            signals = new_signals

    except PlaywrightTimeoutError as exc:

        status = "timeout"

        error = str(exc)

        try:

            signals = await collect_page_signals(
                page
            )

            pages.append(signals)

            merge_addresses(
                address_map,
                extract_addresses(signals)
            )

        except Exception:
            pass

    except Exception as exc:

        message = str(exc)

        if (
            "ERR_NAME_NOT_RESOLVED" in message
            or "ERR_CONNECTION_REFUSED" in message
            or "ERR_CONNECTION_CLOSED" in message
        ):
            status = "inactive"

        elif (
            "ERR_BLOCKED_BY_CLIENT" in message
            or "ERR_ACCESS_DENIED" in message
        ):
            status = "blocked"

        else:
            status = "error"

        error = message

    finally:

        await context.close()

    try:

        classification = await classify_site(
            url=url,
            pages=pages,
            status=status,
            error=error
        )

    except Exception as exc:

        if error is None:
            error = (
                "Classifier error: "
                + str(exc)
            )

        classification = (
            fallback_classification(
                url,
                pages
            )
        )

    discovered_wallets = list(
        address_map.values()
    )

    # Challenge only asks for addresses from sites classified as scams
    if classification.classification == "NOT_SCAM":
        final_wallets = []
        final_screenshots = []

    else:
        final_wallets = discovered_wallets
        final_screenshots = screenshots

    return SiteResult(
        url=url,
        classification=(
            classification.classification
        ),
        crypto_addresses=final_wallets,
        confidence=classification.confidence,
        reasoning=classification.reasoning,
        indicators=classification.indicators,
        pages_visited=[
            page_signal.url
            for page_signal in pages
        ],
        status=status,
        error=error,
        screenshots=final_screenshots
    )