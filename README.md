# TRM Scam Investigation Agent

This project implements an autonomous system for investigating a supplied
collection of websites, classifying each target as either `SCAM` or
`NOT_SCAM`, and extracting cryptocurrency addresses discovered on websites
that are classified as scams.

The primary goal of the system is to combine autonomous web navigation with
reliable evidence collection and fraud classification while remaining
careful about the risks associated with interacting with potentially
malicious websites.


## Architecture

The system uses a hybrid architecture that separates deterministic tasks
from tasks that require semantic reasoning. Playwright is responsible for
browser automation and provides an isolated browser context for each target
website. During an investigation, the system collects page signals including
visible text, links, buttons, form fields, page metadata, and HTML content.

Cryptocurrency address extraction is handled separately through deterministic
pattern matching and network-specific validation. This design prevents the
language model from generating or hallucinating cryptocurrency addresses and
makes the extraction process independently testable.

The site exploration component examines the available navigation options and
prioritizes actions that are likely to reveal financially relevant evidence.
Pages and controls related to deposits, wallets, recharging, investments,
cryptocurrency, and trading receive higher priority than low-value navigation
such as privacy or informational pages. The explorer deliberately avoids
actions that could authorize transactions, connect a cryptocurrency wallet,
send funds, or perform another irreversible financial action.

Evidence from every page visited during the investigation is accumulated and
then provided to an OpenAI language model. The model evaluates the complete
set of collected evidence and returns a structured classification containing
the final `SCAM` or `NOT_SCAM` verdict, a confidence score, concise reasoning,
and the strongest indicators used to reach the decision.

The batch-processing layer allows multiple targets to be investigated
concurrently while enforcing a limit on the number of active browser sessions.
Results are checkpointed to JSON after each completed investigation so that
progress is preserved even if a later target fails or the program is
interrupted.


## Design Philosophy

The design intentionally uses deterministic logic whenever correctness can be
verified directly and reserves language-model reasoning for tasks that are
inherently ambiguous.

Cryptocurrency address extraction is an example of a task where deterministic
logic is preferable. Valid wallet addresses follow network-specific formats
that can be detected and validated programmatically, so relying on a language
model for this step would introduce unnecessary hallucination risk.

Fraud classification is less deterministic because scam websites can vary
greatly in appearance, terminology, and behavior. The language model is
therefore used to interpret the accumulated evidence and determine whether the
overall behavior of a website is more consistent with a scam or a legitimate
service.

This separation allows the system to benefit from language-model reasoning
without making the entire investigation dependent on probabilistic output.


## Project Structure

The `site_session.py` module manages Playwright and isolated browser contexts.
The `page_signals.py` module collects information from each visited page.
The `extractor.py` module detects and validates cryptocurrency addresses.
The `site_explorer.py` module determines which areas of a website should be
explored next. The `classifier.py` module evaluates the collected evidence
using the language model. The `investigator.py` module coordinates the full
investigation of a single website, while `batch_processor.py` manages
concurrent investigations across the complete target list. Finally,
`main.py` provides the application entry point and loads the supplied URLs.


## Setup

A Python environment should be created before installing the project
dependencies. This project was developed using Python 3.12.

If Conda is being used, an environment can be created and activated with:

```bash
conda create -n scam-agent python=3.12 -y
conda activate scam-agent
```

The required dependencies can then be installed with:

```bash
python -m pip install -r requirements.txt
```

Playwright also requires a Chromium installation:

```bash
python -m playwright install chromium
```

The project reads configuration values from a local `.env` file. A template
is provided in `.env.example`. Create the local configuration file with:

```bash
cp .env.example .env
```

The OpenAI API key and desired model should then be added to `.env`. The real
`.env` file is excluded from version control so that API credentials are not
committed to the repository.


## Running

On macOS or Linux, the complete investigation can be started from the project
root with:

```bash
PYTHONPATH=src python -m agent.main
```

The program loads the URLs from `data/targets.txt`, investigates the targets,
and continuously writes progress to `output/results.json`.

During execution, the terminal displays the number of completed targets along
with the classification produced for each website.


## Output

The final JSON output contains an entry for every supplied URL. Each entry
contains the original target URL, its `SCAM` or `NOT_SCAM` classification,
the confidence score returned by the classifier, the reasoning behind the
decision, the strongest indicators observed during the investigation, the
pages visited, the investigation status, any recorded error, and any
cryptocurrency addresses discovered on scam websites.

When an address is discovered, the output also records the cryptocurrency
network, the page where the address was found, nearby contextual text, and an
asset hint when one can be inferred from the surrounding page content.

The program also supports saving screenshots when cryptocurrency addresses are
discovered so that the address can be preserved together with visual context.


## Testing

The deterministic components of the system include unit tests covering schema
validation, cryptocurrency address extraction, duplicate handling, and
classifier prompt construction.

The complete test suite can be executed with:

```bash
PYTHONPATH=src python -m pytest
```

The tests do not require live calls to the language model. This allows the
deterministic portions of the application to be validated without consuming
API credits or depending on external model availability.


## Security Considerations

The supplied websites must be treated as potentially malicious. Browser
sessions are therefore created using isolated Playwright contexts rather than
a persistent personal browser profile. Downloads are disabled, service workers
are blocked, and the application does not provide websites with access to the
OpenAI API key.

The exploration logic does not enter real financial credentials, connect
cryptocurrency wallets, approve transactions, send cryptocurrency, or perform
other irreversible financial operations. Financially sensitive actions such
as payment confirmation or wallet authorization are explicitly avoided by the
navigation logic.

Website text is also treated as untrusted data when it is passed to the
language model. The classifier is instructed to ignore any content attempting
to modify its role, classification rules, or response format. This reduces the
risk that prompt-injection text embedded within a malicious website could
influence the behavior of the classification system.

For stronger isolation, the project also includes a Docker configuration.
When investigating hostile or unknown targets, the system should preferably be
executed inside a disposable container or virtual machine rather than directly
inside a personal browsing environment.


## Assumptions

The assignment requires a binary classification for every target. The system
therefore ultimately produces either `SCAM` or `NOT_SCAM`, even when a website
is unavailable or the evidence is incomplete.

Operational conditions such as an inactive website, a timeout, blocked access,
or another browser failure are represented separately through the status
field. When the available evidence is limited, the classifier is expected to
reflect that uncertainty through a lower confidence score rather than
inventing evidence.

The system does not use real financial accounts, personal credentials,
cryptocurrency wallets, or actual funds while exploring a target.


## Alternative Approaches Considered

### Static HTTP Scraping

A simpler implementation using `requests` and BeautifulSoup would require less
browser overhead and would likely process the target list more quickly.
However, many modern websites render their interfaces dynamically with
JavaScript, and relevant evidence may only become visible after navigation or
interaction. Playwright was therefore selected so the system can observe the
website as an actual browser would.


### Fully LLM-Controlled Browser Navigation

Another possible design would allow the language model to choose and execute
every browser interaction directly. This could make the system more flexible,
particularly on unfamiliar websites, but it would also increase
unpredictability, API cost, latency, and security risk.

The current implementation therefore uses constrained autonomous navigation.
The browser explorer deterministically ranks actions that are likely to expose
useful financial evidence while preventing dangerous or irreversible actions.
The language model is then used where semantic reasoning provides the greatest
benefit: classification of the accumulated evidence.


### LLM-Based Cryptocurrency Address Extraction

The language model could also have been asked to identify wallet addresses
directly from page content. This approach was rejected because wallet formats
can be recognized and validated programmatically. Deterministic extraction is
easier to test, reduces hallucination risk, and allows every extracted address
to be traced directly back to the page on which it was discovered.


## Distinguishing Features

One of the main characteristics of this implementation is the separation
between evidence collection, deterministic wallet extraction, autonomous
navigation, and language-model classification. These components can be tested
and modified independently rather than combining the entire workflow into one
large agent prompt.

The investigation also accumulates evidence across multiple pages instead of
classifying a target solely from its landing page. This is important because
fraudulent behavior or cryptocurrency deposit information may only appear
deeper within a website.

The system records confidence scores, supporting indicators, pages visited,
status information, and screenshot evidence to make the resulting
classification more auditable. Checkpointing after every completed target also
allows the batch investigation to recover useful results even if individual
websites fail.


## Future Improvements

With additional development time, cryptocurrency extraction could be expanded
to include QR-code detection and additional blockchain networks. Bitcoin
Bech32 and Bech32m validation could also be strengthened beyond the current
candidate-detection approach.

The navigation system could be extended to handle more complex single-page
applications, popups, multi-step registration flows, and controlled login
flows using disposable credentials. A future version could also combine the
existing deterministic navigation strategy with a constrained model-based
planner that selects from an explicitly permitted set of browser actions.

Screenshot evidence could be improved by locating the exact DOM element
containing a cryptocurrency address and capturing a focused image around that
element rather than relying on full-page screenshots.

Additional evaluation would also be valuable. Given a larger labeled dataset,
classification thresholds, navigation priorities, address-extraction recall,
and model behavior could be measured systematically. More detailed telemetry,
retry policies, and registrable-domain-aware navigation would further improve
reliability when processing large and diverse sets of websites.