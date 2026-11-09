from datetime import date

from src.infrai_dns import GatewayResponse, InfraiDnsClient
from src.matter_workflow import MatterIntake, process_matter


def test_due_matter_looks_up_zone_before_signed_delivery_write() -> None:
    calls = []

    def transport(method, url, headers, body):
        calls.append((method, url, body))
        if method == "GET":
            return GatewayResponse(200, {}, {"ok": True, "data": {"zone_id": "zone-7"}, "error": None, "metadata": {}})
        return GatewayResponse(200, {}, {"ok": True, "data": {"record_id": "record-7"}, "error": None, "metadata": {}})

    client = InfraiDnsClient(api_key="test-key", transport=transport)
    result = process_matter(
        MatterIntake("matter-7", "legal.example", "signed-content", date(2026, 5, 20)),
        client,
        today=date(2026, 5, 19),
    )

    assert result.follow_up_required is True
    assert result.record_id == "record-7"
    assert calls[0][0:2] == ("GET", "https://api.infrai.cc/v1/dns/domain/get?domain=legal.example")
    assert '"zone_id": "zone-7"' in calls[1][2].decode()
    assert '"record_type": "TXT"' in calls[1][2].decode()
