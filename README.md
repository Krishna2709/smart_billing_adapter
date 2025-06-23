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

Open `adapters/dummy_adapter.py`

```python
import requests

class DUMMYAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.dummybilling.com'

    def create_customer(self, data: dict) -> str:

        headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
        response = requests.post(f'{self.base_url}/customers', json=data, headers=headers)

        if response.status_code == 201:
            return response.json()['id']  # Return the provider id
        else:
            response.raise_for_status()

    def get_invoice(self, inv_id: str) -> dict:
        
        headers = {'X-API-Key': self.api_key}
        response = requests.get(f'{self.base_url}/invoices/{inv_id}', headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
```

Sample Usage:
```
from adapters.dummy_adapter import DUMMYAdapter

# 1. Instantiate with your API key
adapter = DUMMYAdapter(api_key="sk-demo")

# 2. Create a customer using your canonical data model
canonical_customer = {
    "id": "cust_123",
    "name": "Alice Smith",
    "email": "alice@example.com"
}

# 3. The adapter uses the mapping JSON behind the scenes
provider_customer_id = adapter.create_customer(canonical_customer)
print("New provider ID:", provider_customer_id)

# 4. Fetch an invoice by ID
invoice = adapter.get_invoice("inv_456")
print("Invoice amount:", invoice["amount"], invoice["currency"])
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

GigTel Mapping:
```json
{
  "User.id": "userId",
  "User.name": "userName",
  "User.email": "userEmail",
  "User.phone": "userPhone",
  "Domain.id": "domainId",
  "Domain.name": "domainName",
  "Address.id": "addressId",
  "Address.street": "addressStreet",
  "Address.city": "addressCity",
  "Address.state": "addressState",
  "Address.zip": "addressZip",
  "PhoneNumber.id": "phoneNumberId",
  "PhoneNumber.number": "phoneNumber",
  "Invoice.id": "invoiceId",
  "Invoice.amount": "invoiceAmount",
  "Invoice.date": "invoiceDate"
}
```

## 4 – Filling in the blanks

```python
import requests

class GIGTELAdapter:
    def __init__(self, auth_token: str, base_url: str = 'https://api.gigtel.com/v0'):
        self.auth_token = auth_token
        self.base_url = base_url

    def create_customer(self, data: dict) -> str:
        # Endpoint: /v0/domains/{domain}/users/
        response = requests.post(f'{self.base_url}/domains/{data['domain']}/users/', json=data, headers={'Authorization': self.auth_token})
        return response.json().get('id')
        # return 'stubbed_user_id'

    def get_invoice(self, inv_id: str) -> dict:
        # Endpoint: /v0/invoices/{inv_id}
        response = requests.get(f'{self.base_url}/invoices/{inv_id}', headers={'Authorization': self.auth_token})
        return response.json()
        # return {'invoiceId': inv_id, 'amount': 100, 'date': '2023-10-01'}
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
