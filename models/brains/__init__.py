"""
Foundation Brain Zoo — biologically and speculatively inspired architectures.

Each brain maps a real (or imagined) neural architecture onto liquid cells.
All share the same forward() interface so they can be trained, compared,
and ensembled interchangeably.

Active brains (10 — each tests a genuinely different wiring hypothesis):
  JellyfishBrain    — nerve net, no brain, radially symmetric (simplest possible)
  FungalBrain       — mycelium network, no neurons, chemical diffusion
  InsectBrain       — mushroom bodies, dual learned/innate tracks
  OctopusBrain      — distributed arm intelligence, no central control
  CorvidBrain       — dense nuclear clusters, no layered cortex
  DolphinBrain      — massive cortex, hemispheric switching
  HumanBrain        — full cortical hierarchy (13 regions)
  AlienBrain        — no biological constraints, pure math optimization
  UltimateBrain     — best features from all, hand-designed chimera

Ensemble:
  BrainEnsemble     — meta-controller that routes to/blends multiple brains

Retired (mammalian variants / prototypes — kept as files, removed from registry):
  CatBrain, DogBrain, ReptileBrain — mammalian wiring variants, not architecturally distinct
  NeuromorphicBrain — 4-region prototype, superseded by foundation_core
"""

from models.brains.human_brain import HumanBrain
from models.brains.octopus_brain import OctopusBrain
from models.brains.corvid_brain import CorvidBrain
from models.brains.dolphin_brain import DolphinBrain
from models.brains.insect_brain import InsectBrain
from models.brains.alien_brain import AlienBrain
from models.brains.ultimate_brain import UltimateBrain
from models.brains.fungal_brain import FungalBrain
from models.brains.jellyfish_brain import JellyfishBrain
from models.brains.ensemble import BrainEnsemble

ALL_BRAINS = {
    "jellyfish": JellyfishBrain,
    "fungal": FungalBrain,
    "insect": InsectBrain,
    "octopus": OctopusBrain,
    "corvid": CorvidBrain,
    "dolphin": DolphinBrain,
    "human": HumanBrain,
    "alien": AlienBrain,
    "ultimate": UltimateBrain,
}

__all__ = [
    "HumanBrain", "OctopusBrain", "CorvidBrain", "DolphinBrain",
    "InsectBrain", "AlienBrain", "UltimateBrain",
    "FungalBrain", "JellyfishBrain",
    "BrainEnsemble", "ALL_BRAINS",
]
