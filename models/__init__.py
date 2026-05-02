"""
Foundation — Neural Model Suite
================================

Pure deep liquid neural network backbone for the Foundation AI system.

Architecture:
  1. LiquidCell / MultiScaleLiquidCell — continuous-time recurrence
  2. Stacked LiquidBlocks with residual connections — depth without gradient loss
  3. Domain-aware gating — routes signal through domain-specific expert heads
  4. Three output heads — prediction, anomaly scoring, property regression

Import hierarchy:
  from models.liquid_core import LiquidCell, MultiScaleLiquidCell, LiquidPredictor
  from models.scientist_brain import FoundationCore (alias: ScientistBrain)
  from models.bridge import load_tasuke_weights, sync_from_tasuke
  from models.presence import render_scientist_presence
"""
