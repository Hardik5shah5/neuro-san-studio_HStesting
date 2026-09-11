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

import asyncio

from coded_tools.industry.corep_finrep_stp.synthetic_reporting_data import SyntheticReportingData


def test_synthetic_reporting_data_is_confidential_free():
    """The prototype provider returns stable demo data and no real-source dependency."""
    response = asyncio.run(SyntheticReportingData().async_invoke({}, {}))

    assert response["mode"] == "SYNTHETIC_DEMO_ONLY"
    assert response["confidential_data_used"] is False
    assert response["reporting_run_id"] == "DEMO-20260831-001"
    assert len(response["source_records"]) == 8
    assert {item["expected"] for item in response["expected_controls"]} == {"PASS"}