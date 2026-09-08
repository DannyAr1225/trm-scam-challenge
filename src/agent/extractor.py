import re

import base58

from eth_utils import is_address

from .schemas import (
    CryptoAddress,
    PageSignals,
)


ETH_PATTERN = re.compile(
    r"(?<![0-9A-Za-z])"
    r"0x[a-fA-F0-9]{40}"
    r"(?![0-9A-Za-z])"
)

TRON_PATTERN = re.compile(
    r"(?<![1-9A-HJ-NP-Za-km-z])"
    r"T[1-9A-HJ-NP-Za-km-z]{33}"
    r"(?![1-9A-HJ-NP-Za-km-z])"
)

BTC_LEGACY_PATTERN = re.compile(
    r"(?<![1-9A-HJ-NP-Za-km-z])"
    r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}"
    r"(?![1-9A-HJ-NP-Za-km-z])"
)

BTC_BECH32_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"bc1[ac-hj-np-z02-9]{11,71}"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE
)


def get_context(
    text: str,
    start: int,
    end: int,
    window: int = 100
) -> str:

    left = max(
        0,
        start - window
    )

    right = min(
        len(text),
        end + window
    )

    return text[left:right].strip()


def valid_ethereum_address(
    value: str
) -> bool:

    return is_address(value)


def valid_tron_address(
    value: str
) -> bool:

    try:
        payload = base58.b58decode_check(
            value
        )

        return (
            len(payload) == 21
            and payload[0] == 0x41
        )

    except Exception:
        return False


def valid_bitcoin_legacy_address(
    value: str
) -> bool:

    try:
        payload = base58.b58decode_check(
            value
        )

        return (
            len(payload) == 21
            and payload[0] in {
                0x00,
                0x05
            }
        )

    except Exception:
        return False


def infer_asset_hint(
    network: str,
    context: str
) -> str | None:

    lowered = context.lower()

    if "usdt" in lowered or "tether" in lowered:
        return "USDT"

    if "usdc" in lowered:
        return "USDC"

    if network == "BTC":
        return "BTC"

    if network == "ETH/ERC20":

        if "eth" in lowered or "ethereum" in lowered:
            return "ETH"

    if network == "TRON/TRC20":

        if "trx" in lowered or "tron" in lowered:
            return "TRX"

    return None


def extract_pattern(
    text: str,
    pattern: re.Pattern,
    network: str,
    source_url: str,
    source_type: str,
    validator=None
) -> list[CryptoAddress]:

    results = []

    for match in pattern.finditer(text):

        value = match.group(0)

        if validator is not None:

            if not validator(value):
                continue

        context = get_context(
            text,
            match.start(),
            match.end()
        )

        results.append(
            CryptoAddress(
                address=value,
                network=network,
                source_url=source_url,
                context=context,
                asset_hint=infer_asset_hint(
                    network,
                    context
                ),
                source_type=source_type
            )
        )

    return results


def extract_from_text(
    text: str,
    source_url: str,
    source_type: str
) -> list[CryptoAddress]:

    addresses = []

    addresses.extend(
        extract_pattern(
            text,
            ETH_PATTERN,
            "ETH/ERC20",
            source_url,
            source_type,
            valid_ethereum_address
        )
    )

    addresses.extend(
        extract_pattern(
            text,
            TRON_PATTERN,
            "TRON/TRC20",
            source_url,
            source_type,
            valid_tron_address
        )
    )

    addresses.extend(
        extract_pattern(
            text,
            BTC_LEGACY_PATTERN,
            "BTC",
            source_url,
            source_type,
            valid_bitcoin_legacy_address
        )
    )

    addresses.extend(
        extract_pattern(
            text,
            BTC_BECH32_PATTERN,
            "BTC",
            source_url,
            source_type
        )
    )

    return addresses


def extract_addresses(
    signals: PageSignals
) -> list[CryptoAddress]:

    candidates = []

    candidates.extend(
        extract_from_text(
            signals.text,
            signals.url,
            "visible_text"
        )
    )

    candidates.extend(
        extract_from_text(
            signals.html,
            signals.url,
            "html"
        )
    )

    unique_addresses = {}

    for candidate in candidates:

        if candidate.network == "ETH/ERC20":
            normalized_address = (
                candidate.address.lower()
            )

        else:
            normalized_address = (
                candidate.address
            )

        key = (
            candidate.network,
            normalized_address
        )

        existing = unique_addresses.get(
            key
        )

        if existing is None:
            unique_addresses[key] = candidate

        elif (
            existing.source_type == "html"
            and
            candidate.source_type == "visible_text"
        ):
            unique_addresses[key] = candidate

    return list(
        unique_addresses.values()
    )