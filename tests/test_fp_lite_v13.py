
import unittest
from dae_p1.M13_fp_lite import QuantileCalculator, ProofCardGenerator, ProfileManager

class TestProofCardV13(unittest.TestCase):
    
    def test_p50_p95_simulation_1(self):
        # Simulation 1: Wi-Fi 7/8 Install Window - Tail Latency
        # RTT: [20, 22, 21, 23, 24, 25, 26, 28, 30, 40, 80, 120] (N=12)
        rtt = [20, 22, 21, 23, 24, 25, 26, 28, 30, 40, 80, 120]
        
        qc = QuantileCalculator()
        # p50: N=12, rank=ceil(6) = 6. sorted[5] -> 25
        p50 = qc.calculate(rtt, 50)
        self.assertEqual(p50, 25)
        
        # p95: N=12, rank=ceil(0.95*12)=ceil(11.4)=12. sorted[11] -> 120
        p95 = qc.calculate(rtt, 95)
        self.assertEqual(p95, 120)

    def test_p50_p95_simulation_2(self):
        # Simulation 2: FWA Congestion
        # N=20. [35, 38, 40, 42, 45, 46, 47, 48, 50, 52, 55, 60, 65, 70, 80, 90, 120, 150, 180, 210]
        rtt = [35, 38, 40, 42, 45, 46, 47, 48, 50, 52, 55, 60, 65, 70, 80, 90, 120, 150, 180, 210]
        
        qc = QuantileCalculator()
        
        # p50: N=20, rank=ceil(10)=10. val=52
        p50 = qc.calculate(rtt, 50)
        self.assertEqual(p50, 52)
        
        # p95: N=20, rank=ceil(19)=19. val is 19th -> index 18? No, rank is 1-based index.
        # rank=ceil(0.95*20)=19.
        # sorted data: ... 180, 210
        # index 18 (19th element) is 180.
        p95 = qc.calculate(rtt, 95)
        self.assertEqual(p95, 180)

    def test_verdict_logic_wifi(self):
        # Using Sim 1 data, Profile WIFI78_INSTALL_ACCEPT
        # Metric: rtt point=120 (p95)
        # Threshold: 80ms
        
        gen = ProofCardGenerator()
        
        # Mocking window data. Generator extracts 'latency_ms' or 'rtt'.
        data = [{"rtt": x} for x in [20, 22, 21, 23, 24, 25, 26, 28, 30, 40, 80, 120]]
        
        card = gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-SIM-1")
        
        self.assertEqual(card["verdict"], "NOT_READY")
        self.assertIn("P95_RTT_TOO_HIGH", card["reason_code"])
        self.assertEqual(card["sample_count"], 12)
        
        # Verify p95 output structure
        p95_rtt = next((x for x in card["p95"] if x["name"] == "rtt_ms_p95"), None)
        self.assertIsNotNone(p95_rtt)
        self.assertEqual(p95_rtt["value"], 120)

    def test_verdict_logic_insufficient(self):
        gen = ProofCardGenerator()
        data = [{"rtt": 10}] * 5 # Only 5 samples
        
        card = gen.generate(data, "WIFI78_INSTALL_ACCEPT", "W-SMALL")
        self.assertEqual(card["verdict"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("INSUFFICIENT_SAMPLES", card["reason_code"])

if __name__ == '__main__':
    unittest.main()
