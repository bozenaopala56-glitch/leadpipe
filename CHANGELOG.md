# Changelog

Format zgodny z Keep a Changelog. Projekt uzywa conventional commits.

## [Unreleased]

### Added

- Kompletna dokumentacja projektu: README, API reference, architektura, rulesety i contributing guide.

## [0.1.0] - 2026-05-27

### Added

- CLI `leadpipe` z komendami `import`, `scan`, `decide` i `pipeline`.
- T1 parsers: JSON-LD, kontakt, formularze, CTA, industry classification i runner `run_t1`.
- T0.5 enrichment: NIP extraction/checksum, Biala Lista VAT, cache i `run_t0_5`.
- T0 scanner: HTTP, DNS, SSL/TLS, HTML, tech detection, performance, agregacja sygnalow i batch runner.
- Modele Pydantic dla leadow, scanow, sygnalow, dowodow, decyzji, trace, feedbacku, suppression i batchy.
- SQLAlchemy schema dla Postgres.
- YAML rulesety dla gates, kampanii, evidence, suppression, feedback i T2 eligibility.
- Dashboard sample, deployment files i pliki planowania projektu.

### Changed

- Przeprowadzono kompleksowy audyt i poprawki kontraktow runtime.
- Kampanie zostaly ustawione jako finalny zestaw WWW-first: `REDESIGN_OUTDATED`, `REDESIGN_ADS_WASTE`, `REDESIGN_CONVERSION`, `REDESIGN_TRUST`, `WORDPRESS_REWORK`, `MOBILE_REBUILD`, `TECH_REBUILD`.

### Fixed

- Dopasowano engine, modele i testy do config-first rulesetow YAML.
- Ustabilizowano testy T0, T0.5, T1, CLI i modeli.

### Deprecated

- Samodzielne kampanie techniczne z wczesnych specyfikacji sa traktowane jako historyczne albo jako evidence modifiers, nie jako glowne kampanie runtime.

## [Research/spec] - 2026-05-23

### Added

- Pierwotna specyfikacja T0/T1/T2 i pytania do analizy.
- Krytyczna analiza pipeline'u, rekomendujaca T0.5, feedback loop, selektywne T2 i produkcyjny storage.
- Pelny projekt koncepcyjny: architektura, reguly, dashboard, deploy, plany i zadania TDD.
