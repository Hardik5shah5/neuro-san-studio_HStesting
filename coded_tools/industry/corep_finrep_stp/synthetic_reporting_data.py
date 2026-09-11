# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# END COPYRIGHT

from typing import Any
from typing import Dict

from neuro_san.interfaces.coded_tool import CodedTool


class SyntheticReportingData(CodedTool):
    """Return a small, deterministic and explicitly synthetic reporting snapshot."""

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide demo data without reading files, databases, credentials, or user data."""
        reporting_date = str(args.get("reporting_date", "2026-08-31"))
        reporting_run_id = f"DEMO-{reporting_date.replace('-', '')}-001"

        snapshot = {
            "reporting_run_id": reporting_run_id,
            "mode": "SYNTHETIC_DEMO_ONLY",
            "confidential_data_used": False,
            "reporting_date": reporting_date,
            "taxonomy_version": "EU_TAXONOMY_DEMO_2026.1",
            "entity_scope": ["DEMO_BANK_CONSOLIDATED"],
            "currency": "EUR",
            "source_snapshots": [
                {
                    "source_id": "DEMO_GL_001",
                    "system": "synthetic_general_ledger",
                    "as_of": reporting_date,
                    "record_count": 6,
                    "control_total_eur": 1250000000,
                    "schema_hash": "demo-schema-gl-v1",
                },
                {
                    "source_id": "DEMO_RISK_001",
                    "system": "synthetic_risk_data",
                    "as_of": reporting_date,
                    "record_count": 4,
                    "control_total_eur": 850000000,
                    "schema_hash": "demo-schema-risk-v1",
                },
            ],
            "source_records": [
                {"source_id": "DEMO_GL_001", "account": "cash", "amount_eur": 150000000},
                {"source_id": "DEMO_GL_001", "account": "loans", "amount_eur": 850000000},
                {"source_id": "DEMO_GL_001", "account": "securities", "amount_eur": 200000000},
                {"source_id": "DEMO_GL_001", "account": "other_assets", "amount_eur": 50000000},
                {"source_id": "DEMO_GL_001", "account": "customer_deposits", "amount_eur": 1000000000},
                {"source_id": "DEMO_GL_001", "account": "equity", "amount_eur": 150000000},
                {"source_id": "DEMO_RISK_001", "measure": "risk_exposure", "amount_eur": 850000000},
                {"source_id": "DEMO_RISK_001", "measure": "own_funds", "amount_eur": 150000000},
            ],
            "expected_controls": [
                {"control_id": "DEMO-BAL-001", "description": "Assets equal liabilities plus equity", "expected": "PASS"},
                {"control_id": "DEMO-REC-001", "description": "FINREP assets reconcile to general ledger", "expected": "PASS"},
                {"control_id": "DEMO-REC-002", "description": "COREP risk exposure reconciles to risk source", "expected": "PASS"},
                {"control_id": "DEMO-LIN-001", "description": "All demo cells have source references", "expected": "PASS"},
            ],
            "lineage_policy": "Every demo value must retain source_id, mapping_rule_id, calculation_id, and control_id.",
        }
        sly_data["reporting_run_id"] = reporting_run_id
        sly_data["data_mode"] = "SYNTHETIC_DEMO_ONLY"
        return snapshot