# Chapter One: Introduction

**Project:** SkyRisk Auditor – 4D Tactical Multi-Hazard Flight Risk Assessment and Recovery Decision-Support System

**Final Year Project, Department of Software Engineering, University of Gujrat**

---

## 1.1 Introduction

### 1.1.1 Background

- A commercial aircraft cannot stop or pull over in the air. If a hazard appears ahead, the crew and the flight dispatcher must react early and choose a safe alternative.
- Before and during a flight, a dispatcher has to check many things at the same time: the flight path, thunderstorms, space weather, airspace restrictions (NOTAMs) and other aircraft nearby.
- In most airlines these information sources are kept in separate systems. Weather is on one screen, NOTAMs are in long text bulletins, and flight tracking is on a 2D radar screen.
- Because of this, the dispatcher has to join the information manually. This takes time, and important details can be missed.

### 1.1.2 Problem Statement

- NOTAMs are written in short, coded, capital-letter language. They are easy to misread. For example, "RUNWAY NOT CLOSED" can be wrongly flagged as a closure by a simple keyword search.
- Hazards are normally checked one by one. In real life they often occur together (for example, a thunderstorm inside a restricted area during a geomagnetic storm), and together they are more dangerous than the sum of the parts.
- Choosing an alternative route by hand is slow. The dispatcher must balance delay, fuel and safety using phone calls and calculations.
- Decisions are often not recorded in a form that can be checked later for tampering.

### 1.1.3 Proposed Solution

SkyRisk Auditor is a web-based, four-dimensional (latitude, longitude, altitude and time) decision-support system. It brings the separate information sources into one screen and helps the dispatcher decide. In simple words, it does the following:

- Stores flight plans and builds a 4D trajectory (path over space and time) for each flight.
- Finds hazards near the trajectory: convective weather, space weather, NOTAMs and aircraft-to-aircraft conflicts.
- Reads NOTAM text using a locally stored DistilBERT model, so no operational text is sent to a cloud service.
- Calculates one combined risk score from 0 to 100. When hazards overlap, a cascading multiplier increases the score.
- Creates four recovery route candidates (minimum delay, minimum fuel, safest buffer, balanced) and shows their delay, fuel and risk trade-offs.
- Keeps a human in the loop. Only an authorised Flight Dispatcher can approve a route.
- Generates an Operational Flight Plan (OFP) and saves every decision in a SHA-256 hash-chained audit record.
- Controls who can do what through Role-Based Access Control (RBAC).

### 1.1.4 Technology Overview

- **Frontend:** React 19 with Vite.
- **Backend:** Python with FastAPI, divided into five modules.
- **Database:** PostgreSQL, with an automatic SQLite fallback.
- **Machine learning:** DistilBERT (HuggingFace Transformers with PyTorch), running locally on CPU.
- **Data:** historical ADS-B flight data, weather data, NOAA space-weather data and NOTAM data for the Pakistan region.

### 1.1.5 Objectives

1. Combine trajectory, weather, space-weather, NOTAM and conflict information in a single operational view.
2. Calculate a clear and explainable combined risk score for every flight.
3. Classify NOTAM text automatically using a local machine-learning model.
4. Generate and compare recovery routes using delay, fuel and risk.
5. Make sure that final approval always stays with an authorised human.
6. Keep a tamper-evident record of every approval and operational decision.

### 1.1.6 Important Note

SkyRisk Auditor is an academic decision-support prototype. It is not a certified aviation system and it does not control aircraft. Recovery routes are candidates for review by qualified people, not certified clearances.

---

## 1.2 Project/Product Feasibility Report

Feasibility means checking how practical and useful it is to build the system with the staff, skills, time, data and equipment that are available. It is checked at the start and then repeated during the project. The eight feasibility types required by the guidelines are discussed below.

### 1.2.1 Technical Feasibility

**Question:** Can the system be built with the available technology, and do the team members have the required skills?

- **Technology is mature and open source.** React, FastAPI, PostgreSQL, SQLite, PyTorch and HuggingFace are all well documented and free to use.
- **Required skills are available.** The team works in Python, JavaScript/React, SQL, data processing with Pandas and NumPy, and basic NLP model use.
- **Hardware is modest.** DistilBERT has about 66 million parameters. It runs on an ordinary CPU, with a response time of roughly 40 ms per NOTAM in our tests. No GPU is needed.
- **The design is modular.** Five backend modules can be built and tested one by one: Trajectory, Risk and Hazards, Recovery, OFP and Audit, and Authentication/RBAC.
- **The system is already running.** A working backend, frontend, database and local model exist, which proves that the main ideas are technically possible.
- **Limits of the theory.** Real weather, NOTAM and ADS-B feeds can be incomplete or delayed. For this reason, saved fallback datasets are included so that the system still works when a live source is down.

**Conclusion:** Technically feasible as a research and demonstration prototype. Certification and live-data validation would be needed before any real operational use.

### 1.2.2 Operational Feasibility

**Question:** Is the problem worth solving, will the solution work in daily use, and how will users feel about it?

- **The problem is real.** Dispatchers today use several disconnected tools, which causes slow decisions, extra fuel burn and safety risk.
- **The users are clearly defined:** Flight Dispatcher, Aviation Safety Analyst, Aviation Security Auditor and Meteorological Analyst.
- **The screens follow a real workflow:** overview dashboard, flight operations, 4D trajectory view, risk assessment, recovery planning, flight plan, approvals and audit, data sources, users and roles.
- **Human approval is kept.** The system suggests, and the dispatcher decides. This is how aviation operations must work, so users and managers are expected to accept it.
- **Easy to learn.** Colour-coded risk levels and side-by-side route cards reduce the time needed to understand a situation.
- **Known operational limits.** The user-role screen is a prototype directory and not a production identity system. Recovery routes still need expert validation.

**Conclusion:** Operationally feasible as a decision-support tool for evaluation, demonstration and future research.

### 1.2.3 Economic Feasibility

Economic feasibility compares costs with benefits.

**A. Cost estimates**

- *One-time development cost:* team effort, laptops/PCs, and data collection. Software is free and open source, so licence cost is zero.
- *Ongoing cost (maintenance and operation):* bug fixes, dataset updates, model updates, security improvements, hosting and backups.
- *Estimated size and effort* (full calculations are in Section 1.4):
  - Code size: 21,811 lines (21.8 KLOC).
  - Function-point effort: about 25.9 person-months.
  - COCOMO'81 effort: about 94.7 person-months (basic) and 120.9 person-months (intermediate).
- *Real cash cost for the university project is low,* because existing computers, free software and a local model are used. The large estimated value is the *commercial equivalent* of the team's time.

**B. Benefit estimates**

| Type | Benefit |
| --- | --- |
| Tangible | Less time spent checking many sources; faster decisions; lower fuel burn through balanced routes; no paid cloud-AI fees because the NOTAM model runs locally |
| Intangible | Better safety awareness; more confidence in decisions; clear accountability through audit records; better data privacy; strong learning value for the team; good external standing for the university |

**Conclusion:** Economically feasible. Costs are low for a university project, and the benefits (time, safety, traceability) are clear.

### 1.2.4 Schedule Feasibility

**Question:** Can the project be completed with the available staff and time, and can deadlines be met?

- The work is divided into 17 tasks (see Section 1.5). Many of them can be done in parallel by different members.
- The Critical Path Method (Section 1.6) gives a minimum project duration of **31 weeks**, which fits within a two-semester final year project.
- Testing, defect fixing and documentation each have their own time slots, so they are not squeezed in at the end.
- Milestones are fixed in the Gantt chart (Section 1.7) so progress can be checked regularly.
- Tasks with slack (for example, NOTAM model integration and authentication) can be moved a little without delaying the final date.

**Conclusion:** Schedule feasible, provided that the core modules are finished first and new features are not added late.

### 1.2.5 Specification Feasibility

**Question:** Are the requirements clear and definite, and are the scope boundaries known?

- Requirements are clear and can be tested. For example: calculate a risk score from 0 to 100; produce four route candidates; allow approval only for the Dispatcher role; verify the audit chain.
- Every requirement is linked to a backend module and a frontend screen, and the interface between them is a documented REST API.
- The boundaries are written down in Section 1.3. Air traffic control, automatic dispatch and aircraft control are outside the project.
- Requirements are managed by priority, effort and risk (Section 1.3.4), so scope discussions are based on facts and not on opinions.

**Conclusion:** Specification feasible, as long as the scope stays limited to decision support, risk analysis, route comparison and audit.

### 1.2.6 Information Feasibility

**Question:** Is the information complete, reliable and meaningful?

- **Available data:** ADS-B flight trajectories, weather data, NOAA space-weather (Kp index) data, NOTAM text, and recovery-route evaluation reports.
- **Completeness:** Data covers the Pakistan region for selected study periods. It is enough for experiments but not for full national or global operations.
- **Reliability:** Sources are public and well known (OpenSky Network, NOAA SWPC, Open-Meteo/AWC, ICAO/FAA-style NOTAMs).
- **Meaningfulness:** The data matches the hazards the system studies, but there are known limits:
  - Weather is kept as a reference grid. It is not joined to every single trajectory point, because one grid point cannot fairly represent every aircraft position.
  - The Kp index is a global indicator. It is a risk signal and not a direct flight limit.
  - Recovery routes are candidates and need further expert validation.
- **Handling the limits:** The limits are written in the documentation, and results are presented as research indicators.

**Conclusion:** Information feasible for research and prototype evaluation, with the limits clearly disclosed.

### 1.2.7 Motivational Feasibility

**Question:** Are the people involved motivated to do the necessary work correctly and on time?

- The project mixes web development, machine learning, databases, risk analysis and security. This gives team members strong learning and portfolio value.
- The result is visible and easy to demonstrate: dashboards, risk scores, route comparison and an audit ledger.
- Each module can be demonstrated alone, so progress is visible early and keeps motivation high.
- The supervisor and the department support the project, and a safety-related topic raises the interest of future users and examiners.
- Real aviation staff (dispatchers, analysts) have a clear need for a tool like this and are expected to welcome it.

**Conclusion:** Motivationally feasible.

### 1.2.8 Legal and Ethical Feasibility

**Question:** Do any infringements or liabilities arise from this project?

| Area | Position and action |
| --- | --- |
| Safety liability | The system does not control aircraft and does not issue clearances. Final decisions always stay with authorised humans. |
| Claims | Routes must not be called "certified" or "guaranteed safe". No regulatory compliance is claimed without formal approval. |
| Data licences | Public data is used under the terms of its source. Sources are acknowledged. |
| Privacy | Personal data and credentials are not exposed. NOTAM text is processed locally. |
| Fairness and transparency | Model results are shown with confidence values and limits. |
| Accountability | The SHA-256 audit record helps to show who decided what and when. It is not used to hide responsibility. |
| Security | Prototype-level security is acceptable for study. A real deployment would need stronger password handling, token management, transport security and full authorisation checks. |

**Conclusion:** Legally and ethically feasible as an academic decision-support prototype whose limits are clearly stated.

### 1.2.9 Feasibility Summary

| Feasibility type | Result |
| --- | --- |
| Technical | Feasible |
| Operational | Feasible |
| Economic | Feasible |
| Schedule | Feasible (31 weeks) |
| Specification | Feasible (scope controlled) |
| Information | Feasible (limits disclosed) |
| Motivational | Feasible |
| Legal and Ethical | Feasible (prototype only) |

---

## 1.3 Project/Product Scope

Scope is what lies **inside** the system boundary. Context is what lies **outside** it and interacts with it.

### 1.3.1 In Scope (Inside the System)

1. **Flight and 4D trajectory management:** create and read flight plans; store waypoints with latitude, longitude, altitude, speed, heading and time offset.
2. **Multi-hazard risk assessment:** find hazards near the trajectory in space and time; calculate individual hazard scores; calculate one combined score from 0 to 100; apply cascading multipliers when hazards overlap.
3. **NOTAM classification:** accept ICAO-style NOTAM text; classify it with the local DistilBERT model; show the class and its confidence.
4. **Recovery decision support:** generate four route candidates; compare delay, fuel, distance, residual risk and risk reduction; recommend a balanced route.
5. **Human approval:** only the Flight Dispatcher role can approve; other roles are read-only.
6. **OFP and audit:** create the Operational Flight Plan after approval; store audit events with SHA-256 hash chaining; verify the chain.
7. **Authentication and RBAC:** four roles with different capabilities.
8. **Monitoring and dashboards:** active flights, hazards, high-risk flights, separation conflicts, on-demand airspace scan and data-source status.

### 1.3.2 Out of Scope (Project Boundaries)

- Direct control of aircraft or air traffic.
- Automatic dispatch release or automatic route approval.
- Certified air traffic separation services.
- Airline crew and fleet scheduling.
- Real-time communication with aircraft.
- Certified weather forecasting and full terrain-clearance analysis.
- Production-grade identity management and single sign-on.
- Any guarantee of regulatory compliance.

### 1.3.3 Context (Outside the System, but Interacting with It)

| External element | Interaction |
| --- | --- |
| OpenSky Network (ADS-B) | Provides flight telemetry |
| NOAA SWPC | Provides Kp index and space-weather data |
| Open-Meteo / Aviation Weather Center | Provides convective weather data |
| ICAO / FAA-style NOTAM sources | Provide NOTAM text |
| Flight Dispatcher, Safety Analyst, Security Auditor, Meteorological Analyst | Human users |
| Aviation authorities and airline operations centres | Own the real operational decisions and certification |

### 1.3.4 Scope Management

- The project is built **iteratively**: the five modules are delivered in small, testable steps.
- Each requirement has three attributes: **priority**, **effort** and **risk**. These are used to decide whether a new request enters the scope.

| Requirement group | Priority | Effort | Risk | Decision |
| --- | --- | --- | --- | --- |
| Trajectory and risk engine | High | High | Medium | Include (core) |
| Recovery route generation | High | High | Medium | Include (core) |
| Approval, OFP and audit | High | Medium | Low | Include (core) |
| NOTAM classification | High | Medium | Medium | Include (core) |
| RBAC | Medium | Low | Low | Include |
| Dashboards and data-source status | Medium | Medium | Low | Include |
| Extra ideas (crew fatigue, passenger connections, multi-flight optimisation, anomaly detection) | Low | High | High | Excluded to keep the project manageable |

### 1.3.5 Intended Users

| Role | Main responsibility |
| --- | --- |
| Flight Dispatcher | Reviews flights, studies recovery routes and approves the final route |
| Aviation Safety Analyst | Inspects hazards, risk factors and cascading effects |
| Aviation Security Auditor | Verifies the audit chain and reviews user actions |
| Meteorological Analyst | Reviews weather, space weather and NOTAM results |

### 1.3.6 Expected Deliverables

- Working web prototype (React frontend and FastAPI backend).
- Multi-hazard risk engine and local NOTAM classifier.
- Recovery-route comparison component.
- Approval, OFP and audit workflow with RBAC.
- Historical data-processing and validation reports.
- Final project report and demonstration material.

---

## 1.4 Project/Product Costing

A **metric** is a measurement of a product or a process. There are two kinds:

- **Knowledge-oriented metrics** track the process to evaluate, predict or monitor it (for example effort, schedule, cost).
- **Achievement-oriented metrics** measure a product aspect, mostly its quality or size (for example lines of code, function points).

Cost estimation uses **algorithmic models**: mathematical formulas that link inputs (size, complexity) with outputs (effort, time, cost). This chapter uses three methods required by the guidelines: Function Point Analysis, COCOMO'81 and Activity-Based Costing.

### 1.4.0 Inputs and Assumptions

**Measured code size** (static count of the project):

| Subsystem | Technology | Files | Lines of code |
| --- | --- | --: | --: |
| Frontend application | React 19, JSX | 28 | 6,338 |
| Frontend design system | CSS design tokens | 5 | 1,563 |
| Backend API engine | Python, FastAPI | 18 | 5,702 |
| Flight data research scripts | Python (Pandas, GeoPy) | 22 | 7,728 |
| Database and seed scripts | SQLAlchemy / PostgreSQL | 4 | 480 |
| **Total** |  | **77** | **21,811 (21.8 KLOC)** |

**Assumptions** (they are our planning choices and can be changed):

- Labour rate = PKR 850,000 per person-month (about USD 3,000), the rate of a junior software engineer.
- Productivity = 10 function points per person-month.
- One month = 4.33 weeks, so one person-week costs about PKR 196,000.

### 1.4.1 Project Cost Estimation by Function Point Analysis (FPA)

FPA measures the functionality delivered to the user. It does not depend on the programming language.

#### Step 1: Count the five information-domain values

Weights used (Simple / Average / Complex): Inputs 3/4/6, Outputs 4/5/7, Inquiries 3/4/6, Internal files 7/10/15, External interfaces 5/7/10.

| Information domain | Items | Simple | Average | Complex | Function points |
| --- | --: | --: | --: | --: | --: |
| User inputs (EI) | 6 | 0 | 3 | 3 | 3×4 + 3×6 = **30** |
| User outputs (EO) | 6 | 0 | 3 | 3 | 3×5 + 3×7 = **36** |
| User inquiries (EQ) | 6 | 1 | 3 | 2 | 1×3 + 3×4 + 2×6 = **27** |
| Internal logical files (ILF) | 7 | 0 | 4 | 3 | 4×10 + 3×15 = **85** |
| External interfaces (EIF) | 4 | 0 | 2 | 2 | 2×7 + 2×10 = **34** |
| **Count total (UFP)** | **29** |  |  |  | **212** |

**What was counted in each domain:**

- **Inputs:** new flight plan with route waypoints (complex); NOTAM ingestion and classifier trigger (complex); route authorisation with digital signature (complex); space-weather calibration override (average); route rejection (average); user role and permission update (average).
- **Outputs:** combined 4D risk score with cascading result (complex); recovery candidate generation, routes A–D (complex); OFP release (complex); SHA-256 audit hash block (average); real-time conflict and proximity alert (average); fleet hazard summary gauge (average).
- **Inquiries:** trajectory retrieval (average); active hazard lookup (average); flight-to-flight separation distance (average); DistilBERT classification query (complex); audit chain verification (complex); RBAC capability lookup (simple).
- **Internal files:** flights and trajectory (complex); 4D hazards (complex); audit trail (complex); risk assessments (average); recovery plans (average); OFPs (average); users and RBAC (average).
- **External interfaces:** NOAA SWPC space weather (average); Open-Meteo convective weather (average); ICAO/FAA-style NOTAM stream (complex); OpenSky ADS-B telemetry (complex).

#### Step 2: Rate the 14 General System Characteristics (0 = no influence, 5 = strong influence)

| # | Characteristic | Rating | Reason |
| --- | --- | --: | --- |
| 1 | Data communications | 4 | Several external feeds and a web client |
| 2 | Distributed data processing | 3 | Client rendering and asynchronous server |
| 3 | Performance | 5 | About 40 ms NLP response, smooth radar drawing |
| 4 | Heavily used configuration | 4 | Many flights tracked and polled together |
| 5 | Transaction rate | 4 | Frequent state polling and trajectory updates |
| 6 | On-line data entry | 4 | Flight plan entry, approval notes |
| 7 | End-user efficiency | 5 | Dashboard and dual-view 4D radar |
| 8 | On-line update | 4 | Live updates of plans, risks, recovery |
| 9 | Complex processing | 5 | 4D geometry, Pareto optimisation, cascading maths, transformer model, hash chain |
| 10 | Reusability | 4 | Reusable UI parts and backend routers |
| 11 | Installation ease | 3 | Simple launch commands |
| 12 | Operational ease | 4 | Role switching, automatic classification |
| 13 | Multiple sites | 4 | Designed for several FIRs |
| 14 | Facilitate change | 4 | RBAC separation, replaceable model weights |
|  | **Total (ΣFi)** | **57** |  |

#### Step 3: Calculate the function points

```
VAF     = 0.65 + 0.01 × ΣFi = 0.65 + 0.01 × 57 = 1.22
FP est. = Count total × VAF = 212 × 1.22 = 258.64 FP
```

#### Step 4: Calculate cost and effort

```
Cost / FP            = labour rate / productivity = 850,000 / 10 = PKR 85,000
Total project cost   = FP est. × (cost / FP)  = 258.64 × 85,000 = PKR 21,984,400 (about PKR 22.0 million)
Total estimated effort = FP est. / productivity   = 258.64 / 10 = 25.9 person-months
```

**Use for scope control:** this count is taken at the end of requirements and design. At the end of coding and testing it should be counted again. If the later number is higher, the scope has grown (scope creep).

### 1.4.2 Project Cost Estimation by COCOMO'81

**Project type.** Semi-detached. The team knows web development well (React, REST APIs), but parts are new for us: 4D geometry, multi-objective route optimisation and transformer-based NOTAM classification. That puts it between Organic and Embedded.

**Size.** 21.811 KLOC.

#### Basic COCOMO (semi-detached: a = 3.0, b = 1.12, c = 2.5, d = 0.35)

```
Effort   PM   = 3.0 × (21.811)^1.12 = 3.0 × 31.57 = 94.72 person-months
Schedule TD   = 2.5 × (94.72)^0.35  = 2.5 × 4.92  = 12.3 months
People        = PM / TD = 94.72 / 12.3 = 7.7 persons
```

#### Intermediate COCOMO (effort adjusted by cost drivers, M)

Drivers that are not changed from "Nominal" have a multiplier of 1.00 and do not change the result.

| Cost driver | Why this rating | Rating | Multiplier |
| --- | --- | --- | --: |
| RELY – required reliability | Aviation safety context | High | 1.15 |
| DATA – database size | Large 4D coordinate data | High | 1.08 |
| CPLX – product complexity | 4D geometry, transformer, cryptography | Very high | 1.30 |
| TIME – execution time constraint | Fast radar drawing, \~40 ms NLP | High | 1.11 |
| ACAP – analyst capability | Good software and domain skills | High | 0.86 |
| MODP – modern practices | Modular design, REST, version control | High | 0.91 |
| TOOL – software tools | Vite, PyTorch, PostgreSQL, Git | High | 0.91 |
| All other drivers | Nominal | Nominal | 1.00 |

```
M  = 1.15 × 1.08 × 1.30 × 1.11 × 0.86 × 0.91 × 0.91 = 1.2764  (about 1.28)
PM = 3.0 × (21.811)^1.12 × M = 94.72 × 1.2764 = 120.9 person-months
Schedule (from Basic equation) = 12.3 months
People = Effort / Duration = 120.9 / 12.3 = 9.8 persons (about 10)
Cost   = 120.9 × PKR 850,000 = PKR 102,765,000 (about PKR 102.8 million, ≈ USD 362,700)
```

### 1.4.3 Comparison of the Two Estimates

| Item | Function Points | COCOMO'81 Basic | COCOMO'81 Intermediate |
| --- | --: | --: | --: |
| Effort (person-months) | 25.9 | 94.7 | 120.9 |
| Cost (PKR million) | 22.0 | 80.5 | 102.8 |

**How to read the difference (plain words):**

- FPA counts only what the user can see and use. COCOMO counts every line of code, including 7,728 lines of research and data-processing scripts (35% of the total code).
- FPA uses our assumed productivity of 10 FP per person-month. If real productivity is different, the FPA result changes directly.
- Our actual plan is 4 members for 31 weeks, which is about 28.6 person-months. This is close to the function-point estimate.
- The COCOMO values are the *commercial equivalent* of building the product in a company, not the real cash spent on this university project.

### 1.4.4 Activity-Based Costing (ABC)

ABC assigns resources to **activities**, and then activities to the **cost object** (the finished product). The four basic cost drivers are used:

- **Resources:** project members (M1–M4, see Section 1.8), computers, internet, data.
- **Cost rate:** PKR 196,000 per person-week (850,000 ÷ 4.33).
- **Duration:** taken from the task table (Section 1.5).
- **Overhead (fixed cost):** internet, electricity, printing and backup storage. Assumed at PKR 150,000 for the whole project.

| Task | Activity | People | Duration (weeks) | Person-weeks | Cost (PKR) |
| --- | --- | --: | --: | --: | --: |
| T1 | Problem analysis and objectives | 2 | 2 | 4 | 784,000 |
| T2 | Feasibility and scope | 1 | 2 | 2 | 392,000 |
| T3 | Domain and literature review | 2 | 3 | 6 | 1,176,000 |
| T4 | Data collection | 2 | 3 | 6 | 1,176,000 |
| T5 | Requirements, use cases, vision | 3 | 3 | 9 | 1,764,000 |
| T6 | Architecture and database design | 2 | 3 | 6 | 1,176,000 |
| T7 | Data preparation and validation | 2 | 4 | 8 | 1,568,000 |
| T8 | Module 1: 4D trajectory | 1 | 4 | 4 | 784,000 |
| T9 | Module 2: risk and hazards | 2 | 5 | 10 | 1,960,000 |
| T10 | NOTAM model integration | 1 | 5 | 5 | 980,000 |
| T11 | Module 3: recovery routes | 2 | 4 | 8 | 1,568,000 |
| T12 | Modules 4 and 5: OFP, audit, RBAC | 1 | 4 | 4 | 784,000 |
| T13 | React frontend and dashboards | 1 | 6 | 6 | 1,176,000 |
| T14 | Integration | 4 | 3 | 12 | 2,352,000 |
| T15 | Functional and data testing | 4 | 3 | 12 | 2,352,000 |
| T16 | Defect correction and refinement | 3 | 2 | 6 | 1,176,000 |
| T17 | Final documentation and demo | 4 | 3 | 12 | 2,352,000 |
|  | **Labour total** |  |  | **120** | **23,520,000** |
|  | Overhead (fixed) |  |  |  | 150,000 |
|  | **Total ABC estimate** |  |  |  | **23,670,000** |

**Findings:**

- 120 person-weeks is about 27.7 person-months, which agrees with the function-point effort (25.9) and the planned team effort (28.6).
- The most expensive activities are integration, testing and final documentation (PKR 2.35 million each), then the risk module (PKR 1.96 million). These are the first places to look for process improvement, for example automated tests and early documentation.

---

## 1.5 Task Dependency Table

The table was prepared in the way described in the guidelines: first list all tasks, then find which task must come first, then decide which tasks can run in parallel, then repeat until every task is placed.

| Task | Description | Duration (weeks) | Immediate predecessors |
| --- | --- | --: | --- |
| T1 | Problem analysis and objectives | 2 | None |
| T2 | Feasibility study and scope definition | 2 | T1 |
| T3 | Domain review: aviation risk, NOTAM, trajectories | 3 | T1 |
| T4 | Collect and inspect datasets | 3 | T1 |
| T5 | Requirements, use cases, vision document, risk list | 3 | T2, T3 |
| T6 | System architecture and database design | 3 | T5 |
| T7 | Prepare and validate historical datasets | 4 | T4 |
| T8 | Module 1: flight and 4D trajectory | 4 | T6 |
| T9 | Module 2: multi-hazard risk assessment | 5 | T6, T7 |
| T10 | NOTAM model (DistilBERT) fine-tuning and integration | 5 | T5, T7 |
| T11 | Module 3: recovery route generation | 4 | T8, T9 |
| T12 | Modules 4 and 5: OFP, SHA-256 audit, RBAC | 4 | T6 |
| T13 | React frontend and dashboards | 6 | T5, T6 |
| T14 | Integration of frontend and backend | 3 | T10, T11, T12, T13 |
| T15 | Functional, model and data-validation testing | 3 | T14 |
| T16 | Defect correction and usability refinement | 2 | T15 |
| T17 | Final documentation and demonstration | 3 | T16 |

**Which tasks can run in parallel:**

- After T1: T2, T3 and T4.
- After T6: T8, T9, T12 and T13.
- T7 (data preparation) runs next to T5 and T6.
- T10 (NOTAM model) can run next to T8, T9 and T13.

---

## 1.6 Critical Path Method (CPM)

CPM finds the longest chain of dependent tasks. These tasks decide the shortest time in which the project can finish. It shows which tasks are critical and which have spare time.

### 1.6.1 Steps Followed

1. Specify the activities (T1–T17, from the work breakdown).
2. Determine the sequence (immediate predecessors, Section 1.5).
3. Draw the network diagram (activity-on-node).
4. Estimate the time of each activity (one fixed value in weeks).
5. Identify the critical path (longest path, zero slack).
6. Update the diagram as the project progresses.

### 1.6.2 Network Diagram (Activity-on-Node)

Each arrow means "must finish before". Numbers in brackets are durations in weeks.

```
START ──> T1(2)
T1(2)           ──> T2(2), T3(3), T4(3)
T2(2), T3(3)    ──> T5(3)
T4(3)           ──> T7(4)
T5(3)           ──> T6(3), T10(5), T13(6)
T7(4)           ──> T9(5), T10(5)
T6(3)           ──> T8(4), T9(5), T12(4), T13(6)
T8(4), T9(5)    ──> T11(4)
T10(5), T11(4), T12(4), T13(6) ──> T14(3)
T14(3) ──> T15(3) ──> T16(2) ──> T17(3) ──> END

CRITICAL PATH:
T1 → T3 → T5 → T6 → T9 → T11 → T14 → T15 → T16 → T17
```

### 1.6.3 Formulas Used

```
ES(K) = max [ EF(J) : J is a predecessor of K ]
EF(K) = ES(K) + Dur(K)
LF(K) = min [ LS(J) : J is a successor of K ]
LS(K) = LF(K) – Dur(K)
TS(K) = LS(K) – ES(K)                 (total slack)
FS(K) = min [ ES(J) : J is a successor of K ] – EF(K)   (free slack)
```

**Worked example for T9 (risk module):** predecessors T6 (EF = 11) and T7 (EF = 9), so ES = max(11, 9) = 11; EF = 11 + 5 = 16. Its only successor is T11, whose LS is 16, so LF = 16 and LS = 16 – 5 = 11. Total slack = 11 – 11 = 0, so T9 is critical.

### 1.6.4 CPM Table

| Task | Duration | ES | EF | LS | LF | TS | FS | Critical? |
| --- | --: | --: | --: | --: | --: | --: | --: | --- |
| T1 | 2 | 0 | 2 | 0 | 2 | 0 | 0 | **Yes** |
| T2 | 2 | 2 | 4 | 3 | 5 | 1 | 1 | No |
| T3 | 3 | 2 | 5 | 2 | 5 | 0 | 0 | **Yes** |
| T4 | 3 | 2 | 5 | 4 | 7 | 2 | 0 | No |
| T5 | 3 | 5 | 8 | 5 | 8 | 0 | 0 | **Yes** |
| T6 | 3 | 8 | 11 | 8 | 11 | 0 | 0 | **Yes** |
| T7 | 4 | 5 | 9 | 7 | 11 | 2 | 0 | No |
| T8 | 4 | 11 | 15 | 12 | 16 | 1 | 1 | No |
| T9 | 5 | 11 | 16 | 11 | 16 | 0 | 0 | **Yes** |
| T10 | 5 | 9 | 14 | 15 | 20 | 6 | 6 | No |
| T11 | 4 | 16 | 20 | 16 | 20 | 0 | 0 | **Yes** |
| T12 | 4 | 11 | 15 | 16 | 20 | 5 | 5 | No |
| T13 | 6 | 11 | 17 | 14 | 20 | 3 | 3 | No |
| T14 | 3 | 20 | 23 | 20 | 23 | 0 | 0 | **Yes** |
| T15 | 3 | 23 | 26 | 23 | 26 | 0 | 0 | **Yes** |
| T16 | 2 | 26 | 28 | 26 | 28 | 0 | 0 | **Yes** |
| T17 | 3 | 28 | 31 | 28 | 31 | 0 | 0 | **Yes** |

### 1.6.5 All Main Paths Through the Network

| Path | Tasks | Total weeks |
| --- | --- | --: |
| **P1 (critical)** | T1–T3–T5–T6–T9–T11–T14–T15–T16–T17 | **31** |
| P2 | T1–T2–T5–T6–T9–T11–T14–T15–T16–T17 | 30 |
| P3 | T1–T3–T5–T6–T8–T11–T14–T15–T16–T17 | 30 |
| P4 | T1–T4–T7–T9–T11–T14–T15–T16–T17 | 29 |
| P5 | T1–T3–T5–T6–T13–T14–T15–T16–T17 | 28 |
| P6 | T1–T3–T5–T6–T12–T14–T15–T16–T17 | 26 |
| P7 | T1–T4–T7–T10–T14–T15–T16–T17 | 25 |
| P8 | T1–T3–T5–T10–T14–T15–T16–T17 | 24 |

### 1.6.6 Results and Meaning

- **Critical path:** T1, T3, T5, T6, T9, T11, T14, T15, T16, T17. **Minimum project duration: 31 weeks.**
- Any delay in a critical task delays the whole project. To finish earlier, the critical tasks must be shortened.
- **Most flexible tasks:** T10 (NOTAM model, 6 weeks of slack) and T12 (OFP, audit, RBAC, 5 weeks of slack). T13 (frontend) has 3 weeks of slack.
- **Near-critical tasks:** T2 and T8 have only 1 week of slack, and path P2/P3 is just 1 week shorter than the critical path. They need close monitoring.
- The diagram must be updated when real durations are known, because a different critical path can appear.

---

## 1.7 Gantt Chart

The schedule below uses the **early-start** logic: each task starts as early as possible without breaking a dependency. ■ = task is being worked on, □ = slack (task may be delayed here without moving the end date). Time is shown in four-week blocks, and exact start and end weeks are given in the table.

| Task | Activity | Start wk | End wk | Depends on | Responsible | W1–4 | W5–8 | W9–12 | W13–16 | W17–20 | W21–24 | W25–28 | W29–31 |
| --- | --- | --: | --: | --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| T1 | Problem analysis | 1 | 2 | – | M1, M4 | ■ |  |  |  |  |  |  |  |
| T2 | Feasibility and scope | 3 | 4 | T1 | M1 | ■ | □ |  |  |  |  |  |  |
| T3 | Domain review | 3 | 5 | T1 | M1, M4 | ■ | ■ |  |  |  |  |  |  |
| T4 | Data collection | 3 | 5 | T1 | M4, M2 | ■ | ■ |  |  |  |  |  |  |
| T5 | Requirements, vision | 6 | 8 | T2, T3 | M1, M2, M3 |  | ■ |  |  |  |  |  |  |
| T6 | Architecture, database | 9 | 11 | T5 | M2, M4 |  |  | ■ |  |  |  |  |  |
| T7 | Data preparation | 6 | 9 | T4 | M4, M2 |  | ■ | ■ |  |  |  |  |  |
| T8 | Module 1: trajectory | 12 | 15 | T6 | M2 |  |  | ■ | ■ |  |  |  |  |
| T9 | Module 2: risk | 12 | 16 | T6, T7 | M4, M2 |  |  | ■ | ■ |  |  |  |  |
| T10 | NOTAM model | 10 | 14 | T5, T7 | M4 |  |  | ■ | ■ | □ |  |  |  |
| T11 | Module 3: recovery | 17 | 20 | T8, T9 | M2, M4 |  |  |  |  | ■ |  |  |  |
| T12 | Modules 4, 5: OFP, audit, RBAC | 12 | 15 | T6 | M2 |  |  | ■ | ■ | □ |  |  |  |
| T13 | React frontend | 12 | 17 | T5, T6 | M3 |  |  | ■ | ■ | ■ |  |  |  |
| T14 | Integration | 21 | 23 | T10–T13 | M1–M4 |  |  |  |  |  | ■ |  |  |
| T15 | Testing and validation | 24 | 26 | T14 | M1–M4 |  |  |  |  |  | ■ | ■ |  |
| T16 | Defect correction | 27 | 28 | T15 | M2, M3, M4 |  |  |  |  |  |  | ■ |  |
| T17 | Documentation, demo | 29 | 31 | T16 | M1–M4 |  |  |  |  |  |  |  | ■ |

**Resource note.** Weeks 12–16 are the busiest (T8, T9, T10, T12 and T13 overlap). Tasks with slack (T10 and T12) should use late-start logic, so that M2 and M4 are not overloaded. Critical tasks T9 and T11 are never delayed for this reason.

### 1.7.1 Milestones and Achievement Criteria

| Milestone | Week | Achievement criteria |
| --- | --: | --- |
| MS1: Foundation ready | 5 | Feasibility and scope approved by supervisor; domain review and datasets collected |
| MS2: Requirements approved | 8 | Requirements, use cases, vision document and risk list approved |
| MS3: Data ready | 9 | Datasets cleaned, validated and documented |
| MS4: Design complete | 11 | Architecture and database schema approved |
| MS5: Core backend modules | 16 | Trajectory and risk modules run with test data and pass unit tests |
| MS6: All modules built | 20 | Recovery, OFP, audit, RBAC, NOTAM model and frontend finished separately |
| MS7: Integrated prototype | 23 | Full flow works: flight → risk → recovery → approval → OFP → audit |
| MS8: Testing complete | 26 | Test cases executed; model and data validation reports written |
| MS9: Refinement complete | 28 | All high-priority defects closed |
| MS10: Final delivery | 31 | Final report and demonstration approved |

---

## 1.8 Introduction to Team Members and Their Skill Set

*Note: replace the name fields below with the real names and registration numbers of the group members. The roles and skills are matched to the tasks in Section 1.9. The supervisor name should also be added here.*

| Member | Name | Role | Skill set | Main tasks |
| --- | --- | --- | --- | --- |
| M1 | \[Name, Reg. No.\] | Project Coordinator and Requirements Analyst | Requirements engineering, project planning, technical writing, aviation domain study, presentation, basic testing | T1, T2, T3, T5, documentation, test planning |
| M2 | \[Name, Reg. No.\] | Backend and Database Developer | Python, FastAPI, REST API design, SQL and PostgreSQL, SQLAlchemy, Pydantic validation, backend testing | T4 to T9, T11, T12 |
| M3 | \[Name, Reg. No.\] | Frontend and Visualisation Developer | React, JavaScript, Vite, CSS design system, SVG visualisation, API integration, user-interface design | T5, T13, interface parts of T14 to T16 |
| M4 | \[Name, Reg. No.\] | Machine Learning and Data Analyst | Python data processing (Pandas, NumPy), NLP, HuggingFace Transformers, PyTorch, dataset validation, statistics | T1, T3, T4, T6, T7, T9, T10, T11 |

If the project is completed by fewer members, one person takes several roles, and the schedule must then be stretched or lower-priority features must be removed.

---

## 1.9 Task and Member Assignment Table

The table shows who is responsible for each task and who helps. The last column shows the person-weeks each task needs (it matches the ABC table in Section 1.4.4).

| Task | Description | Primary (lead) | Supporting | Person-weeks |
| --- | --- | --- | --- | --: |
| T1 | Problem analysis and objectives | M1 | M4 | 4 |
| T2 | Feasibility and scope | M1 | – | 2 |
| T3 | Domain review | M1 | M4 | 6 |
| T4 | Data collection | M4 | M2 | 6 |
| T5 | Requirements, use cases, vision, risk list | M1 | M2, M3 | 9 |
| T6 | Architecture and database design | M2 | M4 | 6 |
| T7 | Data preparation and validation | M4 | M2 | 8 |
| T8 | Module 1: 4D trajectory | M2 | – | 4 |
| T9 | Module 2: multi-hazard risk | M4 | M2 | 10 |
| T10 | NOTAM model integration | M4 | – | 5 |
| T11 | Module 3: recovery routes | M2 | M4 | 8 |
| T12 | Modules 4 and 5: OFP, audit, RBAC | M2 | – | 4 |
| T13 | React frontend and dashboards | M3 | – | 6 |
| T14 | Integration | M2 | M1, M3, M4 | 12 |
| T15 | Testing and validation | M1 | M2, M3, M4 | 12 |
| T16 | Defect correction | M2 | M3, M4 | 6 |
| T17 | Final documentation and demonstration | M1 | M2, M3, M4 | 12 |

### 1.9.1 Workload per Member

| Member | Tasks | Person-weeks | Share of total (120) |
| --- | --- | --: | --: |
| M1 | T1, T2, T3, T5, T14, T15, T17 | 19 | 16% |
| M2 | T4, T5, T6, T7, T8, T9, T11, T12, T14, T15, T16, T17 | 41 | 34% |
| M3 | T5, T13, T14, T15, T16, T17 | 20 | 17% |
| M4 | T1, T3, T4, T6, T7, T9, T10, T11, T14, T15, T16, T17 | 40 | 33% |
| **Total** |  | **120** | **100%** |

**Balance check:** M2 and M4 carry about two-thirds of the work. To reduce this, M3 can help with the approval and audit screens of T12 and the recovery screens of T11, and M1 can write test cases and take more documentation work. This keeps the critical-path tasks (T9 and T11) protected.

---

## 1.10 Tools and Technology with Reasoning

### 1.10.1 Needs and Constraints (Checklist from the Guidelines)

| Question | Answer for SkyRisk Auditor |
| --- | --- |
| Development process | Iterative, module by module. Tests must be repeated often, so automated checks (linting, API tests) are used. |
| Host (development) platform | Windows laptops/PCs with VS Code, Python virtual environment and Node.js. |
| Target platform | Any modern web browser; server with Python and PostgreSQL (SQLite as fallback). |
| Programming languages | Python (backend, data, ML), JavaScript/JSX (frontend), SQL, CSS. |
| Existing tools reviewed | React, FastAPI, PostgreSQL, HuggingFace and PyTorch are proven and already known by the team, so they are reused. |
| Distribution of team | Team works from the same university and shares one Git repository. |
| Size of development effort | Medium: about 21.8 KLOC and 259 function points. |
| Budget and time | Very small cash budget; 31 weeks. Therefore free and open-source tools are chosen. |

### 1.10.2 Frontend

| Tool | Reason for selection | Alternative rejected |
| --- | --- | --- |
| **React 19** | Component-based. Cards, forms, risk panels and route comparisons are reused across screens. Handles complex state (selected flight, risk result, recovery plan). | Plain HTML/jQuery becomes hard to manage for complex 4D state. |
| **Vite** | Very fast start-up and live reload; light production build. Useful for frequent interface testing. | Next.js adds server-rendering that an operations dashboard does not need. |
| **CSS design tokens (vanilla CSS)** | One consistent dark aeronautical theme; full control over radar animations. | TailwindCSS adds many utility classes that clutter detailed SVG templates. |
| **SVG canvas for 4D radar and altitude profile** | Sharp at any screen size, light, and safe on laptops without a strong graphics card. | WebGL/Three.js can lose context and needs heavy assets. |
| **ESLint and npm** | Code-quality checks and dependency management. | – |

### 1.10.3 Backend

| Tool | Reason for selection | Alternative rejected |
| --- | --- | --- |
| **Python** | Strong support for web services, data processing and machine learning in one language. The risk engine and NOTAM model share the same environment. | Using two languages would complicate integration. |
| **FastAPI** | Fast, asynchronous REST API, automatic interactive documentation, and easy binding to Python ML code. | Django is heavy for this need; Flask has no built-in typed validation. |
| **Pydantic** | Validates inputs (callsign, airports, altitude, speed, NOTAM text, approval note) before they enter the system. | Manual validation is error-prone. |
| **SQLAlchemy** | One layer to work with all tables (flights, hazards, assessments, plans, OFPs, users, audit). | Raw SQL everywhere reduces maintainability. |
| **Uvicorn** | Server that runs the FastAPI application. | – |

### 1.10.4 Database

| Tool | Reason for selection | Alternative rejected |
| --- | --- | --- |
| **PostgreSQL** | Reliable transactions, integrity rules, indexing for many 4D coordinate rows, and several users working together. | Flat JSON/CSV files have no relational rules or safe concurrent writes. |
| **SQLite (automatic fallback)** | If the PostgreSQL service is not running, the system switches to SQLite and continues. This protects live demonstrations. | A hard failure would stop the demonstration. |

### 1.10.5 Machine Learning and Data

| Tool | Reason for selection | Alternative rejected |
| --- | --- | --- |
| **DistilBERT** | About 66 million parameters; smaller and faster than full BERT while keeping most of its language understanding. Runs on CPU in about 40 ms. | Cloud LLM APIs cost money, need internet, are slower, and send operational text outside the organisation. |
| **PyTorch and HuggingFace Transformers** | Standard tools to load the model, tokenise text and run inference. | – |
| **Pandas, NumPy, GeoPy** | Clean and join CSV data, compute indicators and distances, and write validation reports. | – |
| **Pareto multi-objective route logic** | Balances delay, fuel and risk together, and also uses vertical step-climbs. | Plain Dijkstra on a fixed airway grid only looks at distance and cannot balance weather and fuel. |

### 1.10.6 Security and Audit

| Tool | Reason for selection | Alternative rejected |
| --- | --- | --- |
| **SHA-256 hash chaining** | Every audit event includes the hash of the previous one. If someone changes an old record, the chain breaks and the change is detected. Fast and needs no outside service. | A public blockchain brings fees, slow confirmation and third-party dependence. |
| **Role-Based Access Control** | Separates duties (only the Dispatcher can approve; the Auditor can verify). | One shared role would remove accountability. |

### 1.10.7 Development and Testing Tools

- VS Code (editor), Git (version control), Python virtual environment, Node.js and npm.
- Interactive API documentation generated by FastAPI for endpoint testing.
- Manual functional testing with the demonstration scenario; CSV/JSON validation reports for data and model checks.

### 1.10.8 Summary of Technology Choices

| Layer | Technology |
| --- | --- |
| Frontend | React 19, Vite, CSS design tokens, SVG visualisation |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL with SQLite fallback |
| Machine learning | DistilBERT, PyTorch, HuggingFace Transformers |
| Data processing | Pandas, NumPy, GeoPy |
| Integrity and access | SHA-256 hash chain, RBAC |
| Tools | VS Code, Git, npm, ESLint, virtual environment |

---

## 1.11 Vision Document

The Vision Document gives the stakeholders' view of the product. It explains the "why" and the "what" and is the base for the detailed requirements. It can change slowly as understanding grows.

### 1.11.1 Purpose

To give everyone (team, supervisor, examiners, future users) one clear picture of what SkyRisk Auditor must do, for whom, and within which limits.

### 1.11.2 Problem Statement and the "Problem Behind the Problem"

| Item | Description |
| --- | --- |
| **The visible problem** | Dispatchers must check weather, space weather, NOTAMs, trajectories and traffic in separate tools, then choose a new route by hand. |
| **Who is affected** | Dispatchers, safety analysts, auditors, meteorologists, airlines and passengers. |
| **Effect** | Slow decisions, missed hazards, extra fuel and delay, and weak records of why a decision was made. |
| **Problem behind the problem** | The real gap is not missing data. It is that the data is not joined, not explained in one risk number, and not recorded in a way that can be checked later. |
| **Benefit of a solution** | One 4D view, one explainable score, comparable recovery options, human approval and a tamper-evident record. |

### 1.11.3 Product Position

For flight dispatchers and aviation safety staff who must make quick, safe route decisions, SkyRisk Auditor is a web-based 4D decision-support system that combines multiple hazards into one risk score and proposes recovery routes. Unlike separate weather, NOTAM and radar tools, it keeps one view, uses a local NOTAM model, and records every decision in a hash-chained audit trail.

### 1.11.4 Stakeholders and Their Needs

| Stakeholder | Key need |
| --- | --- |
| Flight Dispatcher | Fast risk view, route options, and a clear approval step |
| Aviation Safety Analyst | Explanation of which hazards raise the score and how they combine |
| Aviation Security Auditor | Proof that records are not changed after the fact |
| Meteorological Analyst | Access to weather, space-weather and NOTAM results |
| Project team | A feasible scope and a working demonstration |
| Supervisor and examiners | Technical depth, correct engineering process, clear limits |
| Airline management (indirect) | Lower delay and fuel cost, better accountability |
| Aviation authority (external) | Systems that do not weaken safety rules |

### 1.11.5 System Boundary and Actors

- **Inside the boundary:** the five backend modules, the React dashboard, the database, the local NOTAM model and the historical datasets.
- **Outside the boundary:** external data providers (OpenSky, NOAA, Open-Meteo/AWC, NOTAM sources), the aircraft, air traffic control, and official dispatch systems.
- **Actors:** Flight Dispatcher, Aviation Safety Analyst, Aviation Security Auditor, Meteorological Analyst (human); external data feeds (system actors).

### 1.11.6 Key Needs and Features

| Need | Feature that answers it |
| --- | --- |
| See where each flight will be in space and time | 4D trajectory engine and radar view |
| Know the combined danger | Multi-hazard score from 0 to 100 with cascading multiplier |
| Understand coded NOTAMs | DistilBERT NOTAM classifier |
| Choose a safer route quickly | Four recovery candidates with delay, fuel and risk |
| Keep human control | Role-restricted approval with a note and signature |
| Release a formal plan | OFP generation after approval |
| Prove nothing was changed | SHA-256 audit chain with verification |
| Control who may do what | RBAC with four roles |

### 1.11.7 Constraints

| Type | Constraint |
| --- | --- |
| Technical | CPU-only machines; free tools; live feeds may fail, so fallback data is needed |
| Economic | Very small cash budget; free and open-source software |
| Time | 31 weeks within the academic year |
| Political and regulatory | Aviation is strictly regulated. The system must not claim certification, and airspace and military-activity data are sensitive |
| Environmental | The system should support fuel-efficient route choices (less fuel burned means lower emissions); the local model avoids heavy cloud computing |
| Data | Public data only; coverage mainly the Pakistan region; known grid and resolution limits |
| Ethical and legal | Human decision authority, data-licence compliance, honest statement of limits |

### 1.11.8 Alternatives Considered

| Alternative | Why not chosen |
| --- | --- |
| Keep manual process (do nothing) | Does not solve the problem; the main reason for this project |
| Cloud LLM for NOTAMs | Cost, internet dependence, delay, data-privacy concern |
| Shortest-path route search only | Cannot balance delay, fuel and risk or use vertical options |
| Public blockchain for audit | Fees, delay, external dependence |
| Flat files for storage | No integrity rules or safe concurrent use |

### 1.11.9 Risks and Budget

- The main risks are listed in Section 1.12.
- **Budget for the detailed planning phase (T1 to T6):** 33 person-weeks, which is about PKR 6.47 million as a commercial equivalent (PKR 196,000 per person-week). The real cash cost for the university project is small.

### 1.11.10 Vision Checkpoints

| Checkpoint | Answer |
| --- | --- |
| Is the "problem behind the problem" explored? | Yes, see 1.11.2: the gap is joined, explainable and auditable decision support. |
| Is the problem statement correct? | Yes, it is based on the real dispatcher workflow. |
| Is the stakeholder list complete? | Yes, see 1.11.4 (users, team, supervisor, airline, authority). |
| Is the system boundary agreed? | Yes, see 1.3 and 1.11.5. |
| Are all actors defined? | Yes, four human actors and external data feeds. |
| Are constraints explored? | Yes, see 1.11.7. |
| Are political, economic and environmental constraints covered? | Yes, all three are listed. |
| Are all key features identified? | Yes, see 1.11.6 and 1.13. |
| Do the features solve the identified problems? | Yes, each need is linked to a feature. |
| Are the features consistent with the constraints? | Yes. Human approval, fallback data and free tools respect the constraints. |

---

## 1.12 Risk List

The list is sorted from highest to lowest priority. **Score = Probability × Impact**, where High = 3, Medium = 2, Low = 1. The list is created at the start and reviewed at the end of every iteration. New risks are added and solved risks are closed.

| ID | Risk | Prob. | Impact | Score | Mitigation (prevent) | Contingency (if it happens) | Owner |
| --- | --- | :-: | :-: | :-: | --- | --- | --- |
| R1 | Live data feeds (ADS-B, weather, NOAA, NOTAM) are unavailable, limited or incomplete | H | H | 9 | Keep saved fallback datasets; store raw feed copies | Switch to archived data and mark results as "fallback data" | M4 |
| R2 | NOTAM model misclassifies text or has too little training data | M | H | 6 | Show confidence value; test with a labelled NOTAM suite; keep a human check | Retrain with more samples; use keyword rules as a backup | M4 |
| R3 | Recovery routes are wrongly seen as certified or safe | M | H | 6 | Clear disclaimers; compulsory human approval; label routes as candidates | Remove claims from the interface and documents; add expert review | M1 |
| R4 | Delay in a critical-path task (T9, T11) delays the project | M | H | 6 | Weekly progress check; protect critical tasks; watch near-critical T2 and T8 | Use the slack of T10 and T12; cut optional features | M1 |
| R5 | M2 and M4 are overloaded (about two-thirds of the work) | H | M | 6 | Move support tasks to M1 and M3; use late-start for tasks with slack | Reduce scope of low-priority features | M1 |
| R6 | Scope creep (extra modules and ideas added) | H | M | 6 | Use priority, effort and risk to accept features; recount function points after design | Freeze features after MS6 | M1 |
| R7 | Weather and trajectory data do not match well (grid resolution, global Kp) | H | M | 6 | Document the limits; treat output as research indicators | Use a finer weather source when available | M4 |
| R8 | Integration problems between backend, model and frontend | M | M | 4 | Fixed API contract; test each module alone; early integration | Add extra integration time from slack | M2 |
| R9 | Prototype authentication is weak | M | M | 4 | Role checks on approval; state limits clearly | Add stronger password handling and tokens as future work | M2 |
| R10 | Loss of code or data (hardware failure) | L | H | 3 | Git repository and regular backups | Restore from the latest backup | All |
| R11 | PostgreSQL service fails during a demonstration | L | H | 3 | Automatic SQLite fallback; test before demo | Run demonstration on SQLite | M2 |
| R12 | Data licence or privacy issue | L | M | 2 | Use public sources and credit them; no personal data stored | Remove the affected dataset | M1 |
| R13 | Slow performance on the examiner's computer | L | M | 2 | CPU-only model; light SVG graphics; rehearsal on a normal laptop | Use a recorded demonstration as backup | M3 |

---

## 1.13 Product Features / Product Decomposition

Functional requirements describe what the system must do. They are shown here as a breakdown from product to modules to features. Priority: H = high, M = medium, L = low.

### 1.13.1 Decomposition Tree

```
SkyRisk Auditor
├── Module 1: Flight and 4D Trajectory
├── Module 2: Multi-Hazard Risk Assessment
│     └── NOTAM Classification (DistilBERT)
├── Module 3: Recovery Decision Support
├── Module 4: OFP and Audit
├── Module 5: Authentication and RBAC
├── Web Dashboard (React)
└── Data and Infrastructure
```

### 1.13.2 Module 1: Flight and 4D Trajectory

| ID | Feature | Description | Priority |
| --- | --- | --- | :-: |
| F1.1 | Flight plan entry | Create and read flights with validated callsign, airports, cruise altitude and speed | H |
| F1.2 | 4D waypoint generation | Store latitude, longitude, altitude, speed, heading and time offset for each waypoint | H |
| F1.3 | Flight profile | Climb, cruise and descent profile with wind effect on ground speed | M |
| F1.4 | Trajectory retrieval | Return the full 4D path of a flight | H |
| F1.5 | Flight status | Operational status and monitoring state of each flight | M |

### 1.13.3 Module 2: Multi-Hazard Risk Assessment

| ID | Feature | Description | Priority |
| --- | --- | --- | :-: |
| F2.1 | Hazard register | Store convective weather, space weather, NOTAM and airspace hazards | H |
| F2.2 | 4D hazard check | Test distance, altitude overlap and the hazard's active time window against the trajectory | H |
| F2.3 | Individual scores | Score each hazard type separately | H |
| F2.4 | Combined risk score | Weighted score from 0 to 100 with a cascading multiplier (1.0 to 1.45) when hazards overlap | H |
| F2.5 | NOTAM classification | Local DistilBERT model returns the risk class and confidence | H |
| F2.6 | NOTAM coordinate parsing | Convert coordinate codes into decimal latitude and longitude | M |
| F2.7 | Separation conflict detection | Find flights that may lose safe separation | M |
| F2.8 | On-demand airspace scan | Scan all active flights and list high-risk ones | M |

### 1.13.4 Module 3: Recovery Decision Support

| ID | Feature | Description | Priority |
| --- | --- | --- | :-: |
| F3.1 | Trigger | Start recovery planning when the risk score is above the limit (40) | H |
| F3.2 | Four candidate routes | Minimum delay, minimum fuel, safest buffer, balanced | H |
| F3.3 | Trade-off comparison | Show delay, fuel, distance, residual risk and risk reduction side by side | H |
| F3.4 | Balanced recommendation | Pareto-based pick that balances delay, fuel and risk | M |
| F3.5 | Approve or reject | Dispatcher approves with a note and signature, or rejects | H |

### 1.13.5 Module 4: OFP and Audit

| ID | Feature | Description | Priority |
| --- | --- | --- | :-: |
| F4.1 | OFP generation | Create the Operational Flight Plan after route approval | H |
| F4.2 | Audit events | Record actor, role, action, entity, previous state, new state and time | H |
| F4.3 | Hash chain | Link each event to the previous one using SHA-256 | H |
| F4.4 | Integrity verification | Check the whole chain and report any break | H |

### 1.13.6 Module 5: Authentication and RBAC

| ID | Feature | Description | Priority |
| --- | --- | --- | :-: |
| F5.1 | Four roles | Dispatcher, Safety Analyst, Security Auditor, Meteorological Analyst | H |
| F5.2 | Capability matrix | Defines who can view, approve, generate OFP and verify audit | H |
| F5.3 | Approval enforcement | Only the Dispatcher can approve; others see a read-only warning | H |
| F5.4 | User and role directory | View users and update role capabilities (prototype level) | L |

### 1.13.7 Web Dashboard (React)

| ID | Feature | Description | Priority |
| --- | --- | --- | :-: |
| F6.1 | Overview dashboard | Active flights, hazards, high-risk flights, conflicts | H |
| F6.2 | Flight operations | Flight list, waypoint ledger, new flight entry, instant scan | H |
| F6.3 | 4D radar and altitude profile | Horizontal radar view plus vertical cross-section with a time slider | H |
| F6.4 | Risk assessment screen | Score breakdown, cascading effect, NOTAM classifier playground | H |
| F6.5 | Recovery planning screen | Route cards and approval dialog | H |
| F6.6 | Approvals and audit screen | Audit ledger and integrity check | H |
| F6.7 | Data sources screen | Status of database, model and external feeds | M |
| F6.8 | Users, roles and settings | Role view and system settings | L |

### 1.13.8 Data and Infrastructure

| ID | Feature | Description | Priority |
| --- | --- | --- | :-: |
| F7.1 | Data ingestion with fallback | Use live feeds when available, saved datasets when not | H |
| F7.2 | Database switching | PostgreSQL first, automatic SQLite fallback | H |
| F7.3 | Validation reports | CSV/JSON reports on data quality and recovery-route evaluation | M |

### 1.13.9 Main Quality Requirements

| Quality | Requirement |
| --- | --- |
| Performance | NOTAM classification in about 40 ms on CPU; smooth radar drawing |
| Reliability | Automatic database fallback; fallback datasets for data feeds |
| Security and integrity | Role checks on approval; SHA-256 chain for audit records |
| Usability | Colour-coded risk levels; side-by-side route comparison |
| Maintainability | Five separate modules; typed and validated API |
| Privacy | NOTAM text processed locally, no personal data exposed |

---

## 1.14 Chapter Summary

- SkyRisk Auditor is a 4D flight-risk assessment and recovery decision-support system that brings trajectory, weather, space weather, NOTAM and conflict information into one place.
- The feasibility study found the project feasible in all eight areas as an academic prototype, with its limits clearly stated.
- Scope was defined with inside, outside and context, and managed through priority, effort and risk.
- Estimates: 21.8 KLOC; 258.64 function points (about 25.9 person-months); COCOMO'81 effort of 94.7 (basic) and 120.9 (intermediate) person-months; ABC estimate of 120 person-weeks.
- The project plan has 17 tasks, a critical path of 31 weeks (T1, T3, T5, T6, T9, T11, T14, T15, T16, T17), a Gantt chart with ten milestones, a four-member team and a workload table.
- The tools were chosen with reasons, the vision document and risk list were prepared, and the product was broken down into features.
- The next chapter can describe the existing system in more detail, review related work and set the requirements and design base.
