# Synthesis Protocol: Li₂In₂GeS₆

**Status:** Lab-ready (E_hull = 0.014 eV, verified against Materials Project live data)  
**Priority:** #1 new candidate from expanded discovery — largest geometric channel of all 86 candidates screened (bottleneck 2.235 Å, 20% wider than LGPS)  
**Related compound:** Li₂In₂SiS₆ (Ge analog) has been synthesized and characterized; this protocol adapts that route.

---

## Target Material

| Property | Value |
|---|---|
| Formula | Li₂In₂GeS₆ |
| Family | Li-S-In (indium thiogermanate) |
| E_hull | 0.014 eV (synthesizable) |
| Vol/atom | 23.55 Å³ (largest of 86 candidates) |
| Band gap | 2.32 eV (insulating — electrolyte viable) |
| Conductivity estimate | ≥LGPS-class if Ea ≈ 0.22 eV (DFT-NEB needed to confirm) |

---

## Precursors

| Compound | Formula | Purity | Source |
|---|---|---|---|
| Lithium sulfide | Li₂S | ≥99.9% | Sigma-Aldrich 566ed or equivalent |
| Indium(III) sulfide | In₂S₃ | ≥99.9% | Sigma-Aldrich or Alfa Aesar |
| Germanium(IV) sulfide | GeS₂ | ≥99.99% | Sigma-Aldrich 556/Strem |

**Stoichiometry:**  
Li₂S : In₂S₃ : GeS₂ = 1 : 1 : 1 (molar)

**Example batch (500 mg total target):**
- Li₂S: 500 × (45.95/452.43) = 50.8 mg
- In₂S₃: 500 × (325.83/452.43) = 360.0 mg
- GeS₂: 500 × (136.78/452.43) = 151.2 mg  
  *(MW of Li₂In₂GeS₆ ≈ 452.4 g/mol — adjust once exact structure confirmed)*

---

## Equipment

- Argon glovebox (O₂ < 1 ppm, H₂O < 1 ppm)
- Planetary ball mill (e.g., Fritsch Pulverisette 7) with ZrO₂ or agate vials
- Hydraulic press (cold pressing, 5–10 ton)
- Tube furnace or box furnace capable of 700°C
- Evacuated quartz ampoules (OD 10–12 mm) or sealed Al₂O₃ crucibles under Ar
- Vacuum line (rotary pump, < 10⁻² torr)

---

## Protocol

### Step 1 — Weighing and mixing (glovebox)

1. Weigh all precursors inside the glovebox. Li₂S is moisture-sensitive; GeS₂ can oxidize slowly in air.
2. Combine in a ZrO₂ ball-mill vial with 3–5 balls (5 mm diameter, ball-to-powder ratio ≈ 10:1).
3. Seal the vial under Ar.

### Step 2 — Ball milling

- Speed: 400–500 rpm
- Duration: 2 × 30 min with 10 min cooling break (prevents excessive heating)
- Result: fine gray/yellow powder, uniform mixture

### Step 3 — Cold pressing

1. Transfer powder to a 10 mm die inside the glovebox.
2. Press at 5–7 ton (≈ 630–900 MPa for 10 mm die) for 5 min.
3. Result: dense pellet, ~65–75% theoretical density.

### Step 4 — Sealing

**Option A (preferred) — Evacuated quartz ampoule:**
1. Place pellet in a quartz ampoule inside the glovebox.
2. Transfer to vacuum line, evacuate to < 10⁻² torr over 10 min.
3. Flame-seal under vacuum.

**Option B — Sealed tube furnace with Ar flow:**
- Place pellet in Al₂O₃ crucible inside a quartz tube.
- Purge with 3 cycles of Ar/vacuum. Run furnace under flowing Ar.

### Step 5 — Sintering

| Stage | Temperature | Ramp rate | Hold |
|---|---|---|---|
| Pre-reaction | 300°C | 2°C/min | 6 h |
| Main sintering | 650°C | 2°C/min | 48–72 h |
| Cooling | RT | 1°C/min | — |

**Note:** Li₂In₂SiS₆ (the Si analog) was synthesized at 700°C by Baumer et al. Start at 650°C and increase if XRD shows incomplete reaction. Do not exceed 750°C — risk of decomposition to binary sulfides.

### Step 6 — Regrinding and re-sintering (optional)

If XRD shows secondary phases (In₂S₃, GeS₂ peaks remain):
1. Break ampoule in glovebox, regrind to powder.
2. Re-press and repeat Step 4–5 at 680°C for 48 h.

---

## Characterization

### A — Phase purity (XRD)

- Instrument: Powder XRD (Cu Kα, λ = 1.5406 Å)
- Sample prep: grind in glovebox, seal under Kapton tape or in an airtight dome holder
- Target: compare to MP-predicted pattern for Li₂In₂GeS₆ (mp-id available from expanded_discovery_results.json)
- Reject if: In₂S₃ peaks present at 2θ ≈ 28.6°, 33.0°, 47.2° (strongest reflections)

### B — Conductivity and activation energy (AC impedance spectroscopy)

**Setup:**
- Pellet geometry: 10 mm diameter, ~1 mm thickness (re-press if needed after sintering)
- Electrode: sputtered Au or applied carbon paste (blocking electrodes are fine for Ea measurement)
- Frequency range: 1 Hz – 10 MHz
- Temperature range: 25°C – 80°C (7–8 points, ΔT = 10°C)

**Analysis:**
- Fit Nyquist plot with equivalent circuit: R_bulk (‖ C_bulk) + R_grain-boundary (‖ CPE) + CPE_electrode
- σ = L / (R_bulk × A)   where L = thickness, A = area
- Plot ln(σ·T) vs. 1/T → slope = −Ea/k_B → extract Ea

**Target for LGPS-class:**
- σ(25°C) > 1 mS/cm
- Ea < 0.25 eV

**Expected result for Li₂In₂GeS₆ (model estimate):**
- Ea: 0.22–0.30 eV (DFT-NEB needed for precision)
- σ: 0.1–4 mS/cm (wide range due to model uncertainty; experiment will be definitive)

### C — ⁷Li solid-state NMR (optional, high-value)

- Measures Li+ dynamics directly
- T₁ relaxation time → correlation time for Li hop rate
- Complements impedance: confirms bulk vs. grain-boundary conductivity

---

## Safety Notes

- Li₂S reacts vigorously with water → H₂S (toxic). All handling must be in glovebox or dry conditions.
- GeS₂ is an eye/skin irritant. Handle with appropriate PPE.
- Evacuated quartz ampoules can shatter — use a protective shield when breaking.
- H₂S may be released if ampoule is opened in air after failed synthesis. Open in fume hood.

---

## Literature Context

- Li₂In₂SiS₆ (Si analog): synthesized by Baumer et al. 2015 (Z. Anorg. Allg. Chem.), characterized as a wide-gap semiconductor with layered structure.
- Li₂In₂GeS₆ may not yet be characterized as an electrolyte in the literature — this would be a novel measurement.
- Expanded pipeline rank: #1 new candidate by geometric channel width (bottleneck 2.235 Å > LGPS 1.859 Å).
- If Ea < 0.25 eV confirmed by impedance, this compound would be competitive with current best-in-class sulfide electrolytes.
