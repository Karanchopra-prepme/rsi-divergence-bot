"""
REDESIGNED DIVERGENCE DETECTOR - Human-Like Visual Pattern Matching
NOW 100% RAILWAY COMPATIBLE (NO SCIPY REQUIRED)
"""

import pandas as pd
import numpy as np
from datetime import datetime


# ----------------------------
# REPLACEMENT FOR SCIPY argrelextrema
# ----------------------------
def argrelextrema(data, comparator, order=3):
    """
    Pure NumPy alternative to SciPy's argrelextrema.
    Finds local extrema by comparing points to neighbors.
    """
    idxs = []
    ln = len(data)

    for i in range(order, ln - order):
        left = data[i - order:i]
        right = data[i + 1:i + 1 + order]

        if comparator(data[i], max(left)) and comparator(data[i], max(right)):
            idxs.append(i)

    return np.array(idxs)


class HumanLikeDivergenceDetector:

    def __init__(self,
                 min_peak_prominence=2.0,
                 min_rsi_divergence=5.0,
                 lookback_candles=50,
                 require_confirmation=True,
                 min_time_between_peaks=5):

        self.min_peak_prominence = min_peak_prominence
        self.min_rsi_divergence = min_rsi_divergence
        self.lookback_candles = lookback_candles
        self.require_confirmation = require_confirmation
        self.min_time_between_peaks = min_time_between_peaks

    # ---------------------------------------------------------
    # PROMINENT PEAK / TROUGH FINDERS (NO SCIPY ANYMORE)
    # ---------------------------------------------------------
    def find_prominent_peaks(self, df, column='high'):
        if len(df) < 20:
            return []

        data = df[column].values
        peaks = argrelextrema(data, lambda x, y: x > y, order=3)

        prominent = []
        for idx in peaks:
            if idx < 5 or idx >= len(data) - 5:
                continue

            peak_val = data[idx]
            left_min = np.min(data[max(0, idx - 10):idx])
            right_min = np.min(data[idx + 1:min(len(data), idx + 10)])

            left_p = ((peak_val - left_min) / left_min * 100) if left_min > 0 else 0
            right_p = ((peak_val - right_min) / right_min * 100) if right_min > 0 else 0

            if left_p >= self.min_peak_prominence and right_p >= self.min_peak_prominence:
                prominent.append({
                    "index": idx,
                    "value": peak_val,
                    "prominence": min(left_p, right_p)
                })

        return prominent

    def find_prominent_troughs(self, df, column='low'):
        if len(df) < 20:
            return []

        data = df[column].values
        troughs = argrelextrema(data, lambda x, y: x < y, order=3)

        prominent = []
        for idx in troughs:
            if idx < 5 or idx >= len(data) - 5:
                continue

            low_val = data[idx]
            left_max = np.max(data[max(0, idx - 10):idx])
            right_max = np.max(data[idx + 1:min(len(data), idx + 10)])

            left_p = ((left_max - low_val) / low_val * 100) if low_val > 0 else 0
            right_p = ((right_max - low_val) / low_val * 100) if low_val > 0 else 0

            if left_p >= self.min_peak_prominence and right_p >= self.min_peak_prominence:
                prominent.append({
                    "index": idx,
                    "value": low_val,
                    "prominence": min(left_p, right_p)
                })

        return prominent

    # ---------------------------------------------------------
    # REST OF YOUR LOGIC (UNCHANGED)
    # ---------------------------------------------------------

    def get_rsi_at_peaks(self, df, price_peaks):
        r = []
        for p in price_peaks:
            idx = p["index"]
            r.append({
                "index": idx,
                "price": p["value"],
                "rsi": df["rsi"].iloc[idx],
                "prominence": p["prominence"]
            })
        return r

    def validate_divergence_alignment(self, peak1, peak2, div_type):
        td = abs(peak2["index"] - peak1["index"])
        if td < self.min_time_between_peaks:
            return False, "Peaks too close"
        if td > self.lookback_candles:
            return False, "Peaks too far"

        price_pct = abs((peak2["price"] - peak1["price"]) / peak1["price"] * 100)
        if price_pct < 0.5:
            return False, "Price difference too small"

        rsi_diff = abs(peak2["rsi"] - peak1["rsi"])
        if rsi_diff < self.min_rsi_divergence:
            return False, "RSI difference too small"

        if div_type == "BEARISH":
            if not (peak2["price"] > peak1["price"] and peak2["rsi"] < peak1["rsi"]):
                return False, "Not bearish divergence"

        if div_type == "BULLISH":
            if not (peak2["price"] < peak1["price"] and peak2["rsi"] > peak1["rsi"]):
                return False, "Not bullish divergence"

        return True, "Valid"

    def check_price_action_confirms(self, df, div, idx):
        if not self.require_confirmation:
            return True, "Skip"

        if idx + 3 >= len(df):
            return False, "Not enough candles"

        now = df["close"].iloc[idx]
        next_prices = df["close"].iloc[idx+1:idx+4]

        if div == "BEARISH":
            if sum(1 for p in next_prices if p < now) < 2:
                return False, "Price not falling"

        if div == "BULLISH":
            if sum(1 for p in next_prices if p > now) < 2:
                return False, "Price not rising"

        return True, "Confirmed"

    # ---------------------------------------------------------
    # BEARISH / BULLISH DETECTORS (UNCHANGED)
    # ---------------------------------------------------------

    def detect_bearish_divergence(self, df):
        if df is None or len(df) < 30:
            return None

        peaks = self.find_prominent_peaks(df)
        if len(peaks) < 2:
            return None

        peaks_rsi = self.get_rsi_at_peaks(df, peaks)
        p1, p2 = peaks_rsi[-2], peaks_rsi[-1]

        valid, reason = self.validate_divergence_alignment(p1, p2, "BEARISH")
        if not valid:
            return None

        confirmed, c_reason = self.check_price_action_confirms(df, "BEARISH", p2["index"])
        if not confirmed:
            return None

        price_pct = (p2["price"] - p1["price"]) / p1["price"] * 100
        rsi_ch = p1["rsi"] - p2["rsi"]

        quality = self._calculate_quality_score(
            abs(price_pct), abs(rsi_ch),
            min(p1["prominence"], p2["prominence"]),
            confirmed
        )

        if quality < 60:
            return None

        return {
            "type": "BEARISH",
            "price1": float(p1["price"]),
            "price2": float(p2["price"]),
            "rsi1": float(p1["rsi"]),
            "rsi2": float(p2["rsi"]),
            "price_change_pct": round(price_pct, 2),
            "rsi_change": round(rsi_ch, 2),
            "current_price": float(df["close"].iloc[-1]),
            "current_rsi": float(df["rsi"].iloc[-1]),
            "timestamp": df["timestamp"].iloc[-1],
            "quality": quality,
            "quality_label": self._get_quality_label(quality),
            "confirmed": confirmed,
            "explanation": reason
        }

    def detect_bullish_divergence(self, df):
        if df is None or len(df) < 30:
            return None

        troughs = self.find_prominent_troughs(df)
        if len(troughs) < 2:
            return None

        with_rsi = self.get_rsi_at_peaks(df, troughs)
        t1, t2 = with_rsi[-2], with_rsi[-1]

        valid, reason = self.validate_divergence_alignment(t1, t2, "BULLISH")
        if not valid:
            return None

        confirmed, c_reason = self.check_price_action_confirms(df, "BULLISH", t2["index"])
        if not confirmed:
            return None

        price_pct = (t1["price"] - t2["price"]) / t1["price"] * 100
        rsi_ch = t2["rsi"] - t1["rsi"]

        quality = self._calculate_quality_score(
            abs(price_pct), abs(rsi_ch),
            min(t1["prominence"], t2["prominence"]),
            confirmed
        )

        if quality < 60:
            return None

        return {
            "type": "BULLISH",
            "price1": float(t1["price"]),
            "price2": float(t2["price"]),
            "rsi1": float(t1["rsi"]),
            "rsi2": float(t2["rsi"]),
            "price_change_pct": round(abs(price_pct), 2),
            "rsi_change": round(abs(rsi_ch), 2),
            "current_price": float(df["close"].iloc[-1]),
            "current_rsi": float(df["rsi"].iloc[-1]),
            "timestamp": df["timestamp"].iloc[-1],
            "quality": quality,
            "quality_label": self._get_quality_label(quality),
            "confirmed": confirmed,
            "explanation": reason
        }

    # ---------------------------------------------------------
    # QUALITY SYSTEM
    # ---------------------------------------------------------

    def _calculate_quality_score(self, price_change_pct, rsi_change, prominence, confirmed):
        price_score = min(price_change_pct * 6, 30)
        rsi_score = min(rsi_change * 3, 30)
        prom_score = min(prominence * 4, 20)
        conf_score = 20 if confirmed else 0
        return min(price_score + rsi_score + prom_score + conf_score, 100)

    def _get_quality_label(self, q):
        if q >= 85: return "Excellent ⭐⭐⭐⭐⭐"
        if q >= 75: return "Very Good ⭐⭐⭐⭐"
        if q >= 65: return "Good ⭐⭐⭐"
        return "Fair ⭐⭐"
