import re

from playwright.async_api import Page

from .schemas import (
    FormField,
    PageButton,
    PageLink,
    PageSignals,
)

from .settings import (
    MAX_HTML_CHARS,
    MAX_PAGE_TEXT_CHARS,
)


def clean_text(value: str) -> str:

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


async def collect_page_signals(
    page: Page,
    status_code: int | None = None
) -> PageSignals:

    try:
        title = await page.title()
    except Exception:
        title = ""

    try:
        body_text = await page.locator(
            "body"
        ).inner_text()

    except Exception:
        body_text = ""

    body_text = clean_text(
        body_text
    )[:MAX_PAGE_TEXT_CHARS]

    try:
        link_data = await page.locator(
            "a"
        ).evaluate_all(
            """
            elements => elements.map(element => ({
                text: (
                    element.innerText ||
                    element.getAttribute("aria-label") ||
                    ""
                ).trim(),
                href: element.href || ""
            }))
            """
        )

    except Exception:
        link_data = []

    links = []

    for item in link_data[:150]:

        href = item.get("href", "")

        if not href:
            continue

        links.append(
            PageLink(
                text=clean_text(
                    item.get("text", "")
                ),
                href=href
            )
        )

    try:
        button_data = await page.locator(
            """
            button,
            [role="button"],
            input[type="submit"],
            input[type="button"]
            """
        ).evaluate_all(
            """
            elements => elements.map(element => ({
                text: (
                    element.innerText ||
                    element.value ||
                    element.getAttribute("aria-label") ||
                    ""
                ).trim()
            }))
            """
        )

    except Exception:
        button_data = []

    buttons = []

    seen_buttons = set()

    for item in button_data[:100]:

        button_text = clean_text(
            item.get("text", "")
        )

        if not button_text:
            continue

        normalized = button_text.lower()

        if normalized in seen_buttons:
            continue

        seen_buttons.add(normalized)

        buttons.append(
            PageButton(
                text=button_text
            )
        )

    try:
        input_data = await page.locator(
            "input"
        ).evaluate_all(
            """
            elements => elements.map(element => ({
                input_type: element.type || "",
                name: element.name || "",
                placeholder: element.placeholder || "",
                value: element.value || ""
            }))
            """
        )

    except Exception:
        input_data = []

    form_fields = [
        FormField(**item)
        for item in input_data[:100]
    ]

    try:
        html = await page.content()

    except Exception:
        html = ""

    html = html[:MAX_HTML_CHARS]

    return PageSignals(
        url=page.url,
        title=title,
        text=body_text,
        html=html,
        links=links,
        buttons=buttons,
        form_fields=form_fields,
        status_code=status_code
    )