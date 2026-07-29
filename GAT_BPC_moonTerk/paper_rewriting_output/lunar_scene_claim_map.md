# Lunar-Scene Claim Map for Sections 1--4

## Purpose

This internal map controls the lunar-scene revision of the English working
draft. It is not part of the manuscript. Its function is to keep every
application statement within either an external citation boundary or a frozen
project-evidence boundary.

## Scene Claims and Boundaries

| ID | Manuscript claim | Evidence anchor | Permitted wording | Prohibited extension |
|---|---|---|---|---|
| LS01 | South-pole water-ice prospecting requires coordinated movement between candidate sites under terrain, illumination, power, thermal and communication considerations | C041, C042, C054, C055 | Present these factors as mission-planning context | Imply that the current optimization model explicitly represents every factor, especially communication or fully time-varying illumination |
| LS02 | Permanently shadowed regions are high-priority cold-trap environments for water-ice prospecting, while thermally stable candidate areas are not restricted to a claim that all lunar water ice occurs only inside such regions | C042, C054; NASA lunar-water and LRO context checked on 2026-07-24 | Describe PSR interiors, rims and nearby transition areas as scientifically important candidate zones | State that all lunar water ice exists only in PSRs or that project proxies establish ground-truth abundance |
| LS03 | The benchmark represents a wide regional survey on one 50 km by 50 km real-map base area | README.md lines 147--155; `domain/scenario.py`; EV010--EV011 | State explicitly that 50 km by 50 km is a forward-looking benchmark scenario and a fixed spatial extent | Present the extent as a demonstrated mission capability or infer field performance |
| LS04 | The benchmark assumes higher-mobility future rovers through configured speed and horizon parameters | `domain/scenario.py`; `domain/real_maps.py::_path_metrics` | Call these values scenario parameters used to study a future operational regime | Claim that present flight-qualified rovers can achieve the configured speed or that the speed model is physically calibrated |
| LS05 | Tasks represent in-situ prospecting operations at candidate locations, and path options encode different time, energy and risk priorities | README.md line 153; EV009--EV011 | Explain detect, sample and drill as task modes and the three predeclared path options as planning alternatives | Claim that task-site resource abundance has been validated in situ or that the optimizer searches all continuous lunar trajectories |
| LS06 | Each trip leaves and returns to a depot, and a multi-trip route couples repeated trips through docking, recharge and mission time | EV002; manuscript Eqs. (2)--(8) | Tie the route structure to repeated deployment from a support location | Claim physical validation of the charging architecture or add an unimplemented charger-capacity constraint |
| LS07 | Shadow exposure is a cumulative trip resource that is distinct from the risk term in the objective | `columns.py`; `objective.py`; EV029 | Explain that a path may be attractive in travel time yet infeasible under the shadow limit | Treat the shadow proxy as a validated thermal-survival model or collapse it into generic distance |
| LS08 | Science-weighted completion time rewards earlier completion of higher-weight prospecting tasks | EV003; manuscript Eqs. (8)--(10) | Explain the operational role of the third objective term through earlier characterization of higher-priority sites | Use ownership, appropriation, race, "first discovered belongs to", "first-mover advantage", "land rush", or a newly coined time-sensitive problem label |
| LS09 | Exactness concerns the frozen logical graph and declared path options | EV009; CL005; Theorem 1 | Repeat the fixed logical-path solution-space qualifier near formulation and proof claims | Generalize exactness to continuous terrain, environmental truth or real mission safety |
| LS10 | Learning reorders exact pricing work and valid branch candidates but does not control cuts or proof-bearing decisions | EV001, EV004--EV008 | Present guidance as computational ordering within the lunar resource-rich pricing problem | Attribute feasibility, cut validity, bounds, pruning, pricing closure or optimality to learned scores |
| LS11 | Orbital/near-infrared observations and Chang'E-5 samples establish water-related signals and multiple host materials, but they do not by themselves determine abundance, physical occurrence or accessibility at a south-pole candidate site | C054, C061, C062; CL038 | Use the distinction between remote indications and required in-situ evidence to motivate candidate-site detection, sampling and drilling | Transfer Chang'E-5 sample quantities to the benchmark region or present a remote anomaly as an operationally characterized resource |
| LS12 | The lunar solar and seasonal illumination cycles motivate independently fixed mission epochs and a four-phase south-polar comparison, with environmental-anchor spacing distinct from the shorter routing horizon, while polar shadow still depends on topography and time of year | C063, C064; EV033; CL039; M006 | Use C063 for the full seasonal cycle and C064 for operational season-conditioned illumination; explain 12 anchors, three per phase, one-hour preprocessing over each 16–76 h window, paired-family comparison, and per-instance exactness | State that either source prescribes the four groups, routing horizon or best phase; transfer C064's study extent; claim invariant local shadow, within-solve departure-time-dependent attributes, or completed seasonal results |
| LS13 | Prospecting service does not require direct sunlight as a hard constraint; predefined task time windows provide a static representation of externally specified instrument, communication-schedule and mission-planning restrictions | EV034; CL040 | Keep communication contextual and state that it is not a separate dynamic optimization resource | Claim measured communication schedules, add an unstated communication constraint, or imply time-dependent path resources inside a solve |
| LS14 | Waiting is prohibited at candidate task sites and en route; a rover may wait only at the support depot and may adjust each trip's depot departure time to meet the selected task windows | EV035; CL041 | Explain depot timing as operational preparation at the support location and count it in elapsed mission time | Describe task-site loitering as feasible, omit depot waiting from the mission horizon, or claim that the frozen implementation already realizes the rule |

## Paragraph Allocation

| Section | Required lunar content | Main evidence |
|---|---|---|
| Abstract | Candidate-site fleet coordination; repeated depot returns; terrain-aware path alternatives; energy and shadow resources; earlier completion of higher-weight tasks | LS01, LS05--LS08 |
| Introduction | Remote-signal versus in-situ-evidence gap; spatial heterogeneity between shadowed target zones and more favorable access areas; static task-window interpretation; 50 km by 50 km future benchmark assumption; independently frozen mission epochs; mission-level routing gap; exact-safe learning boundary | LS01--LS04, LS08--LS13 |
| Related Work 2.1 | Distinguish local navigation, safe PSR access, path-network construction and fleet-level route selection; state map/proxy boundary | LS01--LS05, LS09 |
| Related Work 2.2 | Explain which terrestrial exact-routing structures transfer and which lunar resources change the pricing state | LS06--LS07, LS09 |
| Related Work 2.3 | Keep the review centered on proof-preserving guidance for the resulting resource-rich pricing and branch process | LS10 |
| Section 3 opening and 3.1 | Define the 50 km by 50 km scenario, candidate-site roles, epoch anchor and mission window, fixed path options within one solve, and immutable window-aggregated map attributes | LS02--LS05, LS09, LS12 |
| Section 3.2 | Connect trip and multi-trip route constraints to repeated deployment, shadow exposure, energy, load, recharge and mission duration | LS06--LS07 |
| Section 3.3 | Give the operational interpretation of normalized cost, risk and 0.4 times science-weighted completion time | LS08 |
| Section 4.1--4.3 | Explain why lunar path alternatives, cumulative shadow, recharge and multi-trip state make pricing the primary guidance target | LS06--LS07, LS10 |

## Language Guardrails

- Do not name the problem as a "time-sensitive resource-exploration" class.
- Do not use territorial, ownership, appropriation, race or land-rush language.
- Do not imply that all lunar water ice is confined to permanently shadowed
  regions.
- Do not present the 50 km by 50 km extent or configured rover speed as a
  current hardware fact.
- Do not use communication as an explicit mathematical constraint unless a
  corresponding variable or resource is introduced. It may remain part of the
  cited mission-planning context.
- Keep environmental fidelity, optimization exactness and algorithmic
  acceleration as three separate claim classes.
- Use “mission epoch” for the external scenario index. Do not call it a
  departure-time bucket or SPPRC state.
- Keep epoch-anchor spacing, environmental sampling resolution and routing
  mission horizon as three distinct quantities.
