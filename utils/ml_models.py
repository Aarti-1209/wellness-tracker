import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
import warnings
warnings.filterwarnings('ignore')


class WellnessPredictor:

    def __init__(self):
        self.scaler = MinMaxScaler()
        self._init_models()

    def _init_models(self):
        np.random.seed(42)
        n_samples = 1000
        X = np.random.rand(n_samples, 9)
        weights = np.array([0.20, 0.18, 0.12, -0.18, -0.10, 0.08, 0.10, 0.07, 0.13])
        base_score = X @ weights
        base_score = (base_score - base_score.min()) / (base_score.max() - base_score.min()) * 100
        base_score = np.clip(base_score + np.random.normal(0, 3, n_samples), 0, 100)
        risk_labels = np.where(base_score >= 70, 0, np.where(base_score >= 45, 1, 2))
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.reg_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.reg_model.fit(X_scaled, base_score)
        self.clf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.clf_model.fit(X_scaled, risk_labels)

    def _extract_features(self, entry: dict) -> np.ndarray:
        mood = entry.get('mood', 5) / 10.0
        sleep_h = min(entry.get('sleep_hours', 7), 12) / 12.0
        sleep_q = entry.get('sleep_quality', 7) / 10.0
        stress = (10 - entry.get('stress', 5)) / 10.0
        anxiety = (10 - entry.get('anxiety', 5)) / 10.0
        study_h = min(entry.get('study_hours', 4), 12) / 12.0
        ex_mins = min(entry.get('exercise_mins', 0), 120) / 120.0
        water = min(entry.get('water_intake', 6), 12) / 12.0
        energy = entry.get('energy', 6) / 10.0
        return np.array([[mood, sleep_h, sleep_q, stress, anxiety,
                          study_h, ex_mins, water, energy]])

    def analyze(self, entry: dict):
        X = self._extract_features(entry)
        X_scaled = self.scaler.transform(X)
        raw_score = self.reg_model.predict(X_scaled)[0]
        wellness_score = int(np.clip(raw_score, 0, 100))
        risk_idx = self.clf_model.predict(X_scaled)[0]
        risk_map = {0: "Low", 1: "Medium", 2: "High"}
        risk_level = risk_map[risk_idx]
        mental_score = self._calc_mental_score(entry)
        physical_score = self._calc_physical_score(entry)
        predictions = {
            "mental_score": mental_score,
            "physical_score": physical_score,
            "burnout_probability": self._burnout_prob(entry),
            "sleep_debt": max(0, 8 - entry.get('sleep_hours', 7))
        }
        return wellness_score, risk_level, predictions

    def _calc_mental_score(self, entry: dict) -> int:
        mood = entry.get('mood', 5) * 0.30
        stress_inv = (10 - entry.get('stress', 5)) * 0.25
        anxiety_inv = (10 - entry.get('anxiety', 5)) * 0.20
        focus = entry.get('focus', 5) * 0.15
        energy = entry.get('energy', 5) * 0.10
        raw = (mood + stress_inv + anxiety_inv + focus + energy) / 10.0 * 100
        return int(np.clip(raw, 0, 100))

    def _calc_physical_score(self, entry: dict) -> int:
        sleep = min(entry.get('sleep_hours', 7) / 8.0, 1.0) * 30
        sleep_q = entry.get('sleep_quality', 7) / 10.0 * 20
        ex = min(entry.get('exercise_mins', 0) / 45.0, 1.0) * 30
        water = min(entry.get('water_intake', 6) / 8.0, 1.0) * 20
        raw = sleep + sleep_q + ex + water
        return int(np.clip(raw, 0, 100))

    def _burnout_prob(self, entry: dict) -> float:
        stress = entry.get('stress', 5)
        sleep = entry.get('sleep_hours', 7)
        study = entry.get('study_hours', 4)
        mood = entry.get('mood', 5)
        prob = 0.0
        if stress >= 8: prob += 0.35
        elif stress >= 6: prob += 0.15
        if sleep <= 5: prob += 0.25
        elif sleep <= 6: prob += 0.10
        if study >= 10: prob += 0.15
        elif study >= 8: prob += 0.05
        if mood <= 3: prob += 0.25
        elif mood <= 5: prob += 0.10
        return min(prob, 1.0)

    def batch_analyze(self, history: list):
        if not history:
            return [], [], []
        features, scores, labels = [], [], []
        for entry in history:
            score, risk, _ = self.analyze(entry)
            features.append(self._extract_features(entry)[0])
            scores.append(score)
            labels.append(risk)
        return features, scores, labels