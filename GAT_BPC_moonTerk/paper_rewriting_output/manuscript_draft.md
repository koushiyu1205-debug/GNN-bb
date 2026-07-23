<!--
PaperSpine manuscript draft
Current coverage: Section 3 only
Draft date: 2026-07-23
Language: English
Evidence status: mathematical formulation drafted from current project contracts and code
-->

# 3. Problem Setting and Mathematical Formulation

This section defines the transportation decisions represented by the lunar
water-ice exploration model. The formulation separates three objects that are
easy to conflate: a path option describes movement along one directed logical
edge, a sortie is a depot-to-depot task sequence, and a journey is the complete
multi-sortie schedule assigned to one rover. This separation determines both
the column structure of the master problem and the scope of the exact solution
claim.

## 3.1 Transportation network, map inputs, and fixed path-option space

Let \(\mathcal{T}\) denote the set of prospecting tasks, \(\mathcal{K}\) the
available rover set, and \(0\) the depot. The mission-level transportation
network is a directed logical graph
\(\mathcal{G}=(\mathcal{V},\mathcal{E})\), with
\(\mathcal{V}=\{0\}\cup\mathcal{T}\). A task \(i\in\mathcal{T}\) is described
by its location, operation mode, science weight \(w_i\), demand \(q_i\),
service duration \(\sigma_i\), service energy \(g_i\), service cost
\(c_i^{\mathrm{srv}}\), time window \([r_i,D_i]\), local shadow score, and
local thermal-risk attribute. These quantities are fixed instance inputs; the
optimization model neither estimates water-ice abundance nor updates the map
payload during a solve.

For each directed logical edge \((u,v)\in\mathcal{E}\), the instance declares
a finite path-option set \(\mathcal{A}_{uv}\). The current benchmark retains
three alternatives, denoted `low_time`, `low_energy`, and `low_risk`. A path
option \(a\in\mathcal{A}_{uv}\) carries travel time
\(\tau_{uv}^{a}\), energy proxy \(e_{uv}^{a}\), integrated risk
\(\rho_{uv}^{a}\), distance \(d_{uv}^{a}\), shadow exposure
\(h_{uv}^{a}\), and the associated precomputed geometry. The optimizer selects
among these declared alternatives but does not generate a new continuous
surface trajectory at run time.

The scope is therefore discrete. Define the fixed logical-path solution space
\(\Omega(\mathcal{I})\) as the set of all feasible rover journeys induced by
the frozen instance
\[
\mathcal{I}=
\bigl(
\mathcal{G},
\{\mathcal{A}_{uv}\}_{(u,v)\in\mathcal{E}},
\mathcal{T},
\mathcal{K},
\text{resource parameters},
\text{time windows},
\text{objective parameters}
\bigr).
\]
Any optimality statement in this paper is restricted to
\(\Omega(\mathcal{I})\). It does not imply optimality over arbitrary
continuous trajectories on the lunar surface, and the fidelity of the
underlying terrain, illumination, and risk layers remains separate from the
mathematical exactness of the discrete optimization procedure.

## 3.2 Tasks, sorties, and multi-sortie journeys

A sortie starts at the depot, serves an ordered sequence of distinct tasks,
and returns to the depot:
\[
s =
\bigl(
0,i_1,\ldots,i_m,0;
a_0,\ldots,a_m;
t_s^0
\bigr),
\qquad
m\leq M,
\tag{1}
\]
where \(M\) is the maximum number of tasks per sortie, \(t_s^0\) is the
departure time, and each \(a_\ell\) is a declared path option for the
corresponding directed leg. Given the sequence and path choices, timing is
constructed in execution order. If \(t_{\ell-1}^{\mathrm{cmp}}\) is the
completion time at the preceding task, the arrival, service-start, and
completion times at \(i_\ell\) are
\[
\begin{aligned}
t_{\ell}^{\mathrm{arr}}
  &= t_{\ell-1}^{\mathrm{cmp}}
     +\tau_{i_{\ell-1},i_\ell}^{a_{\ell-1}},\\
t_{\ell}^{\mathrm{start}}
  &=\max\{t_{\ell}^{\mathrm{arr}},r_{i_\ell}\},\\
t_{\ell}^{\mathrm{cmp}}
  &=t_{\ell}^{\mathrm{start}}+\sigma_{i_\ell},
\end{aligned}
\tag{2}
\]
with \(i_0=0\) and \(t_0^{\mathrm{cmp}}=t_s^0\).

The return leg determines \(t_s^{\mathrm{return}}\). Let \(E_s\), \(H_s\),
and \(Q_s\) denote, respectively, the total energy proxy, shadow exposure, and
collected load accumulated over the travel and service activities of \(s\).
The implemented recharge duration and sortie end time are
\[
t_s^{\mathrm{rch}}
  =d^{\mathrm{dock}}+\frac{E_s}{P^{\mathrm{rch}}},
\qquad
t_s^{\mathrm{end}}
  =t_s^{\mathrm{return}}+t_s^{\mathrm{rch}},
\tag{3}
\]
where \(d^{\mathrm{dock}}\) is the docking overhead and
\(P^{\mathrm{rch}}\) is the recharge-power proxy. A sortie is feasible only
if every task is completed by its due time and
\[
Q_s\leq Q,\qquad
E_s\leq B,\qquad
H_s\leq H^{\max},\qquad
t_s^{\mathrm{end}}\leq H^{\mathrm{mis}},
\tag{4}
\]
where \(Q\) is rover capacity, \(B\) is the usable-energy limit,
\(H^{\max}\) is the maximum shadow exposure per sortie, and
\(H^{\mathrm{mis}}\) is the mission horizon. Risk is accumulated in the
objective; it is not introduced here as an unrecorded feasibility threshold.

A journey \(p\) is one rover's multi-sortie schedule,
\[
p=(s_1,\ldots,s_{n_p}).
\tag{5}
\]
All sorties in \(p\) must be individually feasible and task-disjoint. They are
also time-compatible:
\(t_{s_{\ell+1}}^0\geq t_{s_\ell}^{\mathrm{end}}\), so the next sortie cannot
start before the preceding return and recharge have finished. Let
\(\mathcal{T}_p\subseteq\mathcal{T}\) be the tasks served by \(p\), and define
\(a_{ip}=1\) if \(i\in\mathcal{T}_p\), and \(0\) otherwise. One selected
journey occupies one rover; it must not be interpreted as a single sortie or
as one local path.

## 3.3 Objective function and journey master problem

Three additive quantities determine the official journey cost. For a feasible
journey \(p\), let \(C_p\) be its operating cost, formed from service cost,
travel distance, and energy proxy; let \(R_p\) be its route and service risk;
and let
\[
W_p=\sum_{i\in\mathcal{T}_p}w_i t_{ip}^{\mathrm{cmp}}
\tag{6}
\]
be its science-weighted completion term. Given the fixed positive
instance-reference values \(\widehat C\), \(\widehat R\), and
\(\widehat W\), the column cost is
\[
c_p =
\omega_C\frac{C_p}{\widehat C}
+\omega_R\frac{R_p}{\widehat R}
+\omega_W\frac{W_p}{\widehat W}.
\tag{7}
\]
The current experimental configuration uses
\(\omega_C=1\), \(\omega_R=1\), and \(\omega_W=0.4\). The normalization
references are fixed for an instance and are shared by column construction,
the master problem, pricing, and objective audits.

Makespan is deliberately excluded from (7). It is computed after journey
selection as
\[
M^{\mathrm{rep}}
=
\max_{p:\lambda_p=1}
\max_{i\in\mathcal{T}_p}
t_{ip}^{\mathrm{cmp}},
\tag{8}
\]
and is reported only as an evaluation metric. Optimizing a global makespan
would require an explicit master-level linking variable and corresponding
constraints. Adding a per-column makespan penalty to \(c_p\) would define a
different objective and would break alignment with the current exact
implementation.

Let \(\mathcal{P}\subseteq\Omega(\mathcal{I})\) be the set of all feasible
journey columns and let \(\lambda_p\) indicate whether journey \(p\) is
selected. The integer journey master problem is
\[
\begin{aligned}
\min_{\lambda}\quad
& \sum_{p\in\mathcal{P}}c_p\lambda_p \\
\text{s.t.}\quad
& \sum_{p\in\mathcal{P}}a_{ip}\lambda_p=1,
&& i\in\mathcal{T},\\
& \sum_{p\in\mathcal{P}}\lambda_p\leq |\mathcal{K}|,\\
& \sum_{p\in\mathcal{P}}a_{hp}\lambda_p\leq b_h,
&& h\in\mathcal{H},\\
& \lambda_p\in\{0,1\},
&& p\in\mathcal{P}.
\end{aligned}
\tag{9}
\]
The first constraint assigns every task exactly once, and the second limits
the number of selected journeys to the available fleet. The optional rows
\(\mathcal{H}\) represent active, deterministically generated,
pricing-compatible valid inequalities with column coefficient \(a_{hp}\) and
right-hand side \(b_h\). Their validity and lifecycle remain independent of
the learning layer described later.

Branch-Price-and-Cut solves the linear relaxation over a restricted set
\(\mathcal{P}'\subset\mathcal{P}\) and generates missing columns through
pricing. Let \(\pi_i\), \(\mu\), and \(\gamma_h\) denote the dual values of the
task-cover, fleet-limit, and active-cut rows, respectively. The reduced cost of
a feasible journey is evaluated through one shared expression:
\[
\overline c_p
=
c_p
-\sum_{i\in\mathcal{T}}\pi_i a_{ip}
-\mu
-\sum_{h\in\mathcal{H}}\gamma_h a_{hp}.
\tag{10}
\]
At a branch-tree node \(n\), the current branch context restricts the admissible
journey set to \(\mathcal{P}(n)\); it is a feasibility filter rather than an
additional dual term in (10). Equations (7), (9), and (10) are consequently
the common mathematical interface for restricted-master optimization, native
exact pricing, column admission, and reduced-cost auditing.
