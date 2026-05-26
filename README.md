# Reflective Equilibrium Machine

Multi-agent LLM mechanization of Reflective Equilibrium (RE) as formalized by Beisbart et al.,
with a case study replicating Rechnitzer's trolley equilibration.

## How it works

Six agents:

- **CommitmentFormer** — reads raw case scenarios and forms per-case action verdicts (the
  initial commitments C₀).
- **PrincipleInferencer** — A-step: proposes a revised theory T given current C.
- **CommitmentInferencer** — B-step: proposes a revised commitment set C given current T and
  C₀.
- **AccountVerifier** — per-commitment score: does T entail / contradict / stay silent on each
  commitment? Python averages the per-item scores.
- **SystematicityVerifier** — single score: how compact and unifying is T?
- **FaithfulnessVerifier** — per-IC status (preserved / reformulated / dropped / denied)
  mapped to {1.0, 0.8, 0.3, 0.0} and averaged.

Aggregate `Z = α_a · Account + α_s · Systematicity + α_f · Faithfulness` drives a greedy
alternating loop: A-step, B-step, repeat. Accept any proposal that strictly improves Z. Stop
when neither step is accepted (fixed point) or at MAX_STEPS.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env       # add your OpenRouter key
```

## The five trolley cases

The system is seeded with these five raw scenarios (full text in
`experiments/trolley.py`). No moral verdicts are baked in — the CommitmentFormer
agent reads the cases and produces the initial commitments C₀.

1. **Case 1 — Judge.** A judge can frame an innocent person to satisfy a mob and save five
   hostages from being killed. (Foot 1967.)
2. **Case 2 — Trolley driver.** The driver of a runaway trolley can either continue toward
   five workmen or steer onto a side track with one workman.
3. **Case 3 — Bystander at the switch.** A bystander next to a switch can divert a runaway
   trolley from five workmen onto one workman. (Thomson 1976.)
4. **Case 4 — Fat man on the bridge.** A bystander on a bridge can push a heavy man onto the
   track to stop the trolley, killing the heavy man but saving five workmen.
5. **Case 5 — Three-way switch.** A bystander can do nothing (five die), throw the switch one
   way (one dies), or throw the switch the other way (five die on a different track).

The philosophically interesting tension is between Case 3 (intuitively permissible diversion)
and Case 4 (intuitively impermissible pushing) — both kill one to save five, but feel morally
different. The RE process is what's supposed to articulate why.

## Run the trolley experiment

```bash
python -m experiments.trolley                # JSON trace only
python -m experiments.trolley --markdown     # also write a readable .md writeup
```

Override the default model per-run:

```bash
RE_MODEL=anthropic/claude-3.5-haiku python -m experiments.trolley --markdown
RE_MODEL=openai/gpt-4o-mini python -m experiments.trolley --markdown
```

Re-render the markdown of a previous JSON trace (useful when the renderer changes):

```bash
python -m experiments.rerender runs/trolley_<timestamp>.json --model <model>
```

## Three-model comparison (May 2026)

Same prompts, same 5 raw trolley cases. Different equilibrium positions:

| Model | Steps | Accepted | Principles | Faithfulness | Z |
|---|---|---|---|---|---|
| `google/gemini-2.0-flash-001` | 4 | 3 | **2** — clean doing/allowing split | 1.000 | 0.950 |
| `anthropic/claude-3.5-haiku` | 4 | 5 | **3** — incl. utilitarian carve-out for fat-man | 0.960 | 0.953 |
| `openai/gpt-4o-mini` | 2 | 1 | **5** — one per case, no abstraction | 1.000 | 0.850 |

- **Gemini** lands on a Foot/Thomson-style structural distinction (divert vs. directly cause
  harm, with a carve-out for diverting an existing threat). Two principles, broad coverage.
- **Claude Haiku** moves more aggressively — reformulates IC4 ("MUST NOT push the heavy man")
  to a strict-conditions permission, building toward a consequentialist framework with
  explicit "last resort" carve-outs.
- **GPT-4o-mini** fails to abstract — its PrincipleInferencer just emits one principle per
  commitment. Perfect Account, but Systematicity collapses to 0.400.

See the per-run writeups in `runs/`.

## Layout

```
src/re_machine/
  schemas.py     # Pydantic types (Case, Commitment, Principle, EpistemicState, ...)
  llm.py         # OpenRouter wrapper, structured-JSON helper
  loop.py        # equilibrate(...)
  trace.py       # rich-printed console + JSON dump + markdown renderer
  agents/        # 6 agents, one file each
experiments/
  trolley.py     # the 5-case replication run
  rerender.py    # regenerate markdown from a stored JSON trace
runs/            # JSON traces + markdown writeups
```

## Source documents

- `RP.pdf` — research plan framing the project.
- `formal_re.pdf` — Beisbart et al.'s formal RE.
- `trolley.pdf` — Rechnitzer's trolley case study.
