import unittest
from dae_p1.M13_fp_lite import ProofCardGenerator, ProfileManager

class TestProofCardV13(unittest.TestCase):
    def setUp(self):
        self.generator = ProofCardGenerator()

    def test_sim1_wifi78_install_accept(self):
        """
        8.1 模擬 1：Wi‑Fi 7/8 安裝窗 — 尾端延遲爆掉
        樣本（rtt_ms，N=12）：[20, 22, 21, 23, 24, 25, 26, 28, 30, 40, 80, 120]
        計算（Nearest-Rank）：p50=25ms；p95=120ms
        裁決：NOT_READY（原因：P95_RTT_TOO_HIGH）
        """
        rtt_values = [20, 22, 21, 23, 24, 25, 26, 28, 30, 40, 80, 120]
        # Construct window data (list of dictionaries)
        window_data = [{"rtt": v} for v in rtt_values]
        
        card = self.generator.generate(window_data, "WIFI78_INSTALL_ACCEPT", "W-SIM-1")
        
        # Verify verdict
        self.assertEqual(card["verdict"], "NOT_READY")
        self.assertIn("P95_RTT_TOO_HIGH", card["reason_code"])
        
        # Verify p50/p95
        # M13 uses NearestRank.
        # N=12. 
        # p50: rank = ceil(0.5 * 12) = 6. Sorted idx 5. sorted: 20 21 22 23 24 25 ... -> 25. Correct.
        # p95: rank = ceil(0.95 * 12) = ceil(11.4) = 12. Sorted idx 11 (last). -> 120. Correct.
        
        p50_rtt = next((item["value"] for item in card["p50"] if item["name"] == "rtt_ms_p50"), None)
        p95_rtt = next((item["value"] for item in card["p95"] if item["name"] == "rtt_ms_p95"), None)
        
        self.assertEqual(p50_rtt, 25)
        self.assertEqual(p95_rtt, 120)

    def test_sim2_fwa_congestion(self):
        """
        8.2 模擬 2：FWA 晚高峰 — 尾端 RTT 超門檻
        樣本（rtt_ms，N=20）
        計算（Nearest-Rank）：p50=52ms；p95=180ms
        裁決：NOT_READY（原因：TAIL_RTT_TOO_HIGH）
        """
        rtt_values = [35, 38, 40, 42, 45, 46, 47, 48, 50, 52, 55, 60, 65, 70, 80, 90, 120, 150, 180, 210]
        window_data = [{"rtt": v} for v in rtt_values]
        
        card = self.generator.generate(window_data, "FWA_CONGESTION_SUSPECT", "W-SIM-2")
        
        self.assertEqual(card["verdict"], "NOT_READY")
        self.assertIn("TAIL_RTT_TOO_HIGH", card["reason_code"])
        
        p50_rtt = next((item["value"] for item in card["p50"] if item["name"] == "rtt_ms_p50"), None)
        p95_rtt = next((item["value"] for item in card["p95"] if item["name"] == "rtt_ms_p95"), None)
        
        self.assertEqual(p50_rtt, 52)
        self.assertEqual(p95_rtt, 180)

    def test_sim3_cable_upstream(self):
        """
        8.3 模擬 3：Cable 上行間歇性 — 尾端上行延遲尖峰
        樣本（us_rtt_ms，N=40）
        計算（Nearest-Rank）：p50=35ms；p95=200ms
        裁決：NOT_READY（原因：TAIL_US_RTT_TOO_HIGH）
        """
        us_rtt_values = [20, 22, 21, 25, 24, 23, 26, 28, 30, 29, 35, 40, 45, 50, 55, 60, 80, 120, 200, 300, 
                         25, 24, 23, 22, 21, 26, 28, 30, 29, 35, 40, 45, 50, 60, 70, 90, 110, 140, 180, 220]
        
        # Note: M13 maps "us_rtt" key to "us_rtt_ms"
        window_data = [{"us_rtt": v} for v in us_rtt_values]
        
        card = self.generator.generate(window_data, "CABLE_UPSTREAM_INTERMITTENT", "W-SIM-3")
        
        self.assertEqual(card["verdict"], "NOT_READY")
        self.assertIn("TAIL_US_RTT_TOO_HIGH", card["reason_code"])
        
        p50_val = next((item["value"] for item in card["p50"] if item["name"] == "us_rtt_ms_p50"), None)
        p95_val = next((item["value"] for item in card["p95"] if item["name"] == "us_rtt_ms_p95"), None)
        
        self.assertEqual(p50_val, 35)
        self.assertEqual(p95_val, 200)

if __name__ == '__main__':
    unittest.main()
