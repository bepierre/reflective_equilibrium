# Reflective Equilibrium as Multi-Objective Optimization

**TL;DR.** Recast the formal model of reflective equilibrium (RE) as a multi-objective
optimization problem over two axis families — **epistemic** (Beisbart's account,
systematicity, faithfulness) and **value** (utilitarian, Kantian, virtue-ethics, care,
contractualist loadings). Each equilibrium state then has a position in a joint
objective space, and the Pareto frontier of that space is the *real* object of study.
RE is one *traversal method* among many to reach the frontier — and the empirical
question is where on the frontier it lands and how it compares to alternative traversals
(random sampling, MCMC, evolutionary methods, single-pass LLM judgment).

## Background, briefly

Beisbart, Betz, and Brun (2021) gave the first fully formal model of RE: an epistemic
state `(C, T)` (commitments + theory) is evaluated by an achievement function

```
Z(C, T | C₀) = α_a · Account(C, T) + α_s · Systematicity(T) + α_f · Faithfulness(C | C₀)
```

with three weights that sum to 1. Equilibration alternately optimizes `T` and `C` to
maximize `Z` until a fixed point is reached. Freivogel (2023) ran 65k+ simulations on
this model with random propositional sentence pools and found that RE does promote
agreement and blocks "anything goes," but stops short of unique outputs.

We have a working **LLM-based instantiation** of the Beisbart model
(`reflective_equilibrium` repo): six agents (CommitmentFormer, two inferencers, three
verifiers) running on a small ethical case set. Currently it reproduces a Rechnitzer-shaped
RE process on the five trolley cases. Three models (Gemini Flash 2, Claude 3.5 Haiku,
GPT-4o-mini) land at qualitatively different equilibria — different theories, different
faithfulness costs — already suggesting the *equilibrium position* is more interesting
than the question of *whether* equilibrium is reached.

## The reframe: RE as multi-objective optimization

Right now `Z` collapses three epistemic desiderata into one scalar via fixed weights
`(α_a, α_s, α_f)`. That's already a Pareto problem in disguise — different weight
configurations trace out the Pareto front in `(Account, Systematicity, Faithfulness)`
space. Beisbart and Freivogel both ran sensitivity analyses on the weights; neither
treated this as a Pareto question explicitly.

**Step 1 — make the epistemic Pareto frontier explicit.** Drop the weights, treat the
three desiderata as three objectives, and characterize the *front* of attainable
`(A, S, F)` triples across the space of epistemic states.

**Step 2 — add a value axis family.** Tag each candidate principle `p` with a value
loading vector `v(p) ∈ [0, 1]^K`, where `K` is a small number of ethical-framework
dimensions (e.g., the five frameworks from MoReBench-Theory: Benthamite utilitarianism,
Kantian deontology, virtue ethics, care ethics, contractualism). The tagging is **fuzzy**
— a principle like "minimize aggregate harm in cases of unavoidable loss" might have
loading `(0.7, 0.1, 0.05, 0.1, 0.05)`, not a hard one-hot.

For a theory `T = {p₁, ..., pₙ}`, the aggregate value loading is `V(T) = Σᵢ v(pᵢ) / n`
(or weighted by per-principle confidence). Now every epistemic state `(C, T)` has a
position in `ℝ³ × ℝᴷ` — three epistemic axes plus K value axes — and we have a
real multi-objective problem.

**Step 3 — characterize the frontier.** The Pareto-optimal set in this joint space is
the object of empirical study. Two questions immediately become tractable:

- **Where on the frontier does the system land?** A run that ends with `V(T) ≈
  (0.8, 0.1, 0.05, 0.05, 0)` is utilitarian-dominated; one ending at
  `(0.2, 0.6, 0.1, 0.05, 0.05)` is Kantian-dominated. The distribution of landing
  points across runs *is* the model's revealed normative profile.
- **What does the frontier look like overall?** Sample it via methods other than RE —
  multi-objective evolutionary search (NSGA-II), MCMC over commitment sets, exhaustive
  search on small instances — to characterize the frontier independently of any one
  traversal method.

## RE as one traversal method among many

Under the multi-objective framing, RE is a **search strategy** — specifically, alternating
hill-climbing under a fixed weight vector — for reaching the Pareto frontier of the joint
epistemic-value space. Other strategies we can implement and compare:

| Traversal | Mechanism | What it tells us |
|---|---|---|
| **RE (this project)** | Alternating B/A adjustments under fixed `(α_a, α_s, α_f)` | What happens when an agent equilibrates faithfully to initial intuitions |
| **Single-pass LLM judgment** | Read all dilemmas at once, output a theory + commitments | Baseline for "what does the LLM think without an iterative procedure" |
| **MCMC over (C, T)** | Metropolis-Hastings with `Z` as energy | Distribution over high-`Z` states without RE's faithfulness anchor |
| **NSGA-II** | Multi-objective evolutionary search | The actual Pareto front, independent of any single-weight scalarization |
| **Pure-account / pure-systematicity** | Maximize just one desideratum | Degenerate baselines showing what RE buys over each component alone |

The comparison answers: *does RE buy a particular kind of trajectory through the
solution space?* Does it consistently land in regions other methods miss? Does it
reach the frontier at all, or stop short?

## Research questions

1. **Algorithmic.** Does RE reach Pareto-optimal points? When it doesn't, how far off?
2. **Behavioral.** Where on the frontier does RE tend to land? Is the landing region
   stable across initial commitments, or volatile?
3. **Value bias.** Does RE produce a systematically different value-loading distribution
   than other traversal methods? In particular: does the systematicity desideratum
   bias the system toward certain ethical frameworks (e.g., utilitarianism, which
   famously systematizes well)?
4. **Trajectory.** During equilibration, how do the value loadings of the current `T`
   evolve? Are there identifiable "value conflicts" — rounds where adopting a
   utilitarian-loaded principle requires reformulating a Kantian-loaded commitment?
5. **Cross-model variance.** Do different LLMs (used as inferencer / verifier) land at
   systematically different points on the frontier? Our trolley pilot already shows
   yes — Claude Haiku gravitates toward consequentialist reformulations of IC4, Gemini
   toward a clean doing/allowing carve-out.

## Pilot — concrete and small

Use **MoReBench** (Scale Labs, 2025; arXiv 2510.16380; 1,000 moral scenarios, 23k expert
rubric criteria) — specifically the **MoReBench-Theory** subset (150 scenarios with
explicit ethical-framework labels). This gives us framework labels for free, so we don't
have to do the tagging ourselves.

Pipeline:

1. **Sample ~10 dilemmas** from MoReBench-Theory, balanced across frameworks.
2. **Generate a commitment pool** (~30 candidate per-case verdicts via LLM).
3. **Generate a principle pool** (~20 candidates via LLM, half top-down from framework
   archetypes, half bottom-up from the commitments). Tag each with a value-loading
   vector using LLM-judge against the MoReBench-Theory labels as ground truth.
4. **Pre-compute the dialectical structure** (entailment / contradiction strands
   between every principle and every commitment) as a one-time LLM batch.
5. **Run equilibration symbolically** on the pre-computed structure (no LLM in the loop
   — fast). Repeat with sampled `C₀` to characterize behavior.
6. **Run baseline traversals** (NSGA-II, MCMC, single-pass LLM, pure-component) on the
   same dialectical structure.
7. **Plot.** Each method's outputs as points in `(A, S, F, V₁, ..., V₅)` space. Project
   onto pairs of axes. Compare frontiers.

If the plots show a coherent story — RE lands in a distinctive region, different from
single-pass LLM judgment and different from pure-Z maximization — we have a result.
If the plots are noise, we know where to invest: principle pool quality, strand
reliability, or value tagging.

Estimated effort: 2–3 weeks for the pilot. Compute cost: ~$50–100 in LLM calls
(dominated by the strand pre-computation).

## What I think the paper-shaped contribution is

This isn't another "did the LLM behave morally" benchmark. It's a methodological move:
**recasting a long-running debate in moral epistemology (does RE justify? does it
converge? is it pluralism in disguise?) as an empirical question about Pareto traversal
strategies.** The contribution would be (i) the multi-objective reframing itself, (ii)
the empirical characterization of where RE lands relative to baselines, and (iii) a
diagnostic tool — value-trajectory plots — for analyzing any LLM-based moral reasoning
system, not just our RE implementation.

The framing also gives us a clean answer to Freivogel's open problem of "what counts as
sufficient convergence": *convergence to a region of the Pareto frontier*, not to a unique
point. Different framings of "sufficient" become different Pareto-frontier regions.

## References

- Beisbart, Betz, Brun (2021), *Making Reflective Equilibrium Precise*, Ergo.
- Freivogel (2023), *Does reflective equilibrium help us converge?*, Synthese.
- Rechnitzer (2022), trolley case study reconstruction.
- Scale Labs (2025), *MoReBench: Evaluating Procedural and Pluralistic Moral Reasoning
  in Language Models*, arXiv 2510.16380. https://morebench.github.io/.
