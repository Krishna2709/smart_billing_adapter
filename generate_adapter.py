import json
import os
import pathlib
import sys
import textwrap
from typing import Dict, Any

import openai
import yaml
from rich import print

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini" 
MAX_SPEC_CHARS = 50_000     # clip giant specs to keep prompt small

# canonical model used in the prompt so the LLM knows the target structure
CANONICAL_MODEL = textwrap.dedent(
    """
    # Canonical entities (Python pseudo‑code)
    class Customer: id: str; name: str; email: str
    class Invoice: id: str; customer_id: str; amount: float; currency: str
    """
)

PROMPT_TEMPLATE = textwrap.dedent(
    """
    You are a senior API integration engineer. You will read an OpenAPI 3 spec and
    output **JSON only** with two keys: "mapping" and "code".

    • "mapping" must be a JSON object describing how provider fields map to the
      canonical model (see below). Example: {{"Customer.id": "subscriberId", ... }}
    • "code" must be valid runnable Python 3.11 that defines a class
      "{provider}Adapter" with methods:
          - create_customer(data: Customer) -> str      # returns provider id
          - get_invoice(inv_id: str) -> Invoice
      The adapter should use the provider endpoints and auth scheme from the
      spec, but you may stub network calls with comments for brevity.

    Canonical model reference:
    {{canonical}}
    """
)


def load_spec(path: str) -> str:
    """Return the spec as minified JSON (string), clipped to MAX_SPEC_CHARS."""
    raw = pathlib.Path(path).read_text()
    try:
        spec_dict = json.loads(raw)
    except json.JSONDecodeError:
        spec_dict = yaml.safe_load(raw)
    return json.dumps(spec_dict)[:MAX_SPEC_CHARS]


def call_llm(prompt: str) -> Dict[str, Any]:
    """Call OpenAI ChatCompletion in JSON mode and return parsed dict."""
    response = openai.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": "You are precise and output JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise Exception("Empty response from LLM")
    
    return json.loads(content)


def main(spec_path: str, provider: str) -> None:
    spec_json = load_spec(spec_path)

    prompt = PROMPT_TEMPLATE.format(
        provider=provider,
        canonical=CANONICAL_MODEL.strip()
    ) + "\n```openapi-json\n" + spec_json + "\n```"

    print("[yellow]Calling LLM … this may take half a minute.[/yellow]")
    result = call_llm(prompt)

    adapter_dir = pathlib.Path("adapters")
    adapter_dir.mkdir(exist_ok=True)

    # adapter code
    adapter_file = adapter_dir / f"{provider.lower()}_adapter.py"
    adapter_file.write_text(result["code"], encoding="utf‑8")

    # mapping JSON
    mapping_file = adapter_file.with_suffix(".map.json")
    mapping_file.write_text(json.dumps(result["mapping"], indent=2), encoding="utf‑8")

    print(f"[green]Generated[/green] {adapter_file} and {mapping_file}\n")
    print(f"Run [bold]python {adapter_file.name} --help[/bold] or open the file to inspect the stub.")

# ─────────────────────────── Entrypoint ──────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_adapter.py <spec-file.(json|yaml)> <ProviderName>")
        sys.exit(1)

    spec_path, provider_name = sys.argv[1:]
    main(spec_path, provider_name)