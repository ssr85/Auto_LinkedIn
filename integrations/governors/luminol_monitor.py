import time
from typing import Dict, List
from luminol.anomaly_detector import AnomalyDetector
from utils.logger import log

class APIAnomalyMonitor:
    """
    Monitors outbound API calls (LinkedIn, Trello) for anomalies using Luminol.
    Specifically tracks HTTP 429 (Rate Limit) frequency to detect bot-suspicion 
    or aggressive throttling.
    """
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        # ts_data: {timestamp: count}
        self.ts_data: Dict[int, int] = {}
        self._halt_signal = False
        log.info("--- LUMINOL: API Anomaly Monitor Initialized ---")

    def record_429(self, source: str):
        """Records a 429 error and evaluates for anomalies."""
        now = int(time.time())
        # Aggregate by minute for Luminol
        minute_ts = (now // 60) * 60
        self.ts_data[minute_ts] = self.ts_data.get(minute_ts, 0) + 1
        
        # Cleanup data older than 2 hours
        cutoff = now - 7200
        self.ts_data = {ts: val for ts, val in self.ts_data.items() if ts > cutoff}
        
        # Only analyze if we have enough data (at least 3 data points)
        if len(self.ts_data) >= 3:
            result = self._analyze()
            if result['is_anomaly']:
                log.warning(f"🛡️ LUMINOL ANOMALY DETECTED from {source}! Score: {result['anomaly_score']}")
                self._halt_signal = True
            return result
        return {"is_anomaly": False, "anomaly_score": 0.0}

    def _analyze(self) -> Dict:
        """Runs the Luminol anomaly detection."""
        try:
            detector = AnomalyDetector(self.ts_data)
            anomalies = detector.get_anomalies()
            
            max_score = 0
            if anomalies:
                max_score = max([anomaly.anomaly_score for anomaly in anomalies])
            
            return {
                "anomaly_score": max_score,
                "is_anomaly": max_score > self.threshold,
                "count": len(anomalies)
            }
        except Exception as e:
            log.error(f"Luminol analysis failed: {str(e)}")
            return {"is_anomaly": False, "anomaly_score": 0.0}

    def should_halt(self) -> bool:
        """Returns True if an anomaly has been detected that requires a shutdown."""
        return self._halt_signal

    def reset_halt(self):
        """Resets the halt signal manually (e.g. after human intervention)."""
        self._halt_signal = False
        log.info("--- LUMINOL: Anomaly halt signal reset ---")

class LinkedInBotSuspicionError(Exception):
    """Raised when Luminol detects dangerous 429/CAPTCHA spikes."""
    pass

# Shared instance for use across the application (LinkedIn and Trello)
api_monitor = APIAnomalyMonitor()
