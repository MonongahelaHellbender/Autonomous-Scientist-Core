# How to Replicate the Autonomous Scientist
## The UIL 4-Module Discovery Protocol

This framework allows a single researcher to autonomously explore any scientific manifold.

### Step 1: Define the Manifold
Identify the "Geometric Invariant" of your problem.
- *Battery:* Tunnel width > 1.5 Å.
- *Carbon:* Pore space > 17 Å³.
- *Solar:* Band gap between 1.1 and 1.5 eV.

### Step 2: The Ingestion Module
Write a script in `/ingestion` that queries a public API (like MP-API, NASA, or WHO) to gather raw candidates matching your manifold.

### Step 3: The Intelligence Module
Write a script in `/intelligence` to rank these candidates based on performance and stability.

### Step 4: The Adversarial Module
Write a script in `/adversarial` that attempts to break your discovery. Check for:
- Toxicity / Radioactivity
- Raw material cost / Scarcity
- Competitive interference (e.g., Moisture)

### Step 5: Version & Push
Use Git to track the "Chain of Logic." If the Adversarial module rejects a material, your commit history will document *why*, creating a robust scientific paper trail.
