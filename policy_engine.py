"""
DeploySentry AI — Policy Engine

Takes details about a proposed code change and decides whether it should be
APPROVED, sent for REVIEW, or BLOCKED — based on rules defined in rules.yaml.

This is deliberately deterministic (no AI/randomness here) — the same input
always produces the same decision. That predictability matters for anything
safety-related. The AI explanation layer comes later, on TOP of this decision,
not instead of it.
"""

from datetime import datetime
from typing import List, Dict, Any

import yaml


class ChangeRequest:
    """Represents one proposed code change to be evaluated."""

    def __init__(
        self,
        files_changed: List[str],
        lines_changed: int,
        branch: str,
        is_pull_request: bool,
        deploy_hour: int = None,
    ):
        self.files_changed = files_changed
        self.lines_changed = lines_changed
        self.branch = branch
        self.is_pull_request = is_pull_request
        # If no hour is given, use the current real hour
        self.deploy_hour = deploy_hour if deploy_hour is not None else datetime.now().hour


class PolicyEngine:
    def __init__(self, rules_path: str = "rules.yaml"):
        with open(rules_path, "r") as f:
            config = yaml.safe_load(f)
        self.rules = config["rules"]
        self.settings = config["settings"]

    # ---- Each condition check is a small, readable function ----

    def _touches_critical_path(self, change: ChangeRequest) -> bool:
        critical_paths = self.settings["critical_paths"]
        return any(
            critical in f for f in change.files_changed for critical in critical_paths
        )

    def _direct_push_to_main(self, change: ChangeRequest) -> bool:
        return change.branch == "main" and not change.is_pull_request

    def _large_changeset(self, change: ChangeRequest) -> bool:
        return change.lines_changed > self.settings["large_changeset_lines"]

    def _off_hours(self, change: ChangeRequest) -> bool:
        start = self.settings["business_hours_start"]
        end = self.settings["business_hours_end"]
        return change.deploy_hour < start or change.deploy_hour > end

    def _check_condition(self, condition_name: str, change: ChangeRequest) -> bool:
        condition_map = {
            "touches_critical_path": self._touches_critical_path,
            "direct_push_to_main": self._direct_push_to_main,
            "large_changeset": self._large_changeset,
            "off_hours": self._off_hours,
            "always": lambda c: True,
        }
        check_fn = condition_map.get(condition_name)
        if check_fn is None:
            raise ValueError(f"Unknown condition in rules.yaml: {condition_name}")
        return check_fn(change)

    def evaluate(self, change: ChangeRequest) -> Dict[str, Any]:
        """
        Checks the change against every rule in order.
        Returns the FIRST matching rule's decision.
        """
        for rule in self.rules:
            if self._check_condition(rule["condition"], change):
                return {
                    "action": rule["action"],
                    "matched_rule": rule["name"],
                    "reason": rule["description"],
                }
        # Should never reach here because of the "Default" catch-all rule,
        # but fail safe just in case.
        return {"action": "REVIEW", "matched_rule": "Fallback", "reason": "No rule matched"}


# ---- Quick manual test when running this file directly ----
if __name__ == "__main__":
    engine = PolicyEngine("rules.yaml")

    test_cases = [
        ChangeRequest(
            files_changed=["frontend/home.js"],
            lines_changed=50,
            branch="feature/new-header",
            is_pull_request=True,
            deploy_hour=14,
        ),
        ChangeRequest(
            files_changed=["backend/auth/login.py"],
            lines_changed=30,
            branch="feature/fix-login",
            is_pull_request=True,
            deploy_hour=11,
        ),
        ChangeRequest(
            files_changed=["backend/server.py"],
            lines_changed=20,
            branch="main",
            is_pull_request=False,
            deploy_hour=10,
        ),
        ChangeRequest(
            files_changed=["docs/readme.md"] * 1,
            lines_changed=800,
            branch="feature/big-refactor",
            is_pull_request=True,
            deploy_hour=15,
        ),
    ]

    for i, case in enumerate(test_cases, start=1):
        result = engine.evaluate(case)
        print(f"Test {i}: {result['action']:8} — {result['matched_rule']} ({result['reason']})")
