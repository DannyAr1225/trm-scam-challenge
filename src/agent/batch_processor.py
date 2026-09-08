import asyncio
import json

from .classifier import (
    fallback_classification,
)

from .investigator import (
    investigate_site,
)

from .schemas import SiteResult

from .settings import (
    MAX_CONCURRENT_SITES,
    OUTPUT_FILE,
)

from .site_session import SiteSession


def save_results(
    results: list[SiteResult | None]
) -> None:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    available_results = [
        result.model_dump(
            mode="json"
        )
        for result in results
        if result is not None
    ]

    temporary_file = OUTPUT_FILE.with_name(
        OUTPUT_FILE.name + ".tmp"
    )

    temporary_file.write_text(
        json.dumps(
            available_results,
            indent=2
        ),
        encoding="utf-8"
    )

    temporary_file.replace(
        OUTPUT_FILE
    )


async def run_batch(
    urls: list[str],
    session: SiteSession
) -> list[SiteResult]:

    semaphore = asyncio.Semaphore(
        MAX_CONCURRENT_SITES
    )

    results: list[
        SiteResult | None
    ] = [
        None
        for _ in urls
    ]

    async def run_one(
        index: int,
        url: str
    ):

        async with semaphore:

            try:

                result = await investigate_site(
                    url,
                    session
                )

            except Exception as exc:

                fallback = (
                    fallback_classification(
                        url,
                        []
                    )
                )

                result = SiteResult(
                    url=url,
                    classification=(
                        fallback.classification
                    ),
                    confidence=(
                        fallback.confidence
                    ),
                    reasoning=(
                        fallback.reasoning
                    ),
                    indicators=(
                        fallback.indicators
                    ),
                    status="error",
                    error=str(exc)
                )

            return (
                index,
                result
            )

    tasks = [
        asyncio.create_task(
            run_one(
                index,
                url
            )
        )
        for index, url in enumerate(
            urls
        )
    ]

    completed = 0

    for finished_task in asyncio.as_completed(
        tasks
    ):

        index, result = await finished_task

        results[index] = result

        completed += 1

        print(
            f"[{completed}/{len(urls)}] "
            f"{result.classification:<8} "
            f"{result.url}"
        )

        save_results(
            results
        )

    return [
        result
        for result in results
        if result is not None
    ]