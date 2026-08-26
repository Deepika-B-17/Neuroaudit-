"""
Evaluation data structures and metric computation helpers for NeuroAudit ML experiments.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExperimentMetrics:
    """Standard container for empirical subject re-identification evaluation results."""
    dataset_name: str
    n_subjects: int
    n_samples: int
    chance_accuracy: float
    top1_accuracy: float
    balanced_accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    roc_auc: Optional[float] = None
    inference_advantage_gamma: float = 0.0
    confusion_matrix: Optional[list[list[int]]] = field(default_factory=list)
    model_name: str = "Classifier"
    evaluation_strategy: str = "GroupKFold"


def compute_inference_advantage(balanced_accuracy: float, n_classes: int) -> float:
    """
    Compute normalized adversary inference advantage (gamma in [0.0, 1.0]).

    gamma = (A_emp - A_chance) / (1.0 - A_chance)
    """
    if n_classes <= 1:
        return 0.0
    chance = 1.0 / float(n_classes)
    if balanced_accuracy <= chance:
        return 0.0
    gamma = (balanced_accuracy - chance) / (1.0 - chance)
    return float(max(0.0, min(1.0, gamma)))
