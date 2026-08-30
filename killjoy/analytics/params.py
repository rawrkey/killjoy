"""Bounded self-improvement — parameter recommendations from trade outcomes.

The LLM can recommend parameter changes, but every change must:
- Have a reason
- Have evidence
- Be logged
- Be bounded
- Be reversible

The LLM CANNOT rewrite source code or bypass safety.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

PARAMS_DIR = Path("data") / "params"


class ParameterRecommendation(BaseModel):
    """A bounded parameter change recommendation."""
    parameter: str = Field(description="Parameter name")
    current_value: str = Field(description="Current value")
    recommended_value: str = Field(description="Recommended new value")
    reason: str = Field(description="Why this change is recommended")
    evidence: str = Field(description="Evidence supporting this change")
    confidence: float = Field(ge=0, le=1, description="Confidence in recommendation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ParameterManager:
    """Manage bounded parameter recommendations and apply approved changes.

    Parameters are persisted to JSON and can be reverted.
    """
    # Bounded parameter ranges — the LLM cannot recommend outside these
    BOUNDED_PARAMS = {
        "min_dte": {"min": 7, "max": 60, "type": "int"},
        "max_dte": {"min": 14, "max": 90, "type": "int"},
        "min_reward_risk": {"min": 0.5, "max": 3.0, "type": "float"},
        "min_confidence": {"min": 0.1, "max": 0.8, "type": "float"},
        "max_loss_per_trade": {"min": 100, "max": 2000, "type": "float"},
        "preferred_iv_rank_min": {"min": 10, "max": 60, "type": "float"},
        "preferred_iv_rank_max": {"min": 40, "max": 90, "type": "float"},
        "max_correlation": {"min": 0.3, "max": 0.9, "type": "float"},
    }

    # Default values
    DEFAULTS = {
        "min_dte": 7,
        "max_dte": 45,
        "min_reward_risk": 1.0,
        "min_confidence": 0.3,
        "max_loss_per_trade": 500,
        "preferred_iv_rank_min": 25,
        "preferred_iv_rank_max": 75,
        "max_correlation": 0.7,
    }

    def __init__(self, params_dir: Path | None = None) -> None:
        self._dir = params_dir or PARAMS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._params = dict(self.DEFAULTS)
        self._history: list[ParameterRecommendation] = []
        self._load()

    def _load(self) -> None:
        """Load parameters from disk."""
        filepath = self._dir / "current_params.json"
        if filepath.exists():
            try:
                data = json.loads(filepath.read_text())
                # Convert back to proper types
                for key, bounds in self.BOUNDED_PARAMS.items():
                    if key in data:
                        if bounds["type"] == "int":
                            data[key] = int(data[key])
                        else:
                            data[key] = float(data[key])
                self._params.update(data)
            except Exception as e:
                logger.warning("Failed to load params: %s", e)

        # Load history
        history_file = self._dir / "param_history.jsonl"
        if history_file.exists():
            try:
                for line in history_file.read_text().splitlines():
                    if line.strip():
                        self._history.append(ParameterRecommendation(**json.loads(line)))
            except Exception as e:
                logger.warning("Failed to load param history: %s", e)

    def _save(self) -> None:
        """Save current parameters to disk."""
        filepath = self._dir / "current_params.json"
        filepath.write_text(json.dumps(self._params, indent=2))

    def get(self, param: str) -> Any:
        """Get a parameter value."""
        return self._params.get(param, self.DEFAULTS.get(param))

    def get_all(self) -> dict[str, Any]:
        """Get all current parameters."""
        return dict(self._params)

    def recommend(
        self,
        param: str,
        recommended_value: Any,
        reason: str,
        evidence: str,
        confidence: float = 0.5,
    ) -> ParameterRecommendation:
        """Submit a parameter recommendation.

        Validates against bounds before accepting.
        """
        if param not in self.BOUNDED_PARAMS:
            raise ValueError(f"Unknown parameter: {param}")

        bounds = self.BOUNDED_PARAMS[param]
        value_type = bounds["type"]

        # Type conversion
        try:
            if value_type == "int":
                val = int(recommended_value)
            else:
                val = float(recommended_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for {param}: {recommended_value}")

        # Bounds check
        if val < bounds["min"] or val > bounds["max"]:
            raise ValueError(
                f"Value {val} for {param} outside bounds [{bounds['min']}, {bounds['max']}]"
            )

        rec = ParameterRecommendation(
            parameter=param,
            current_value=str(self._params.get(param, "")),
            recommended_value=str(val),
            reason=reason,
            evidence=evidence,
            confidence=confidence,
        )

        self._history.append(rec)
        self._save_history()

        logger.info(
            "Parameter recommendation: %s = %s (reason: %s, confidence: %.2f)",
            param, val, reason, confidence,
        )

        return rec

    def apply_recommendation(self, rec: ParameterRecommendation, min_confidence: float = 0.6) -> bool:
        """Apply a recommendation if confidence is sufficient.

        Returns True if applied, False if confidence too low.
        """
        if rec.confidence < min_confidence:
            logger.info(
                "Recommendation confidence %.2f below threshold %.2f, not applying",
                rec.confidence, min_confidence,
            )
            return False

        old_value = self._params.get(rec.parameter)
        # Store as proper type
        bounds = self.BOUNDED_PARAMS[rec.parameter]
        if bounds["type"] == "int":
            self._params[rec.parameter] = int(rec.recommended_value)
        else:
            self._params[rec.parameter] = float(rec.recommended_value)
        self._save()

        logger.info(
            "Applied parameter change: %s %s -> %s",
            rec.parameter, old_value, rec.recommended_value,
        )
        return True

    def revert_last(self) -> bool:
        """Revert the last applied parameter change."""
        if not self._history:
            return False

        last = self._history[-1]
        try:
            # Revert to proper type
            bounds = self.BOUNDED_PARAMS.get(last.parameter, {})
            old_val = last.current_value
            if bounds.get("type") == "int":
                self._params[last.parameter] = int(old_val)
            else:
                self._params[last.parameter] = float(old_val)
            self._save()
            logger.info("Reverted parameter: %s -> %s", last.parameter, last.current_value)
            return True
        except Exception as e:
            logger.warning("Failed to revert: %s", e)
            return False

    def _save_history(self) -> None:
        """Append recommendation to history file."""
        history_file = self._dir / "param_history.jsonl"
        try:
            with open(history_file, "a") as f:
                for rec in self._history[-1:]:  # Only write new entries
                    f.write(json.dumps(rec.model_dump(mode="json"), default=str) + "\n")
        except Exception as e:
            logger.warning("Failed to save param history: %s", e)

    def get_history(self) -> list[ParameterRecommendation]:
        """Get all parameter recommendations."""
        return list(self._history)
