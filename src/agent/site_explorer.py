from urllib.parse import urlparse

from playwright.async_api import Page

from .schemas import (
    ExplorationAction,
    PageSignals,
)

from .settings import (
    NAVIGATION_TIMEOUT_MS,
    PAGE_SETTLE_TIME_MS,
)


ACTION_TERMS = {
    "deposit": 10,
    "recharge": 10,
    "add funds": 10,
    "fund account": 10,
    "wallet": 8,
    "usdt": 8,
    "usdc": 8,
    "bitcoin": 7,
    "btc": 7,
    "ethereum": 7,
    "eth": 7,
    "crypto": 6,
    "investment": 6,
    "invest": 6,
    "trading": 5,
    "trade": 5,
    "plans": 4,
    "login": 4,
    "log in": 4,
    "sign in": 4,
    "register": 4,
    "sign up": 4,
}


LOW_VALUE_TERMS = {
    "privacy",
    "terms",
    "about",
    "contact",
    "blog",
    "faq",
}


UNSAFE_ACTION_TERMS = {
    "send now",
    "transfer now",
    "confirm payment",
    "place order",
    "purchase",
    "connect wallet",
    "approve transaction",
    "sign transaction",
    "delete account",
}


def action_score(
    text: str
) -> int:

    lowered = text.lower().strip()

    if not lowered:
        return 0

    for dangerous_term in UNSAFE_ACTION_TERMS:

        if dangerous_term in lowered:
            return -100

    score = 0

    for term, value in ACTION_TERMS.items():

        if term in lowered:
            score += value

    for term in LOW_VALUE_TERMS:

        if term in lowered:
            score -= 3

    return score


def same_site(
    original_url: str,
    candidate_url: str
) -> bool:

    original_host = (
        urlparse(original_url)
        .hostname
        or ""
    ).lower()

    candidate_host = (
        urlparse(candidate_url)
        .hostname
        or ""
    ).lower()

    original_host = original_host.removeprefix(
        "www."
    )

    candidate_host = candidate_host.removeprefix(
        "www."
    )

    if not original_host or not candidate_host:
        return False

    return (
        candidate_host == original_host
        or candidate_host.endswith(
            "." + original_host
        )
        or original_host.endswith(
            "." + candidate_host
        )
    )


def action_key(
    current_url: str,
    action: ExplorationAction
) -> str:

    if action.kind == "link":
        return f"link:{action.target}"

    return (
        f"button:{current_url}:"
        f"{action.label.lower()}"
    )


def rank_actions(
    signals: PageSignals,
    visited_urls: set[str],
    attempted_actions: set[str]
) -> list[ExplorationAction]:

    actions = []

    for link in signals.links:

        if not link.href.startswith(
            ("http://", "https://")
        ):
            continue

        if link.href in visited_urls:
            continue

        if not same_site(
            signals.url,
            link.href
        ):
            continue

        score = action_score(
            f"{link.text} {link.href}"
        )

        if score <= 0:
            continue

        action = ExplorationAction(
            kind="link",
            label=link.text or link.href,
            target=link.href,
            score=score
        )

        if action_key(
            signals.url,
            action
        ) not in attempted_actions:

            actions.append(action)

    for button in signals.buttons:

        score = action_score(
            button.text
        )

        if score <= 0:
            continue

        action = ExplorationAction(
            kind="button",
            label=button.text,
            score=score
        )

        if action_key(
            signals.url,
            action
        ) not in attempted_actions:

            actions.append(action)

    return sorted(
        actions,
        key=lambda item: item.score,
        reverse=True
    )


async def perform_action(
    page: Page,
    action: ExplorationAction
) -> bool:

    try:

        if (
            action.kind == "link"
            and action.target
        ):

            await page.goto(
                action.target,
                wait_until="domcontentloaded",
                timeout=NAVIGATION_TIMEOUT_MS
            )

        else:

            button = page.get_by_role(
                "button",
                name=action.label,
                exact=True
            ).first

            if await button.count():

                await button.click()

            else:

                fallback = page.get_by_text(
                    action.label,
                    exact=True
                ).first

                if not await fallback.count():
                    return False

                await fallback.click()

        await page.wait_for_timeout(
            PAGE_SETTLE_TIME_MS
        )

        try:
            await page.wait_for_load_state(
                "domcontentloaded",
                timeout=3_000
            )

        except Exception:
            pass

        return True

    except Exception:
        return False