from __future__ import annotations

from leadpipe.models import Lead
from leadpipe.t0_5 import run_t0_5
from leadpipe.t0_5.cache import EnrichmentCache
from leadpipe.t0_5.enrich_nip import extract_nips, is_valid_nip, normalize_nip
from leadpipe.t0_5.enrich_vat import validate_vat_number


def test_nip_checksum_and_extraction_ignores_phone_like_numbers() -> None:
    assert normalize_nip("123-456-32-18") == "1234563218"
    assert is_valid_nip("1234563218")
    assert not is_valid_nip("1234567890")

    html = "NIP: 123-456-32-18, tel. +48 22 123 45 67, REGON 012345678"
    assert extract_nips(html) == ["1234563218"]


def test_vat_number_validation_accepts_polish_nip_with_prefix() -> None:
    assert validate_vat_number("PL1234563218")
    assert validate_vat_number("123-456-32-18")
    assert not validate_vat_number("PL1234567890")


def test_enrichment_cache_roundtrip_and_expiry(tmp_path) -> None:
    cache = EnrichmentCache(tmp_path / "cache.json", ttl_seconds=10)
    cache.set("nip:1234563218", {"regon": "123"})

    assert cache.get("nip:1234563218") == {"regon": "123"}

    expired = EnrichmentCache(tmp_path / "cache.json", ttl_seconds=-1)
    assert expired.get("nip:1234563218") is None


def test_run_t0_5_merges_nip_regon_vat_and_address() -> None:
    lead = Lead(input_domain="example.pl", normalized_domain="example.pl", company_name="Example")

    def nip_lookup(_lead: Lead, _html_text: str) -> dict[str, object]:
        return {
            "nip": "1234563218",
            "regon": "123456789",
            "legal_form": "SPOLKA Z OGRANICZONA ODPOWIEDZIALNOSCIA",
            "address": "ul. Testowa 1, 00-001 Warszawa",
        }

    def vat_lookup(nip: str) -> dict[str, object]:
        assert nip == "1234563218"
        return {"vat_status": "active", "vat_valid": True}

    enriched = run_t0_5(lead, html_text="", nip_lookup=nip_lookup, vat_lookup=vat_lookup)

    assert enriched["lead"]["nip"] == "1234563218"
    assert enriched["enrichment"]["regon"] == "123456789"
    assert enriched["enrichment"]["vat_status"] == "active"
    assert enriched["signals"]["nip_present"] is True
    assert enriched["signals"]["vat_active"] is True
