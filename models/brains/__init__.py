"""
Foundation Brain Zoo — biologically and speculatively inspired architectures.

Each brain maps a real (or imagined) neural architecture onto liquid cells.
All share the same forward() interface so they can be trained, compared,
and ensembled interchangeably.

Available brains:
  HumanBrain        — full cortical hierarchy (13 regions)
  OctopusBrain      — distributed arm intelligence, no central control
  CorvidBrain       — dense nuclear clusters, no layered cortex
  DolphinBrain      — massive cortex, hemispheric switching
  InsectBrain       — mushroom bodies, dual learned/innate tracks
  AlienBrain        — no biological constraints, pure math optimization
  UltimateBrain     — best features from all, hand-designed chimera
  FungalBrain       — mycelium network, no central brain, chemical diffusion
  ReptileBrain      — brainstem-dominant, energy-efficient, instinct-driven
  JellyfishBrain    — nerve net, no brain, radially symmetric
  CatBrain          — visual predator, huge cerebellum, whisker cortex
  DogBrain          — olfactory-dominant, social cognition, reward-driven

Ensemble:
  BrainEnsemble     — meta-controller that routes to/blends multiple brains
"""

from models.brains.human_brain import HumanBrain
from models.brains.octopus_brain import OctopusBrain
from models.brains.corvid_brain import CorvidBrain
from models.brains.dolphin_brain import DolphinBrain
from models.brains.insect_brain import InsectBrain
from models.brains.alien_brain import AlienBrain
from models.brains.ultimate_brain import UltimateBrain
from models.brains.fungal_brain import FungalBrain
from models.brains.reptile_brain import ReptileBrain
from models.brains.jellyfish_brain import JellyfishBrain
from models.brains.cat_brain import CatBrain
from models.brains.dog_brain import DogBrain
from models.brains.ensemble import BrainEnsemble

ALL_BRAINS = {
    "human": HumanBrain,
    "octopus": OctopusBrain,
    "corvid": CorvidBrain,
    "dolphin": DolphinBrain,
    "insect": InsectBrain,
    "alien": AlienBrain,
    "ultimate": UltimateBrain,
    "fungal": FungalBrain,
    "reptile": ReptileBrain,
    "jellyfish": JellyfishBrain,
    "cat": CatBrain,
    "dog": DogBrain,
}

__all__ = [
    "HumanBrain", "OctopusBrain", "CorvidBrain", "DolphinBrain",
    "InsectBrain", "AlienBrain", "UltimateBrain",
    "FungalBrain", "ReptileBrain", "JellyfishBrain",
    "CatBrain", "DogBrain",
    "BrainEnsemble", "ALL_BRAINS",
]
