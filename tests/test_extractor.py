from agent.extractor import (
    extract_addresses,
)

from agent.schemas import PageSignals


def test_extract_multiple_networks():

    signals = PageSignals(
        url="https://example.com",
        text="""
        Send BTC here:
        1BoatSLRHtKNngkdXEeobR76b53LETtpyT

        Ethereum:
        0xdAC17F958D2ee523a2206206994597C13D831ec7

        USDT TRC20:
        TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
        """
    )

    addresses = extract_addresses(
        signals
    )

    networks = {
        item.network
        for item in addresses
    }

    assert "BTC" in networks
    assert "ETH/ERC20" in networks
    assert "TRON/TRC20" in networks


def test_duplicates_removed():

    ethereum_address = (
        "0xdAC17F958D2ee523"
        "a2206206994597C13D831ec7"
    )

    signals = PageSignals(
        url="https://example.com",
        text=ethereum_address,
        html=f"<div>{ethereum_address}</div>"
    )

    addresses = extract_addresses(
        signals
    )

    assert len(addresses) == 1


def test_no_addresses():

    signals = PageSignals(
        url="https://example.com",
        text=(
            "This page has no cryptocurrency "
            "wallet addresses."
        )
    )

    addresses = extract_addresses(
        signals
    )

    assert addresses == []