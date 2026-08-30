"""Decision Receipt Generator — creates machine-readable audit trails.

Every trade decision gets a permanent receipt that captures:
- Full reasoning chain
- Agent scores
- Kill test results
- Risk gate results
- Execution outcome
- MCP tools used
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from killjoy.agent.models import (
    DecisionReceipt,
    KillDecision,
    MarketThesis,
    RiskDecision,
    TradeProposal,
)

logger = logging.getLogger(__name__)

RECEIPTS_DIR = Path("data") / "receipts"


class DecisionReceiptManager:
    """Generate and persist decision receipts."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or RECEIPTS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def create_receipt(
        self,
        proposal: TradeProposal,
        thesis: MarketThesis,
        kill_decision: KillDecision,
        risk_decision: RiskDecision | None = None,
        portfolio_approved: bool = False,
        portfolio_reasons: list[str] | None = None,
        order_id: str = "",
        agent_scores: dict[str, Decimal] | None = None,
    ) -> DecisionReceipt:
        """Create a decision receipt from the full pipeline context."""

        # Determine final decision
        if not kill_decision.survives:
            final_decision = "KILLED"
        elif not portfolio_approved:
            final_decision = "PORTFOLIO_REJECTED"
        elif risk_decision and not risk_decision.approved:
            final_decision = "RISK_REJECTED"
        else:
            final_decision = "EXECUTE"

        risk_reasons = risk_decision.reasons if risk_decision else []

        receipt = DecisionReceipt(
            trade_id=proposal.id,
            underlying=proposal.underlying,
            strategy=proposal.strategy.value,
            thesis=proposal.thesis,
            confidence=proposal.confidence,
            kill_score=kill_decision.kill_score,
            survives_kill=kill_decision.survives,
            portfolio_check=portfolio_approved,
            risk_check=risk_decision.approved if risk_decision else False,
            final_decision=final_decision,
            kill_reasons=[f"[{o.category}] {o.reasoning}" for o in kill_decision.objections],
            counterfactual=kill_decision.counterfactual,
            portfolio_reasons=portfolio_reasons or [],
            risk_reasons=risk_reasons,
            order_id=order_id,
            alpaca_status="filled" if order_id else ("dry_run" if final_decision == "EXECUTE" else ""),
            agent_scores=agent_scores or {},
            debate_rounds=len(kill_decision.debate_transcript),
            mcp_tools_used=[
                "get_account_info",
                "get_stock_snapshot",
                "get_option_chain",
                "get_option_snapshot",
                "get_all_positions",
                "get_orders",
                "place_option_order" if order_id else "",
            ],
        )

        self._persist(receipt)
        logger.info("Decision receipt created: %s — %s", receipt.receipt_id, final_decision)
        return receipt

    def update_outcome(self, receipt_id: str, pnl: float, result: str) -> None:
        """Update a receipt with final trade outcome."""
        receipt = self._load(receipt_id)
        if receipt:
            receipt.outcome_pnl = Decimal(str(pnl))
            receipt.outcome_result = result
            self._persist(receipt)

    def get_receipt(self, receipt_id: str) -> DecisionReceipt | None:
        return self._load(receipt_id)

    def get_all_receipts(self) -> list[DecisionReceipt]:
        receipts = []
        for f in self._dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                receipts.append(DecisionReceipt(**data))
            except Exception as e:
                logger.debug("Failed to load receipt %s: %s", f, e)
        return sorted(receipts, key=lambda r: r.timestamp, reverse=True)

    def get_receipts_by_decision(self, decision: str) -> list[DecisionReceipt]:
        return [r for r in self.get_all_receipts() if r.final_decision == decision]

    def get_summary(self) -> dict[str, Any]:
        """Get receipt summary stats."""
        receipts = self.get_all_receipts()
        if not receipts:
            return {
                "total": 0,
                "executed": 0,
                "killed": 0,
                "portfolio_rejected": 0,
                "risk_rejected": 0,
                "avg_kill_score": 0,
                "avg_debate_rounds": 0,
                "mcp_tools_used": [],
            }

        executed = [r for r in receipts if r.final_decision == "EXECUTE"]
        killed = [r for r in receipts if r.final_decision == "KILLED"]
        portfolio_rejected = [r for r in receipts if r.final_decision == "PORTFOLIO_REJECTED"]
        risk_rejected = [r for r in receipts if r.final_decision == "RISK_REJECTED"]

        avg_kill = sum(float(r.kill_score) for r in receipts) / len(receipts)
        avg_debate = sum(r.debate_rounds for r in receipts) / len(receipts)

        return {
            "total": len(receipts),
            "executed": len(executed),
            "killed": len(killed),
            "portfolio_rejected": len(portfolio_rejected),
            "risk_rejected": len(risk_rejected),
            "avg_kill_score": round(avg_kill, 3),
            "avg_debate_rounds": round(avg_debate, 1),
            "recent_receipts": [
                {
                    "receipt_id": r.receipt_id,
                    "underlying": r.underlying,
                    "strategy": r.strategy,
                    "final_decision": r.final_decision,
                    "kill_score": float(r.kill_score),
                    "confidence": float(r.confidence),
                    "timestamp": str(r.timestamp),
                }
                for r in receipts[:10]
            ],
        }

    def _persist(self, receipt: DecisionReceipt) -> None:
        filepath = self._dir / f"{receipt.receipt_id}.json"
        data = receipt.model_dump(mode="json")
        filepath.write_text(json.dumps(data, default=str, indent=2))

    def _load(self, receipt_id: str) -> DecisionReceipt | None:
        filepath = self._dir / f"{receipt_id}.json"
        if filepath.exists():
            try:
                data = json.loads(filepath.read_text())
                return DecisionReceipt(**data)
            except Exception:
                pass
        return None
