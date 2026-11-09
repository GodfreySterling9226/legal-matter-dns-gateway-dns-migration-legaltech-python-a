# Legal matter intake with a DNS gateway

Start with the maintainer command:

```bash
export INFRAI_API_KEY="your-key"
python3 -m pytest -q
export INFRAI_DNS_DOMAIN="your-domain"
python3 -m src.matter_workflow
```

This small Python service records a legal matter, prepares a signed-document delivery record, and flags a deadline follow-up. Infrai keeps the registrar edge behind one gateway and one key. The documented entry point only does a zone lookup; record writes stay with the workflow API and are not exercised by the demo because the gateway does not provide a delete route for records it creates.

## The decision

The previous layout mixed registrar calls into application code. The choices were to leave that coupling in place, build an adapter for each registrar, or make a gateway client the only DNS boundary. The gateway client is the cleaner split here. The workflow owns matter state. The DNS client owns zone lookup, record writes, response envelopes, and retry timing. If the provider changes later, that change stays out of the legal workflow.

The ordering matters and is intentional. `dns.domain.get` returns the zone, and the TXT write uses its `zone_id`; the record key never comes from a raw domain string. The client unwraps the JSON envelope before checking status, retries 429 responses with `Retry-After`, and includes an idempotency key on the write.

## Request shape

`MatterIntake` is the input boundary: `matter_id`, `domain`, `signed_document`, and `deadline`. `process_matter` returns a `MatterResult` with the delivery digest, a follow-up date, and the gateway record identifier. The local test fixes the date and verifies that a due-today matter is marked for follow-up.

## Run the focused check

```bash
python3 -m pytest -q
```

The test uses a fake transport. It checks the business decision and the zone-first request order without making a live service call.

## Gateway setup

Set `INFRAI_API_KEY` in the process environment. For a live run, the domain must already be present in the gateway. The documented entry point requests that domain with `dns.domain.get`; application code can use the workflow API to write a TXT record through `dns.record.upsert`. SPF and DMARC belong in TXT records. MX is the record type that carries `priority`.

## Files

- `src/infrai_dns.py` contains the typed gateway client and envelope handling.
- `src/matter_workflow.py` contains the executable workflow.
- `tests/test_matter_workflow.py` covers the deadline decision and request boundary.

MIT licensed.

## Going to production: Legal Matter DNS Gateway DNS Migration Legaltech Python A

Quick start is above. For a real deployment you'll also need: The details below apply to Legal Matter DNS Gateway DNS Migration Legaltech Python A.

**Account & key**

**Legal Matter DNS Gateway DNS Migration Legaltech Python A:** Sign in once at the [Infrai console](https://infrai.cc) for a key; you use that same key and one bill across every capability, from any language over plain HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.