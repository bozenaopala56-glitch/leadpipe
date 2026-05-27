# Contributing

Projekt jest prowadzony TDD: najpierw test, potem minimalna implementacja, potem regresja.

## Uruchamianie Testow

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest
```

Pełna instalacja developerska:

```bash
pip install -e ".[test,postgres,csv]"
```

## Konwencje

- Kod runtime trzymaj w `leadpipe/`.
- Testy dodawaj w `tests/` jako `test_*.py`.
- Publiczne modele i kontrakty waliduj Pydantic.
- Reguly biznesowe trzymaj w YAML, nie hardcoduj progow kampanii w Pythonie.
- `send` w MVP znaczy "gotowe do QA/CSV", nie automatyczna wysylka.
- Nie dodawaj T2 globalnie; T2 ma byc selektywne i sterowane rulesetem.

## Jak Dodac Nowy Modul

1. Dodaj test w `tests/`, ktory opisuje publiczna funkcje albo kontrakt.
2. Utworz modul w odpowiednim miejscu:
   - T0: `leadpipe/t0/`;
   - T0.5: `leadpipe/t0_5/`;
   - T1: `leadpipe/t1/`;
   - decyzje/rules: `leadpipe/engine.py` lub `leadpipe/rules/`;
   - modele/storage: `leadpipe/models.py`, `leadpipe/db_schema.py`.
3. Jesli modul ma byc publiczny, dodaj eksport w `__init__.py`.
4. Uruchom `pytest`.

## Jak Dodac Nowy Ruleset

1. Dodaj plik YAML w `leadpipe/rules/` albo rozszerz istniejacy.
2. Uzyj formatu `version` + `rules`.
3. Nadaj unikalny `key` i przemyslany `priority`.
4. Uzywaj operatorow obslugiwanych przez `DecisionEngine`: `exists`, `missing`, `eq`, `neq`, `in`, `contains`, `gte`, `gt`, `lte`, `lt`.
5. Dodaj test, ktory odpala `DecisionEngine()` i sprawdza oczekiwana decyzje.

## Jak Dodac Nowa Kampanie

1. Dodaj wartosc do `CampaignKey` w `leadpipe/models.py`.
2. Dodaj regule w `leadpipe/rules/campaigns.yml`.
3. Dodaj fixture sygnalow dla happy path i konfliktow.
4. Dodaj test, ze `DecisionEngine.evaluate()` zwraca nowa kampanie.
5. Zaktualizuj dokumentacje rulesetu i dashboard/sample data, jesli kampania ma byc widoczna dla QA.

Przed dodaniem kampanii sprawdz, czy nie da sie jej wyrazic jako evidence dla jednej z obecnych 7 kampanii WWW-first.

## Commit

Uzywaj conventional commits, np.:

```text
feat: add t1 meta parser
fix: handle invalid vat lookup response
docs: update rules reference
test: cover suppression cooldown
```
