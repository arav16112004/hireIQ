"""Process WebGazer.js gaze data and compute attention metrics.

analyze_gaze(gaze_data) -> returns attention metrics such as percent_on_screen, reading_likelihood
"""
from typing import Dict, Any


class WebGazerService:
    def __init__(self):
        pass

    def analyze_gaze(self, gaze_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple heuristic-based analysis for local testing.

        Expected gaze_data format (example):
        {
            "samples": [ {"x": 100, "y": 200, "t": 0.01}, ... ],
            "viewport": {"width": 1280, "height": 720}
        }
        """
        samples = gaze_data.get("samples", [])
        viewport = gaze_data.get("viewport", {})
        w = viewport.get("width", 1280)
        h = viewport.get("height", 720)
        if not samples:
            return {"samples": 0, "percent_on_screen": 0.0, "reading_likelihood": 0.0}

        on_screen = 0
        center_hits = 0
        for s in samples:
            x = s.get("x", -1)
            y = s.get("y", -1)
            if 0 <= x <= w and 0 <= y <= h:
                on_screen += 1
                # center region heuristic
                if w * 0.25 <= x <= w * 0.75 and h * 0.25 <= y <= h * 0.75:
                    center_hits += 1
        percent_on_screen = on_screen / len(samples) * 100.0
        reading_likelihood = center_hits / len(samples)
        return {
            "samples": len(samples),
            "percent_on_screen": percent_on_screen,
            "reading_likelihood": reading_likelihood,
        }
