"""Deterministic, Explainable Risk Assessment Engine.

Computes a calibrated risk score (0-100), categorical risk level
(LOW, MEDIUM, HIGH, CRITICAL), and actionable explanation reasons
based on observable visual detections and restricted zone context.

Design Rules:
- Deterministic heuristic prioritization; zero random numbers.
- Explains the exact rationale for every risk score adjustment.
- Aligned with API_CONTRACT.md and ARCHITECTURE.md.
"""

from typing import Any, Dict, List, Optional, Tuple


class RiskEngine:
    """Evaluates surveillance incidents to determine operational risk priority."""

    BASE_SCORES: Dict[str, int] = {
        "CRITICAL": 80,
        "HIGH": 60,
        "MEDIUM": 40,
        "LOW": 20,
    }

    @classmethod
    def evaluate(
        cls,
        severity: str,
        confidence: float,
        zone_id: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, str, List[str], str]:
        """Compute risk score, risk level, explanation reasons, and action recommendation.

        Args:
            severity: Declared base severity (LOW, MEDIUM, HIGH, CRITICAL).
            confidence: Detector confidence score [0.0, 1.0].
            zone_id: Identifier of the restricted zone breached.
            evidence: Dictionary containing visual detector details.

        Returns:
            Tuple[int, str, List[str], str]:
                (risk_score, risk_level, reasons, recommended_action)
        """
        evidence = evidence or {}
        reasons: List[str] = []

        # 1. Base score from incident severity
        clean_severity = severity.upper() if severity else "HIGH"
        score = cls.BASE_SCORES.get(clean_severity, 50)
        reasons.append(f"Base severity set to {clean_severity} ({score} pts)")

        # 2. Zone incursion factor
        if zone_id and zone_id.strip():
            score += 10
            reasons.append(f"Restricted-zone boundary breached ({zone_id}) (+10 pts)")
        else:
            reasons.append("Perimeter proximity observation without confirmed zone ID")

        # 3. Detector confidence calibration
        if confidence >= 0.85:
            score += 10
            reasons.append(f"High detector confidence ({confidence:.2f} >= 0.85) (+10 pts)")
        elif confidence >= 0.60:
            score += 5
            reasons.append(f"Moderate detector certainty ({confidence:.2f}) (+5 pts)")
        else:
            score -= 10
            reasons.append(f"Lower detector confidence ({confidence:.2f} < 0.60) (-10 pts)")

        # 4. Multi-person presence factor
        person_count = evidence.get("person_count", 1)
        if isinstance(person_count, (int, float)) and person_count >= 2:
            score += 10
            reasons.append(f"Multiple individuals observed ({int(person_count)} persons) (+10 pts)")

        # 5. Clamp final score strictly to [0, 100]
        final_score = max(0, min(100, score))

        # 6. Map final score to categorical risk level
        if final_score >= 85:
            risk_level = "CRITICAL"
            recommended_action = (
                "Immediate tactical dispatch: verify visual feed and initiate perimeter protocol"
            )
        elif final_score >= 65:
            risk_level = "HIGH"
            recommended_action = "Request human verification and alert nearest patrol unit"
        elif final_score >= 40:
            risk_level = "MEDIUM"
            recommended_action = "Monitor camera feed and queue for secondary operator review"
        else:
            risk_level = "LOW"
            recommended_action = "Log incident for routine audit; no immediate response required"

        return final_score, risk_level, reasons, recommended_action
