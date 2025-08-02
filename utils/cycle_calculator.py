from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from schemas.cycle import HormoneLevel, CyclePrediction, CycleStats, MoodType, PhysicalSymptom
import statistics


class MenstrualCycleCalculator:
    def __init__(self):
        self.default_cycle_length = 28
        self.default_period_length = 5
        self.luteal_phase_length = 14  # Generally consistent

    def calculate_cycle_stats(self, entries: List[dict]) -> CycleStats:
        """Calculate comprehensive cycle statistics"""
        period_starts = self._get_period_starts(entries)

        if len(period_starts) < 2:
            return CycleStats(
                total_cycles_tracked=len(period_starts),
                last_period_start=period_starts[0] if period_starts else None
            )

        # Calculate cycle lengths
        cycle_lengths = []
        for i in range(1, len(period_starts)):
            cycle_length = (period_starts[i] - period_starts[i - 1]).days
            if 21 <= cycle_length <= 35:  # Valid cycle range
                cycle_lengths.append(cycle_length)

        # Calculate period lengths
        period_lengths = []
        for start_date in period_starts:
            period_length = self._calculate_period_length(entries, start_date)
            if period_length:
                period_lengths.append(period_length)

        avg_cycle_length = statistics.mean(cycle_lengths) if cycle_lengths else self.default_cycle_length
        avg_period_length = statistics.mean(period_lengths) if period_lengths else self.default_period_length

        last_period = period_starts[-1] if period_starts else None

        # Predictions
        next_period = None
        next_ovulation = None
        current_cycle_day = None
        current_phase = None

        if last_period:
            next_period = last_period + timedelta(days=int(avg_cycle_length))
            next_ovulation = last_period + timedelta(days=int(avg_cycle_length - self.luteal_phase_length))
            current_cycle_day = (date.today() - last_period).days + 1
            current_phase = self._get_current_phase(current_cycle_day, avg_cycle_length)

        return CycleStats(
            average_cycle_length=avg_cycle_length,
            average_period_length=avg_period_length,
            last_period_start=last_period,
            next_predicted_period=next_period,
            next_predicted_ovulation=next_ovulation,
            current_cycle_day=current_cycle_day,
            current_phase=current_phase,
            total_cycles_tracked=len(period_starts)
        )

    def generate_predictions(self, entries: List[dict], days_ahead: int = 30) -> List[CyclePrediction]:
        """Generate cycle predictions for the next X days"""
        stats = self.calculate_cycle_stats(entries)
        predictions = []

        if not stats.last_period_start:
            return predictions

        cycle_length = stats.average_cycle_length or self.default_cycle_length

        for i in range(days_ahead):
            prediction_date = date.today() + timedelta(days=i)
            days_since_last_period = (prediction_date - stats.last_period_start).days
            cycle_day = (days_since_last_period % int(cycle_length)) + 1

            phase = self._get_current_phase(cycle_day, cycle_length)
            hormone_levels = self._predict_hormone_levels(cycle_day, cycle_length)
            predicted_mood = self._predict_mood(phase, entries)
            predicted_symptoms = self._predict_symptoms(phase, entries)
            fertility_status = self._predict_fertility(cycle_day, cycle_length)

            predictions.append(CyclePrediction(
                date=prediction_date,
                cycle_day=cycle_day,
                phase=phase,
                predicted_mood=predicted_mood,
                predicted_symptoms=predicted_symptoms,
                hormone_levels=hormone_levels,
                fertility_status=fertility_status
            ))

        return predictions

    def _get_period_starts(self, entries: List[dict]) -> List[date]:
        """Extract period start dates from entries"""
        period_starts = []
        entries_sorted = sorted(entries, key=lambda x: x['date'])

        in_period = False
        for entry in entries_sorted:
            if entry['is_period_day'] and not in_period:
                period_starts.append(entry['date'])
                in_period = True
            elif not entry['is_period_day']:
                in_period = False

        return period_starts

    def _calculate_period_length(self, entries: List[dict], start_date: date) -> Optional[int]:
        """Calculate period length from a start date"""
        period_days = 0
        current_date = start_date

        for entry in sorted(entries, key=lambda x: x['date']):
            if entry['date'] >= start_date and entry['is_period_day']:
                if entry['date'] == current_date:
                    period_days += 1
                    current_date += timedelta(days=1)
                else:
                    break
            elif entry['date'] > start_date:
                break

        return period_days if period_days > 0 else None

    def _get_current_phase(self, cycle_day: int, cycle_length: float) -> str:
        """Determine current menstrual cycle phase"""
        if cycle_day <= 5:
            return "menstrual"
        elif cycle_day <= cycle_length - self.luteal_phase_length:
            return "follicular"
        elif abs(cycle_day - (cycle_length - self.luteal_phase_length)) <= 2:
            return "ovulation"
        else:
            return "luteal"

    def _predict_hormone_levels(self, cycle_day: int, cycle_length: float) -> HormoneLevel:
        """Predict hormone levels based on cycle day"""
        phase = self._get_current_phase(cycle_day, cycle_length)

        if phase == "menstrual":
            return HormoneLevel(
                estrogen_level="low",
                progesterone_level="low",
                testosterone_level="medium"
            )
        elif phase == "follicular":
            return HormoneLevel(
                estrogen_level="medium" if cycle_day < 10 else "high",
                progesterone_level="low",
                testosterone_level="medium"
            )
        elif phase == "ovulation":
            return HormoneLevel(
                estrogen_level="high",
                progesterone_level="low",
                testosterone_level="high"
            )
        else:  # luteal
            return HormoneLevel(
                estrogen_level="medium",
                progesterone_level="high",
                testosterone_level="low"
            )

    def _predict_mood(self, phase: str, entries: List[dict]) -> List[str]:
        """Predict mood based on phase and historical data"""
        phase_moods = {
            "menstrual": ["tired", "emotional", "irritable"],
            "follicular": ["energetic", "happy", "calm"],
            "ovulation": ["happy", "energetic", "confident"],
            "luteal": ["anxious", "irritable", "sad"]
        }

        # Get historical mood patterns for this phase
        historical_moods = []
        for entry in entries:
            if entry.get('moods'):
                historical_moods.extend(entry['moods'])

        # Combine typical phase moods with personal patterns
        predicted = phase_moods.get(phase, [])
        if historical_moods:
            common_moods = [mood for mood in set(historical_moods)
                            if historical_moods.count(mood) > len(entries) * 0.1]
            predicted.extend(common_moods)

        return list(set(predicted))[:3]  # Return top 3 unique predictions

    def _predict_symptoms(self, phase: str, entries: List[dict]) -> List[str]:
        """Predict physical symptoms based on phase"""
        phase_symptoms = {
            "menstrual": ["cramps", "bloating", "back_pain"],
            "follicular": [],
            "ovulation": ["breast_tenderness"],
            "luteal": ["bloating", "headache", "food_cravings", "acne"]
        }

        return phase_symptoms.get(phase, [])

    def _predict_fertility(self, cycle_day: int, cycle_length: float) -> str:
        """Predict fertility status"""
        ovulation_day = cycle_length - self.luteal_phase_length

        if abs(cycle_day - ovulation_day) <= 1:
            return "high"
        elif abs(cycle_day - ovulation_day) <= 3:
            return "medium"
        else:
            return "low"

    def analyze_mood_patterns(self, entries: List[dict]) -> Dict[str, List[str]]:
        """Analyze mood patterns by cycle phase"""
        phase_moods = {"menstrual": [], "follicular": [], "ovulation": [], "luteal": []}

        for entry in entries:
            if entry.get('moods'):
                # This is simplified - in reality you'd need to determine phase for each entry
                phase = "menstrual"  # You'd calculate this based on the entry date
                phase_moods[phase].extend(entry['moods'])

        return {phase: list(set(moods)) for phase, moods in phase_moods.items()}

    def analyze_symptom_patterns(self, entries: List[dict]) -> Dict[str, List[str]]:
        """Analyze symptom patterns by cycle phase"""
        phase_symptoms = {"menstrual": [], "follicular": [], "ovulation": [], "luteal": []}

        for entry in entries:
            if entry.get('physical_symptoms'):
                phase = "menstrual"  # You'd calculate this based on the entry date
                phase_symptoms[phase].extend(entry['physical_symptoms'])

        return {phase: list(set(symptoms)) for phase, symptoms in phase_symptoms.items()}

