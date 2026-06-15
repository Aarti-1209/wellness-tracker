import json
import os
import numpy as np
from datetime import datetime, timedelta
import random


class DataManager:

    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump({}, f)

    def _load(self) -> dict:
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict):
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def save_entry(self, student_id: str, entry: dict):
        data = self._load()
        if student_id not in data:
            data[student_id] = []
        existing_dates = [e.get('date') for e in data[student_id]]
        if entry.get('date') in existing_dates:
            idx = existing_dates.index(entry['date'])
            data[student_id][idx] = entry
        else:
            data[student_id].append(entry)
        self._save(data)

    def get_history(self, student_id: str) -> list:
        data = self._load()
        return data.get(student_id, [])

    def clear_data(self, student_id: str):
        data = self._load()
        if student_id in data:
            del data[student_id]
        self._save(data)

    def generate_sample_data(self, student_id: str, days: int = 30):
        self.clear_data(student_id)
        random.seed(42)
        base_mood = 6.5
        base_stress = 5.0
        entries = []
        bedtime_options = ["Before 10PM", "10-11PM", "11PM-12AM", "After 12AM"]
        meal_options = ["All meals", "Skipped 1", "Skipped 2+"]
        deadline_options = ["None", "1-2 days", "This week"]
        exercise_types = ["Walking", "Running", "Yoga", "Gym", "Sports", "Cycling"]

        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
            day_of_week = (datetime.now() - timedelta(days=days - i)).weekday()
            weekend_bonus = 1.5 if day_of_week >= 5 else 0
            midweek_stress = 1.5 if day_of_week in [2, 3] else 0
            mood = max(1, min(10, base_mood + random.gauss(0, 1.2) + weekend_bonus))
            stress = max(1, min(10, base_stress + random.gauss(0, 1.5) + midweek_stress - weekend_bonus))
            anxiety = max(1, min(10, stress * 0.8 + random.gauss(0, 1)))
            focus = max(1, min(10, mood * 0.7 + (10 - stress) * 0.3 + random.gauss(0, 0.8)))
            energy = max(1, min(10, mood * 0.5 + 3 + random.gauss(0, 1)))
            sleep_hours = max(4, min(10, 7 + random.gauss(0, 1.2)))
            sleep_quality = max(1, min(10, sleep_hours - 1 + random.gauss(0, 1)))
            bedtime = bedtime_options[min(3, max(0, int(2 + random.gauss(0, 1))))]
            study_hours = max(0, min(14, 5 + random.gauss(0, 2)))
            breaks = max(0, int(study_hours * 0.6 + random.gauss(0, 1)))
            productivity = max(1, min(10, focus * 0.6 + (10 - stress) * 0.4 + random.gauss(0, 0.5)))
            exercise_done = random.random() > 0.35
            exercise_mins = int(max(0, random.gauss(35, 15))) if exercise_done else 0
            exercise_type = random.choice(exercise_types) if exercise_done else "None"
            water = max(2, min(15, random.gauss(7, 2)))
            meals = random.choices(meal_options, weights=[0.6, 0.3, 0.1])[0]
            deadline = random.choices(deadline_options, weights=[0.5, 0.25, 0.25])[0]
            base_mood = max(2, min(9, base_mood + random.gauss(0, 0.2)))
            base_stress = max(2, min(9, base_stress + random.gauss(0, 0.2)))

            entry = {
                "date": date,
                "time": f"{random.randint(18,22):02d}:{random.randint(0,59):02d}",
                "mood": round(mood, 1),
                "stress": round(stress, 1),
                "anxiety": round(anxiety, 1),
                "focus": round(focus, 1),
                "energy": round(energy, 1),
                "sleep_hours": round(sleep_hours, 1),
                "sleep_quality": round(sleep_quality, 1),
                "bedtime": bedtime,
                "study_hours": round(study_hours, 1),
                "breaks_taken": breaks,
                "productivity": round(productivity, 1),
                "deadlines_stress": deadline,
                "exercise_done": exercise_done,
                "exercise_mins": exercise_mins,
                "exercise_type": exercise_type,
                "water_intake": round(water, 1),
                "meals_proper": meals,
                "journal": ""
            }
            entries.append(entry)

        data = self._load()
        data[student_id] = entries
        self._save(data)