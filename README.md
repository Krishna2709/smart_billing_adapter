# LLM‑Driven Billing Adapter Demo

This repo shows how to turn **any OpenAPI / Swagger file** into a runnable Python adapter in *one* command using a LLM. The generated adapter gives you typed stubs (`create_customer`, `get_invoice`, …) plus a JSON field‑mapping so you can plug different billing platforms into a single canonical data model.

> **Status:** Proof‑of‑concept.
---

## What’s inside?

| Path                                | Purpose                                                                          |
| ----------------------------------- | -------------------------------------------------------------------------------- |
| `generate_adapter.py`               | One‑file generator—parse spec → call LLM → emit code + map.                      |
| `specs/dummy_billing_provider.json` | Tiny fake Swagger for quick testing.                                             |
| `adapters/` (generated)             | One sub‑folder per provider containing `<provider>_adapter.py` and mapping JSON. |

---

## 1 – Prerequisites

- Python ≥ 3.11
- OpenAI (or Azure OpenAI) API key with access to `gpt-4o-mini` (change in script if needed)

```bash
python -m pip install openai rich pydantic PyYAML
export OPENAI_API_KEY="sk‑…"
```

---

## 2 – Generate an adapter for the dummy provider

```bash
# run once to scaffold
python generate_adapter.py specs/dummy_billing_provider.json DUMMY
```

Output:

```
adapters/
    dummy_adapter.py        # class DUMMYAdapter – syntactically valid Python
    dummy_adapter.map.json  # canonical ↔ provider field map
```

Open `adapters/dummy_adapter.py`—you’ll see TODOs where real HTTP calls belong.  Importing the class already works:

```python
from adapters.dummy_adapter import DUMMYAdapter, Customer

a = DUMMYAdapter(api_key="demo")
print(a)  # prints object repr without error
```

---

## 3 – Point at a real Swagger (GigTel)

```bash
mkdir -p specs
curl -o specs/gigtel.json https://api.gigtel.com/openapi.json
python generate_adapter.py specs/gigtel.json GIGTEL
```

You now have `gigtel_adapter.py` and `gigtel_adapter.map.json`.

---

## 4 – Filling in the blanks

```python
# adapters/gigtel_adapter.py  (excerpt – replace TODOs)
import httpx

class GIGTELAdapter:
    def __init__(self, token: str, base_url: str = "https://api.gigtel.com"):
        self._client = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {token}"})

    def create_customer(self, data: Customer) -> str:
        resp = self._client.post("/v0/domains/{domain}/users/", json={
            "user": data.id,
            "name-first-name": data.name.split()[0],
            "name-last-name":  data.name.split()[‑1],
            "email": data.email,
            "user-scope": "Basic User"
        })
        resp.raise_for_status()
        return resp.json()["user"]
```

Use the **mapping JSON** to translate field names programmatically rather than hard‑coding.

---

## 5 – Automating spec drift detection

1. Nightly CI job pulls the latest Swagger from each provider.
2. Run `generate_adapter.py` and commit the diff in a PR.
3. Unit tests run on the regenerated code.
4. If tests fail, you know the provider introduced a breaking change.

---

## 6 – Extending the canonical model

Edit `CANONICAL_MODEL` string in `generate_adapter.py`—add classes or fields (e.g., `PaymentMethod`).  The LLM prompt automatically includes the updated definition, and new adapters will map it.

---

## 7 – Troubleshooting

| Symptom                            | Fix                                                                   |
| ---------------------------------- | --------------------------------------------------------------------- |
| `OPENAI_API_KEY` error             | Export the key or set environment variable.                           |
| `openai.error.InvalidRequestError` | Lower `MAX_SPEC_CHARS` or switch to a larger context‑window model.    |
| Rich `MarkupError`                 | You pulled an old script—latest version prints without nested markup. |
| Provider spec needs cookies        | Use DevTools → “Copy as cURL” to fetch the spec once.                 |

---

## 8 – Cleaning up

```bash
rm -rf adapters  # delete all generated code and maps
```

Re‑run the generator any time—the script will recreate the folder from scratch.

---

**Enjoy integrating billing platforms the lazy, LLM‑powered way!**

