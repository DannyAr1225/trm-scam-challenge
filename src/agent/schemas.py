from typing import Literal

from pydantic import BaseModel, Field


class CryptoAddress(BaseModel):
    address: str

    network: Literal[
        "BTC",
        "ETH/ERC20",
        "TRON/TRC20"
    ]

    source_url: str

    context: str | None = None

    asset_hint: str | None = None

    source_type: Literal[
        "visible_text",
        "html"
    ] = "visible_text"


class PageLink(BaseModel):
    text: str = ""
    href: str


class PageButton(BaseModel):
    text: str


class FormField(BaseModel):
    input_type: str = ""
    name: str = ""
    placeholder: str = ""
    value: str = ""


class PageSignals(BaseModel):
    url: str

    title: str = ""

    text: str = ""

    html: str = ""

    links: list[PageLink] = Field(
        default_factory=list
    )

    buttons: list[PageButton] = Field(
        default_factory=list
    )

    form_fields: list[FormField] = Field(
        default_factory=list
    )

    status_code: int | None = None


class ExplorationAction(BaseModel):
    kind: Literal[
        "link",
        "button"
    ]

    label: str

    target: str | None = None

    score: int = 0


class ClassificationResult(BaseModel):
    classification: Literal[
        "SCAM",
        "NOT_SCAM"
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    reasoning: str

    indicators: list[str] = Field(
        default_factory=list
    )


class SiteResult(BaseModel):
    url: str

    classification: Literal[
        "SCAM",
        "NOT_SCAM"
    ]

    crypto_addresses: list[CryptoAddress] = Field(
        default_factory=list
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    reasoning: str

    indicators: list[str] = Field(
        default_factory=list
    )

    pages_visited: list[str] = Field(
        default_factory=list
    )

    status: Literal[
        "success",
        "inactive",
        "timeout",
        "blocked",
        "error"
    ]

    error: str | None = None

    screenshots: list[str] = Field(
        default_factory=list
    )