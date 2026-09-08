import pytest

from pydantic import ValidationError

from agent.schemas import (
    ClassificationResult,
    CryptoAddress,
)


def test_classification_schema():

    result = ClassificationResult(
        classification="SCAM",
        confidence=0.91,
        reasoning="Suspicious investment claims.",
        indicators=[
            "guaranteed returns"
        ]
    )

    assert result.classification == "SCAM"
    assert result.confidence == 0.91


def test_confidence_must_be_valid():

    with pytest.raises(
        ValidationError
    ):

        ClassificationResult(
            classification="SCAM",
            confidence=2.0,
            reasoning="Invalid confidence.",
            indicators=[]
        )


def test_crypto_address_schema():

    wallet = CryptoAddress(
        address=(
            "0xdAC17F958D2ee523"
            "a2206206994597C13D831ec7"
        ),
        network="ETH/ERC20",
        source_url="https://example.com"
    )

    assert wallet.network == "ETH/ERC20"