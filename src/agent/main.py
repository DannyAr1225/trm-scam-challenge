import asyncio

from urllib.parse import urlparse

from .batch_processor import run_batch

from .settings import TARGET_FILE

from .site_session import SiteSession


def valid_url(
    value: str
) -> bool:

    parsed = urlparse(value)

    return (
        parsed.scheme in {
            "http",
            "https"
        }
        and bool(parsed.netloc)
    )


def load_targets() -> list[str]:

    if not TARGET_FILE.exists():

        raise FileNotFoundError(
            f"Target file not found: "
            f"{TARGET_FILE}"
        )

    raw_lines = TARGET_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    urls = []

    seen = set()

    for line in raw_lines:

        url = line.strip()

        if not url:
            continue

        if url.startswith("#"):
            continue

        if not valid_url(url):

            print(
                f"Skipping invalid URL: {url}"
            )

            continue

        if url in seen:
            continue

        seen.add(url)

        urls.append(url)

    return urls


async def main():

    urls = load_targets()

    print(
        f"Loaded {len(urls)} targets."
    )

    if len(urls) != 160:

        print(
            "Warning: challenge target list "
            "is expected to contain 160 URLs."
        )

    session = SiteSession()

    await session.start()

    try:

        results = await run_batch(
            urls,
            session
        )

    finally:

        await session.close()

    scam_count = sum(
        result.classification == "SCAM"
        for result in results
    )

    address_count = sum(
        len(result.crypto_addresses)
        for result in results
    )

    print()
    print("Investigation complete.")
    print(
        f"Sites analyzed: {len(results)}"
    )
    print(
        f"Sites classified SCAM: {scam_count}"
    )
    print(
        f"Crypto addresses discovered: "
        f"{address_count}"
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )