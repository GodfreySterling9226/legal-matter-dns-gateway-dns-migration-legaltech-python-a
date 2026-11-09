from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from .infrai_dns import InfraiDnsClient


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    domain: str
    signed_document: str
    deadline: date


@dataclass(frozen=True)
class MatterResult:
    matter_id: str
    document_digest: str
    follow_up_on: date
    follow_up_required: bool
    record_id: str


def process_matter(
    intake: MatterIntake,
    client: InfraiDnsClient,
    today: date | None = None,
) -> MatterResult:
    current = today or date.today()
    digest = hashlib.sha256(intake.signed_document.encode()).hexdigest()
    zone_id = client.get_zone(intake.domain)
    record = client.upsert_txt(zone_id, f"_signed.{intake.domain}", f'"{intake.matter_id}:{digest}"')
    follow_up_on = intake.deadline - timedelta(days=1)
    return MatterResult(
        matter_id=intake.matter_id,
        document_digest=digest,
        follow_up_on=follow_up_on,
        follow_up_required=current >= follow_up_on,
        record_id=str(record.get("record_id", "")),
    )


def main() -> None:
    domain = os.environ.get("INFRAI_DNS_DOMAIN")
    if not domain:
        raise SystemExit("set INFRAI_DNS_DOMAIN to a domain visible to the gateway")
    zone_id = InfraiDnsClient().get_zone(domain)
    print({"domain": domain, "zone_id": zone_id})


if __name__ == "__main__":
    main()
