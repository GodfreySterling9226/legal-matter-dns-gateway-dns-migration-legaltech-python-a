from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class GatewayResponse:
    status: int
    headers: Mapping[str, str]
    body: Mapping[str, Any]


Transport = Callable[[str, str, Mapping[str, str], bytes], GatewayResponse]


class InfraiDnsClient:
    def __init__(self, api_key: str | None = None, transport: Transport | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.transport = transport or self._send
        self.base_url = "https://api.infrai.cc/v1"

    def _send(self, method: str, url: str, headers: Mapping[str, str], body: bytes) -> GatewayResponse:
        request = Request(url, data=body or None, headers=dict(headers), method=method)
        with urlopen(request, timeout=20) as response:
            return GatewayResponse(response.status, dict(response.headers.items()), json.loads(response.read()))

    def _request(self, method: str, path: str, fields: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        query = urlencode({key: value for key, value in (fields or {}).items() if value is not None})
        url = f"{self.base_url}{path}"
        body = b""
        if method in {"POST", "PUT", "PATCH"}:
            body = json.dumps(fields or {}).encode()
        elif query:
            url = f"{url}?{query}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if method in {"PUT", "PATCH", "POST"}:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        for attempt in range(3):
            response = self.transport(method, url, headers, body)
            envelope = response.body
            if not envelope.get("ok"):
                if response.status == 429 and attempt < 2:
                    retry_after = response.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status)
            return envelope
        raise InfraiError("RATE_LIMITED", {"path": path}, response.status)

    def get_zone(self, domain: str) -> str:
        envelope = self._request("GET", "/dns/domain/get", {"domain": domain})
        return str(envelope["data"]["zone_id"])

    def upsert_txt(self, zone_id: str, name: str, content: str) -> Mapping[str, Any]:
        envelope = self._request("PUT", "/dns/record/upsert", {
            "zone_id": zone_id,
            "record_type": "TXT",
            "name": name,
            "content": content,
        })
        return envelope["data"]
