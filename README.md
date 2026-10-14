# Public Procurement Risk Observatory & Territorial Early Warning System

> **Observatorio de Contratación Pública & Panel de Alertas y Semáforos de Riesgo Territorial (SECOP II)**  
> High-performance analytical web application built with **Shiny for Python**, engineered under **Posit PBC** software engineering guidelines, reactive design patterns, and ggplot2-inspired visual standards.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Shiny for Python](https://img.shields.io/badge/Shiny%20for%20Python-v1.8%2B-1d3190.svg)](https://shiny.posit.co/py/)
[![Tests](https://img.shields.io/badge/Tests-42%20Passed-059669.svg)](https://pytest.org/)
[![Visual Style](https://img.shields.io/badge/Theme-Grammar%20of%20Graphics-0284c7.svg)](https://plotly.com/)
[![Deployment](https://img.shields.io/badge/Deployment-Posit%20Connect%20Cloud-0f172a.svg)](https://connect.posit.cloud)

**Author:** Miguelangel Palma  
- **LinkedIn:** [miguelangelpr](https://www.linkedin.com/in/miguelangelpr)  
- **GitHub:** [MPalma21](https://github.com/MPalma21)  
- **Deployment Platform:** [Posit Connect Cloud](https://connect.posit.cloud)  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Key Capabilities & Analytical Perspectives](#key-capabilities--analytical-perspectives)
3. [Econometric & Methodology Framework](#econometric--methodology-framework)
4. [Visual Design System & Semaphore Hierarchy](#visual-design-system--semaphore-hierarchy)
5. [System Architecture](#system-architecture)
6. [Repository Structure](#repository-structure)
7. [Data Source & API Ingestion](#data-source--api-ingestion)
8. [Installation & Local Execution](#installation--local-execution)
9. [Automated Test Suite](#automated-test-suite)
10. [Deployment to Posit Connect Cloud](#deployment-to-posit-connect-cloud)
11. [Git Commit Standards](#git-commit-standards)

---

## Executive Summary

The **Public Procurement Risk Observatory** is an econometric and institutional audit platform designed to monitor, detect, and quantify anti-competitive risk, market concentration, and discretionary single-source contracting across Colombian territorial jurisdictions.

Powered by direct real-time integration with Colombia's national open data portal ([datos.gov.co](https://www.datos.gov.co/)) via the SODA REST API, the platform streams transactional public procurement records from **SECOP II** (`jbjy-vk9h`). It computes market power metrics, identifies oligopolistic supplier cartels, benchmarks jurisdictional vulnerability against OECD regulatory standards, and models counterfactual fiscal savings from anti-corruption and competitive procurement reforms.

---

## Key Capabilities & Analytical Perspectives

The application is structured into five cohesive, specialized modules accessible via the top navigation interface:

```
[ Top Navigation Bar ]
  ├── 1. Territorial Risk Radar     (mod_risk_radar.py)
  ├── 2. Departmental Audit         (mod_risk_drilldown.py)
  ├── 3. Dominant Contractors       (mod_risk_contractors.py)
  ├── 4. Reform Policy Simulator    (mod_simulator.py)
  └── 5. Evidence Matrix & Microdata (mod_risk_evidence.py)
```

### 1. Territorial Risk Radar (`mod_risk_radar.py`)
- **Macro-Territorial Synthesis:** Aggregates procurement data across departments into an executive KPI dashboard (Total Audited Budget, Critical Jurisdictions, Weighted National Direct Rate, and Worst-Case Territory).
- **HHI Departmental Ranking:** Horizontal bar chart color-coded with the executive semaphore highlighting jurisdictions exceeding DOJ/OECD concentration thresholds ($HHI > 2500$).
- **Two-Dimensional Risk Quadrant:** Scatter plot mapping Direct Contracting Rate (%) against HHI Concentration with bubble sizes proportional to total audited budget and reference threshold lines.
- **Early Warning Panel:** Automated warning cards isolating jurisdictions with critical risk detonators (e.g., direct contracting $> 65\%$, single supplier capturing $> 40\%$ of territorial expenditure).

### 2. In-Depth Departmental Audit (`mod_risk_drilldown.py`)
- **Jurisdictional Dossier:** Dynamic department selector with automatic executive profile breakdown (Total Contracts, HHI, Direct Rate, Top Contractor, and Modality Distribution).
- **Local Supplier Structure:** Bar chart quantifying local market share among leading vendors in the selected territory.
- **Modality Breakdown:** Donut chart categorizing procurement procedures (Direct Contracting, Open Public Bidding, Abbreviated Selection, and Minimum Value).
- **Atypical Mega-Contracts Audit:** Detects individual contractual outliers exceeding the 75th and 90th expenditure percentiles.
- **Automated Technical Diagnosis:** Generates fiscal oversight recommendations tailored to the specific irregularities found in the department.

### 3. Market Power & Dominant Contractors (`mod_risk_contractors.py`)
- **Industrial Concentration KPIs:** Computes the **CR4** (market share of the 4 largest contractors) and **CR8** oligopoly ratios, flagging markets where a small cartel controls $> 50\%$ of public spending.
- **Top 15 Accumulated Budget Ranking:** Identifies national procurement conglomerates by total awarded capital.
- **100% Stacked Allocation Breakdown:** Directly contrasts each leading contractor's revenue derived from **Direct Allocation (discretionary)** vs. **Open Competitive Bidding (transparent)**, exposing political dependency.
- **Audited Contractor Directory:** Filterable data table classifying vendors into Critical Risk, Moderate Risk, and Competitive categories.

### 4. Counterfactual Policy Simulator (`mod_simulator.py`)
- **Interactive Policy Sliders:** Allows economists and policy analysts to simulate regulatory reforms by reducing direct contracting ($0\% - 80\%$) and fostering supplier concurrency ($0\% - 100\%$).
- **OECD Fiscal Savings Benchmark:** Applies an empirical $12.5\%$ cost-reduction benchmark (OECD procurement literature) to all expenditures migrated from single-source direct allocation to open competitive bidding.
- **Before-and-After Comparisons:** Side-by-side KPI cards showing projected reductions in direct allocation and market de-concentration ($\Delta HHI$).
- **Comparative Impact Charts:** Grouped bar charts comparing baseline vs. counterfactual metrics and a budget decomposition pie chart.

### 5. Evidence Matrix & Microdata (`mod_risk_evidence.py`)
- **Territorial Evidence Table:** Consolidated matrix of all audited departments with integrated multi-level semaphore filters (All, High Risk Only, Moderate Risk Only, Competitive Only).
- **Granular Contract-Level Flags:** Individual contract browser identifying high-value direct allocations, single-bidder processes, and extraordinary contract amendments.
- **Secure CSV Export:** Exports sanitized datasets with automatic spreadsheet formula injection protection (neutralizing untrusted `=` or `+` prefixes).

---

## Econometric & Methodology Framework

The platform's analytical core in `services/economic_service.py` is founded on Industrial Organization and Public Economics literature:

1. **Herfindahl-Hirschman Index ($HHI$):**
   $$\text{HHI} = \sum_{i=1}^{N} s_i^2$$
   Where $s_i$ is the percentage market share of supplier $i$.
   - **$HHI < 1,500$:** Competitive market structure (Low Risk).
   - **$1,500 \le HHI \le 2,500$:** Moderate concentration (Medium Risk).
   - **$HHI > 2,500$:** Highly concentrated / oligopolistic market structure (Critical Risk).

2. **Direct Contracting Rate ($\% \text{ Direct}$):**
   $$\% \text{ Direct} = \frac{\text{Budget awarded via single-source direct contracting}}{\text{Total procurement budget}} \times 100$$
   - **$\% \text{ Direct} > 65\%$:** Critical Alert (potential evasion of open bidding mandates).
   - **$35\% \le \% \text{ Direct} \le 65\%$:** Moderate Alert.
   - **$\% \text{ Direct} < 35\%$:** Healthy Competitive Compliance.

3. **Composite Territorial Risk Score:**
   $$\text{Score} = 0.55 \times (\% \text{ Direct}) + 0.45 \times \left(\frac{\text{HHI}}{100}\right)$$

4. **Concentration Ratios ($CR_k$):**
   $$CR_k = \sum_{i=1}^{k} s_i$$
   Measures the cumulative budget share absorbed by the top $k$ contractors (computed for $CR_4$ and $CR_8$).

5. **Counterfactual Fiscal Savings Estimation:**
   $$\text{Transferred Budget} = \text{Base Direct Budget} \times \text{Reduction Ratio}$$
   $$\text{Fiscal Savings} = \text{Transferred Budget} \times 12.5\% \text{ (OECD Benchmark)}$$

---

## Visual Design System & Semaphore Hierarchy

The platform implements an institutional design system ensuring maximum contrast, cognitive legibility, and zero visual overlap:

### 1. Classic Executive Semaphore Palette
| Alert Level | Hex Code | Visual Swatch | Semantic Function |
| :--- | :--- | :--- | :--- |
| **Critical Risk (High)** | `#dc2626` | Crimson Red | Direct allocation, $HHI > 2500$, direct contracting $> 65\%$, warning banners |
| **Moderate Risk (Medium)** | `#d97706` | Warm Amber | Moderate concentration ($1500 - 2500$), transitional contracting |
| **Competitive / Low Risk** | `#059669` | Emerald Green | Competitive public bidding, $HHI < 1500$, counterfactual fiscal savings |
| **Institutional Corporate Base** | `#1d3190` | Royal Cobalt | Primary branding, neutral budget bars, card borders |
| **Midnight Surface** | `#080c42` | Midnight Navy | Global navbar, executive headers, deep contrast elements |
| **Secondary Accents** | `#0284c7` / `#93c5fd` | Sky / Ice Blue | Minimum-value contracting, informational badges |

### 2. Layout & Typography Rules
- **Vertical Card-Header Hierarchy:** Every card in the application strictly positions subtitles **underneath** the title using `.card-header-heading`, `.card-header-title`, and `.card-header-subtitle` block containers with CSS flex-column enforcement.
- **Zero-Overlap Plot Engine (`components/plot_theme.py`):**
  - Margins dynamically computed to prevent collisions between multi-line headers, subtitles, and axes.
  - Horizontal legends placed exclusively at the bottom ($y = -0.22$, bottom margin $85\text{px}$).
  - Plotly floating modebars permanently disabled (`displayModeBar: False`) to eliminate floating toolbars over chart titles.
- **Strict Zero-Emoji Standard:** Pure executive typography, CSS badges, and SVG icons.

---

## System Architecture

The application adheres to a clean 4-tier modular architecture:

```
[ Client / Browser ]
        │
        ▼ (HTTP / WebSockets via Starlette ASGI)
[ Presentation Layer: app.py + www/styles.css ]
        │
        ├─ Assembles responsive navbar layout (ui.page_navbar)
        ├─ Global contextual data banner (components/banner.py)
        ├─ Interactive methodology modal (components/guide_modal.py)
        │
        ▼
[ Reactive Controller Layer: modules/ ]
        │
        ├─ mod_loader.py          -> SODA ingestion trigger & volume parameters
        ├─ mod_risk_radar.py       -> Macro risk ranking, quadrants & alerts
        ├─ mod_risk_drilldown.py   -> Territorial dossier, modalities & outliers
        ├─ mod_risk_contractors.py -> Market power, CR4 & 100% stacked bars
        ├─ mod_simulator.py        -> Policy counterfactual & fiscal savings
        └─ mod_risk_evidence.py    -> Microdata matrix & secure CSV export
        │
        ▼ (Pure Python domain function calls)
[ Domain Logic & Services Layer: services/ ]
        │
        ├─ economic_service.py -> HHI, Gini, CR4, risk matrix, simulation algorithms
        ├─ api_service.py      -> Socrata SODA REST client with type casting
        ├─ scope_service.py    -> Territorial filtering & reproducible sampling
        ├─ table_service.py    -> Search filtering & formula injection prevention
        └─ stats_service.py    -> Statistical summaries, correlation & normality
```

---

## Repository Structure

```text
Shiny APP Python/
├── app.py                         Application entry point and global layout assembly
├── config.py                      Global configuration, endpoints, thresholds, and defaults
├── pyproject.toml                 Project metadata, dependencies, and pytest configuration
├── requirements.txt               Pinned dependencies for deployment environments
├── manifest.json                  Posit Connect Cloud deployment manifest
├── README.md                      Technical documentation and architecture guide
│
├── components/                    Shared UI components and graphic themes
│   ├── __init__.py
│   ├── banner.py                  Global context banner with dataset scope
│   ├── guide_modal.py             Methodology modal with legal and econometric guidelines
│   └── plot_theme.py              Grammar of Graphics Plotly theme & color constants
│
├── modules/                       Shiny for Python encapsulated reactive modules
│   ├── __init__.py
│   ├── mod_loader.py              Sidebar controls: dataset source, volume & fetch trigger
│   ├── mod_risk_radar.py          Perspective 1: Territorial risk radar, HHI & quadrants
│   ├── mod_risk_drilldown.py      Perspective 2: In-depth departmental audit & outliers
│   ├── mod_risk_contractors.py    Perspective 3: Market concentration, CR4 & 100% stacked bars
│   ├── mod_simulator.py           Perspective 4: Policy counterfactual & OECD savings model
│   └── mod_risk_evidence.py       Perspective 5: Microdata evidence matrix & CSV export
│
├── services/                      Pure domain logic and algorithmic services (100% testable)
│   ├── __init__.py
│   ├── economic_service.py        Econometric engine: HHI, CR4/CR8, Gini, risk & simulations
│   ├── api_service.py             SODA REST client with robust type casting & URL parsing
│   ├── scope_service.py           Data scoping, temporal filters & reproducible sampling
│   ├── table_service.py           Table search indexing & CSV export sanitization
│   └── stats_service.py           General descriptive statistics, correlation & normality
│
├── tests/                         Automated test suite (pytest)
│   ├── __init__.py
│   ├── test_banner.py             Tests for context banner formatting and author credits
│   ├── test_data_flow.py          Tests for SODA client, parsing, sanitization & limits
│   ├── test_economic_service.py   Tests for HHI, CR4, risk matrices & policy simulator
│   └── test_services.py           Tests for URL extraction, column classification & stats
│
└── www/                           Static web assets served natively by ASGI
    ├── styles.css                 Production stylesheet with Positron/Executive palette
    └── logo.svg                   Vector logo for navigation branding
```

---

## Data Source & API Ingestion

The application queries Colombia's official open data portal ([datos.gov.co](https://www.datos.gov.co/)) via Socrata Open Data API (SODA):

- **Default Endpoint:** `https://www.datos.gov.co/resource/jbjy-vk9h.json` (SECOP II Electronic Contracts).
- **Protocol:** HTTPS REST with structured SQL-like parameters (`$limit`, `$offset`, `$order`, `$where`, `$q`).
- **Resilience:** Automatic type inference for numeric values, dates, and currency fields with fallback mechanisms preserving leading zeros in territorial codes.
- **Performance:** Ingestion is executed asynchronously via `ExtendedTask`, keeping the WebSocket event loop responsive.

---

## Installation & Local Execution

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed.
- Git.

### 1. Clone Repository
```bash
git clone https://github.com/MPalma21/eda-colombia-shiny.git
cd eda-colombia-shiny
```

### 2. Create Virtual Environment
```bash
# On Windows PowerShell:
python -m venv .venv
.venv\Scripts\Activate.ps1

# On macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install in editable mode via `pyproject.toml`:
```bash
pip install -e .
```

### 4. Run the Application Locally
```bash
shiny run app.py --port 8000 --reload
```
Open your browser at `http://127.0.0.1:8000`.

---

## Automated Test Suite

The repository includes a comprehensive test suite with **42 automated unit and integration tests** executing in milliseconds without browser emulation:

```bash
pytest -v
```

### Test Coverage Highlights:
- **`tests/test_economic_service.py`:** Validates $HHI$ calculations, Gini/Lorenz bounds, $CR_4$ concentration ratios, risk matrix edge cases, and the OECD policy counterfactual simulation algorithm.
- **`tests/test_data_flow.py`:** Validates SODA API URL/resource ID parser, type sanitization, formula injection protection (`=SUM`, `@import`), distributed fetch offsets, and reproducible sampling.
- **`tests/test_banner.py`:** Tests scope explanation, sample limitations, and author credits integrity.
- **`tests/test_services.py`:** Tests column classification, correlation matrices, descriptive summaries, and Shapiro-Wilk normality tests.

---

## Deployment to Posit Connect Cloud

The application is deployed to **Posit Connect Cloud**. To synchronize the deployment bundle:

```bash
# Generate / update the deployment manifest:
rsconnect write-manifest shiny . --overwrite

# Commit and push to main:
git add manifest.json requirements.txt
git commit -m "chore(deploy): sync manifest for Posit Connect Cloud"
git push origin main
```

---

## Git Commit Standards

This repository strictly enforces **Conventional Commits** in **English**:

```
<type>(<scope>): <subject>

Examples:
feat(ui): implement classic executive semaphore palette with navy corporate base
fix(charts): eliminate overlapping titles and legends across all Plotly figures
feat(analytics): replace scatter plot with 100% stacked horizontal bar chart
perf(app): vectorize dataframe operations and optimize cache utilization
docs: update README with comprehensive architecture and methodology guide
```

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.

---

## Author & Contact

**Developed by Miguelangel Palma**  
- **LinkedIn:** [linkedin.com/in/miguelangelpr](https://www.linkedin.com/in/miguelangelpr)  
- **GitHub:** [github.com/MPalma21](https://github.com/MPalma21)  
- **Live Deployment:** [connect.posit.cloud](https://connect.posit.cloud)  
