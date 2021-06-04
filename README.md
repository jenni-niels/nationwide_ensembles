# Nationwide Ensembles

## Ensemble Stats

Not all states have available/stable election so we will use Census geography for this baseline.

### Initial Plan:
* Plan Stats:
  * Cut edges
* District Stats:
  * TOTPOP broken down by race and ethnicity
  * VAP broken down by race and ethnicity

## Retraceable Chains

Key Observation: The path of a chain only depends on the two elements of state. The prior plan and the current seed/value of the pseudo-random number generator.  If we store those values every $m$ steps and reseed the RNG with that values, we can fully reconstruct the chain for those $m-1$ steps.  Thus the choice of $m$ is a trade-off between the cold storage space required to store "landmark" plans, and computation time required to recover the additional steps of the chain.

### Storage Format

`plans_0_999.json`:

    {
        "rnd_seed": i,
        "initial_plan": "relative_path_to_unit_assignment.csv",
        "ensemble_stats": [
            {
                "plan_scores": {"cut_edges": n, ... }
                "district_scores": {
                    "d0": {"TOTPOP": p_0, "HPOP": p_1, "VAP": v_0, ...},
                    ...
                    "dk": {"TOTPOP": p_0', "HPOP": p_1', "VAP": v_0', ...}}
            }
            ...
        ]
    }

, where $i \in \mathbb{Z}^{\geq 0}$ and $d_i$ is the $i$th district id and $p_i$, $p_i'$, $v_i$, $v_i'$ are all $\in \mathbb{Z}^{\geq 0}$.

`plan_0.csv`:


| Unit GEOID | Assignment |
|------------|------------|
| 48001      | d0         |
| 48003      | d2         |
| 48005      | d0         |
| 48007      | d5         |
| 48009      | d5         |

etc.
