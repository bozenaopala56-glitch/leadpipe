from __future__ import annotations

from leadpipe.t1 import run_t1
from leadpipe.t1.contact import extract_contacts
from leadpipe.t1.cta import analyze_ctas
from leadpipe.t1.forms import analyze_forms
from leadpipe.t1.industry import classify_industry
from leadpipe.t1.jsonld import extract_jsonld


HTML = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"LocalBusiness","name":"Alfa Instalacje",
 "telephone":"+48 22 123 45 67","email":"biuro@alfa.pl",
 "address":{"streetAddress":"Testowa 1","addressLocality":"Warszawa"},
 "sameAs":["https://www.facebook.com/alfa"]}
</script>
</head><body>
<a href="mailto:kontakt@alfa.pl">Email</a>
<a href="tel:+48221234567">Telefon</a>
<a href="https://linkedin.com/company/alfa">LinkedIn</a>
<a class="btn" href="/kontakt">Umow konsultacje</a>
<form action="/kontakt" method="post">
  <input name="email"><textarea name="message"></textarea>
</form>
Producent instalacji przemyslowych dla firm.
</body></html>
"""


def test_jsonld_extracts_organization_contact_and_address() -> None:
    data = extract_jsonld(HTML)

    assert data["items"][0]["type"] == "LocalBusiness"
    assert data["organization"]["name"] == "Alfa Instalacje"
    assert data["organization"]["email"] == "biuro@alfa.pl"
    assert data["organization"]["address"]["addressLocality"] == "Warszawa"


def test_contact_extraction_finds_email_phone_and_social() -> None:
    contacts = extract_contacts(HTML)

    assert "kontakt@alfa.pl" in contacts["emails"]
    assert any(phone.endswith("1234567") for phone in contacts["phones"])
    assert contacts["social"]["linkedin"] == ["https://linkedin.com/company/alfa"]
    assert contacts["contactability"] >= 80


def test_forms_and_cta_analysis() -> None:
    forms = analyze_forms(HTML)
    ctas = analyze_ctas(HTML)

    assert forms["form_present"] is True
    assert forms["forms"][0]["action"] == "/kontakt"
    assert {"email", "message"}.issubset(set(forms["forms"][0]["fields"]))
    assert ctas["cta_missing"] is False
    assert ctas["weak_cta"] is False


def test_industry_classification_detects_competitors_and_b2b_fit() -> None:
    competitor = classify_industry("Projektowanie stron www, SEO, Google Ads i sklepy internetowe")
    producer = classify_industry(HTML)

    assert competitor["competitor"] is True
    assert competitor["industry_fit"] < 40
    assert producer["industry"] == "industrial"
    assert producer["lead_value"] >= 70


def test_run_t1_aggregates_structured_data_and_signals() -> None:
    result = run_t1(HTML, headers={"content-type": "text/html"})

    assert result["contacts"]["emails"]
    assert result["forms"]["form_present"] is True
    assert result["industry"]["industry"] == "industrial"
    assert result["signals"]["has_email"] is True
    assert result["signals"]["form_present"] is True
    assert result["signals"]["industry_fit"] >= 70
    assert result["signals"]["t1_confidence"] >= 0.7
    assert result["signals"]["campaign_confidence"] == result["signals"]["t1_confidence"]


def test_run_t1_uses_jsonld_contact_when_visible_contact_is_missing() -> None:
    html = """
    <script type="application/ld+json">
    {"@type":"Organization","email":"biuro@example.pl","telephone":"+48 22 123 45 67"}
    </script>
    """

    result = run_t1(html)

    assert "biuro@example.pl" in result["contacts"]["emails"]
    assert "+48 22 123 45 67" in result["contacts"]["phones"]
    assert result["signals"]["has_email"] is True
    assert result["signals"]["has_phone"] is True
