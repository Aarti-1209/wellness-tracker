class RecommendationEngine:

    def get_recommendations(self, entry, wellness_score, risk_level):
        recs = []
        mood = entry.get('mood', 5)
        stress = entry.get('stress', 5)
        anxiety = entry.get('anxiety', 5)
        sleep_h = entry.get('sleep_hours', 7)
        sleep_q = entry.get('sleep_quality', 7)
        study_h = entry.get('study_hours', 4)
        breaks = entry.get('breaks_taken', 3)
        ex_mins = entry.get('exercise_mins', 0)
        water = entry.get('water_intake', 6)
        meals = entry.get('meals_proper', 'All meals')
        focus = entry.get('focus', 5)
        energy = entry.get('energy', 5)

        if stress >= 8:
            recs.append({"type": "alert", "category": "Stress",
                "message": "Very high stress! Try box breathing 4-4-4-4 pattern."})
        if sleep_h < 5:
            recs.append({"type": "alert", "category": "Sleep",
                "message": f"Critical sleep deprivation {sleep_h}h! Prioritize sleep tonight."})
        if mood <= 3:
            recs.append({"type": "alert", "category": "Mental Health",
                "message": "Very low mood. Please reach out to a friend or counselor."})
        if anxiety >= 8:
            recs.append({"type": "alert", "category": "Anxiety",
                "message": "High anxiety. Name 5 things you see, 4 you feel, 3 you hear."})
        if 5 <= sleep_h < 7:
            recs.append({"type": "tip", "category": "Sleep",
                "message": f"You slept {sleep_h}h. Aim for 7-9 hours every night."})
        if sleep_q <= 4:
            recs.append({"type": "tip", "category": "Sleep Quality",
                "message": "Poor sleep quality. Avoid screens 1hr before bed."})
        if study_h >= 8 and breaks < 3:
            recs.append({"type": "tip", "category": "Study Habits",
                "message": f"Studied {study_h}h with only {breaks} breaks. Use Pomodoro technique."})
        if study_h > 12:
            recs.append({"type": "alert", "category": "Overwork",
                "message": "Over-studying! Beyond 12 hours retention drops sharply."})
        if not entry.get('exercise_done', False):
            recs.append({"type": "tip", "category": "Physical Activity",
                "message": "No exercise today! Even a 15-min walk improves focus."})
        if water < 6:
            recs.append({"type": "tip", "category": "Hydration",
                "message": f"Only {water} glasses today. Aim for 8+ glasses daily."})
        if meals in ["Skipped 1", "Skipped 2+"]:
            recs.append({"type": "tip", "category": "Nutrition",
                "message": "Skipped meals detected. Irregular eating affects mood and focus."})
        if energy <= 3:
            recs.append({"type": "tip", "category": "Energy",
                "message": "Very low energy. A 10-20 min power nap can help."})
        if wellness_score >= 80:
            recs.append({"type": "tip", "category": "Great Job!",
                "message": "Excellent wellness score! Keep this momentum going!"})
        if not recs:
            recs.append({"type": "tip", "category": "General",
                "message": "Solid day! Keep maintaining sleep and daily movement."})
        return recs[:7]