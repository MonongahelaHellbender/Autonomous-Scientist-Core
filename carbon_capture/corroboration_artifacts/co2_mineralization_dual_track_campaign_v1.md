# CO2 Mineralization Dual-Track Campaign

How should the first-pass mineralization pilot expand once we include the nearby proxy, thermochemical, pathway, and sensitivity tests from the last few days?

Plain language:
Keep the clean calcium-silicate pilot as Track A, then add a shadow challenger Track B made of high-scoring but more ambiguous candidates. That lets us test whether the current lane is too narrow without muddying the main experiment.

Technical summary:
Track A remains the exact-lane-centered anchor/control experiment. Track B is a corroboration-driven challenger set drawn from repeated top-10 proxy stability, thermochemical corroboration, and reaction-pathway screening, but kept outside the core exact-conversion interpretation because pathway families remain mixed or underconstrained.

## Why This Expands The First Pilot

- `reinforced_exact_lane_experimental_packet_v1.json`: core anchors, restructuring probes, controls, and explicit batch logic
- `materials_experiment_realism_v1.json`: which candidates are actually easy enough to screen in a real lab
- `thermochemical_carbonation_corroboration_v1.json`: a stronger ranking of candidates under thermal and compositional plausibility
- `reaction_level_carbonation_pathways_v1.json`: which candidates support exact oxide conversion versus mixed restructuring
- `co2_uptake_proxy_sensitivity_audit_v1.json`: which top candidates stay near the top under weight perturbation

## Track A: Exact-Core Interpretability Run

This is still the safest first real-world test because it prioritizes clean product-family interpretation over raw score alone.

| Label | Formula | Role | Tier | Readiness | Kinetics |
| --- | --- | --- | --- | --- | --- |
| anchor_1 | Ca3SiO5 | reinforced_anchors | core_anchor | 100.0 | FAST_SCREENABLE |
| anchor_2 | CaMgSiO4 | reinforced_anchors | core_anchor | 84.779 | FAST_SCREENABLE |
| anchor_3 | Ca2SiO4 | reinforced_anchors | core_anchor | 81.619 | MODERATE_SCREENABLE |
| anchor_4_stretch | Ca3Mg(SiO4)2 | reinforced_anchors | provisional_anchor | 78.489 | MODERATE_SCREENABLE |
| surface_control | CaSiO3 | surface_controls | stable_surface_control | 50.916 | MODERATE_SCREENABLE |
| contrast_control | CaAl12Si4O27 | contrast_candidates | stable_contrast_control | 1.979 | SLOW_OR_RESTRUCTURING_LIMITED |

## Track B: Corroboration Challengers

These candidates repeatedly score well in recent broader passes, but their reaction pathway stories are less constrained. Running them as a shadow slate tests whether the exact-core lane is too narrow.

| Formula | Shadow Role | Proxy | Corroborated | Pathway | Exact Support |
| --- | --- | --- | --- | --- | --- |
| Ca11AlSi3ClO18 | halide_mixed_network_challenger | 92.959 | 89.018 | mixed network restructuring | no |

- `Ca11AlSi3ClO18`: Recent proxy and thermochemical passes keep this halide-bearing candidate near the top, but the current pathway family is 'mixed network restructuring' rather than a clean exact-core conversion. That makes it useful as a challenger track rather than a core anchor.
| Ca11Si4SO18 | sulfur_mixed_network_challenger | 91.86 | 89.777 | mixed network restructuring | no |

- `Ca11Si4SO18`: Recent proxy and thermochemical passes keep this sulfur-bearing candidate near the top, but the current pathway family is 'mixed network restructuring' rather than a clean exact-core conversion. That makes it useful as a challenger track rather than a core anchor.
| Ca9Si4O17F | halide_mixed_network_challenger | 83.571 | 81.809 | mixed network restructuring | no |

- `Ca9Si4O17F`: Recent proxy and thermochemical passes keep this halide-bearing candidate near the top, but the current pathway family is 'mixed network restructuring' rather than a clean exact-core conversion. That makes it useful as a challenger track rather than a core anchor.
| Ca5Si2CO11 | precarbonated_completion_probe | 75.796 | 71.238 | pre-carbonated completion pathway | no |

- `Ca5Si2CO11`: Recent proxy and thermochemical passes keep this already carbon-containing candidate near the top, but the current pathway family is 'pre-carbonated completion pathway' rather than a clean exact-core conversion. That makes it useful as a challenger track rather than a core anchor.

## Decision Branches

- If Track A anchors separate cleanly from both controls and Track B challengers, keep the lane narrow and anchor-centered.
- If Track B challengers show stronger uptake but weaker product-family coherence, widen the exploratory lane but do not replace the core anchors.
- If one or more Track B challengers produce coherent, repeated mixed-network carbonation signatures, promote them into a new challenger appendix lane rather than forcing them into the exact-core interpretation.
- If Track B challengers outperform Track A on both signal strength and coherence, the current exact-core calibration is too restrictive and should be reopened.

## Hold-Outs

- `Ca3Si(ClO2)2`: Useful to remember, but still too ambiguous or already covered by the exact-lane reserve to include in the first expanded comparison run. Pathway `mixed-anion restructuring carbonation`.

## Run Size

- Minimum interpretable run: `6` materials
- Expanded two-track run: `10` materials

This is an experimental design expansion built from local autonomous screening artifacts. It is a test-planning surface, not a measured mineralization result.

