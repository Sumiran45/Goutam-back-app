from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from collections import Counter, defaultdict
from schemas.symptoms import (
    PredictedSymptom, Suggestion, PredictionResponse, 
    SuggestionResponse, SymptomResponse
)
import statistics

class SymptomPredictor:
    """Rule-based symptom prediction and suggestion system"""
    
    def __init__(self):
        self.suggestion_database = self._load_suggestion_database()
        self.cycle_patterns = {
            "early_cycle": [1, 2, 3, 4, 5],  # Days 1-5
            "mid_cycle": [6, 7, 8, 9, 10, 11, 12, 13, 14],  # Days 6-14
            "late_cycle": [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]  # Days 15-28
        }
    
    def predict_tomorrow_symptoms(self, user_symptoms: List[SymptomResponse], 
                                target_date: date) -> PredictionResponse:
        """Predict symptoms for tomorrow based on historical data"""
        
        if not user_symptoms:
            return PredictionResponse(
                date=target_date,
                predicted_symptoms=[],
                confidence_score=0.0,
                based_on_days=0
            )
        
        # Sort symptoms by date
        sorted_symptoms = sorted(user_symptoms, key=lambda x: x.date)
        recent_symptoms = sorted_symptoms[-7:]  # Last 7 days
        
        predictions = []
        
        # Pattern-based predictions
        predictions.extend(self._predict_by_patterns(recent_symptoms, target_date))
        
        # Cycle-based predictions
        predictions.extend(self._predict_by_cycle_phase(recent_symptoms, target_date))
        
        # Sequence-based predictions
        predictions.extend(self._predict_by_sequence(recent_symptoms, target_date))
        
        # Remove duplicates and calculate overall confidence
        unique_predictions = self._merge_predictions(predictions)
        confidence_score = self._calculate_confidence(recent_symptoms, unique_predictions)
        
        return PredictionResponse(
            date=target_date,
            predicted_symptoms=unique_predictions,
            confidence_score=confidence_score,
            based_on_days=len(recent_symptoms)
        )
    
    def generate_suggestions(self, current_symptoms: SymptomResponse, 
                           predicted_symptoms: List[PredictedSymptom]) -> SuggestionResponse:
        """Generate health suggestions based on current and predicted symptoms"""
        
        suggestions = []
        based_on_symptoms = []
        
        # Current symptom suggestions
        if current_symptoms:
            current_suggestions, current_based_on = self._get_current_symptom_suggestions(current_symptoms)
            suggestions.extend(current_suggestions)
            based_on_symptoms.extend(current_based_on)
        
        # Preventive suggestions for predicted symptoms
        if predicted_symptoms:
            preventive_suggestions, preventive_based_on = self._get_preventive_suggestions(predicted_symptoms)
            suggestions.extend(preventive_suggestions)
            based_on_symptoms.extend(preventive_based_on)
        
        # General wellness suggestions
        general_suggestions = self._get_general_wellness_suggestions()
        suggestions.extend(general_suggestions)
        
        # Remove duplicates and sort by priority
        unique_suggestions = self._deduplicate_suggestions(suggestions)
        
        return SuggestionResponse(
            suggestions=unique_suggestions,
            based_on_symptoms=list(set(based_on_symptoms)),
            date=current_symptoms.date if current_symptoms else date.today()
        )
    
    def _predict_by_patterns(self, recent_symptoms: List[SymptomResponse], 
                           target_date: date) -> List[PredictedSymptom]:
        """Predict based on recurring patterns"""
        predictions = []
        
        if len(recent_symptoms) < 3:
            return predictions
        
        # Analyze patterns in the last few days
        symptom_sequences = self._analyze_symptom_sequences(recent_symptoms)
        
        for symptom, pattern_strength in symptom_sequences.items():
            if pattern_strength > 0.6:  # Strong pattern
                confidence = "high" if pattern_strength > 0.8 else "medium"
                predictions.append(PredictedSymptom(
                    symptom=symptom,
                    probability=pattern_strength,
                    confidence=confidence
                ))
        
        return predictions
    
    def _predict_by_cycle_phase(self, recent_symptoms: List[SymptomResponse], 
                              target_date: date) -> List[PredictedSymptom]:
        """Predict based on menstrual cycle phase"""
        predictions = []
        
        if not recent_symptoms:
            return predictions
        
        # Estimate cycle day (simplified - you might want to integrate with cycle tracking)
        last_flow_date = self._find_last_flow_date(recent_symptoms)
        if last_flow_date:
            # Ensure both dates are datetime.date objects before subtraction
            if hasattr(target_date, 'date'):
                target_date = target_date.date()
            if hasattr(last_flow_date, 'date'):
                last_flow_date = last_flow_date.date()
                
            cycle_day = (target_date - last_flow_date).days + 1
            phase_predictions = self._get_cycle_phase_predictions(cycle_day)
            predictions.extend(phase_predictions)
        
        return predictions
    
    def _predict_by_sequence(self, recent_symptoms: List[SymptomResponse], 
                           target_date: date) -> List[PredictedSymptom]:
        """Predict based on symptom sequences"""
        predictions = []
        
        if len(recent_symptoms) < 2:
            return predictions
        
        # Look for "if X then Y" patterns
        yesterday = recent_symptoms[-1] if recent_symptoms else None
        
        if yesterday:
            sequence_predictions = self._get_sequence_predictions(yesterday)
            predictions.extend(sequence_predictions)
        
        return predictions
    
    def _get_current_symptom_suggestions(self, symptoms: SymptomResponse) -> Tuple[List[Suggestion], List[str]]:
        """Get suggestions for current symptoms"""
        suggestions = []
        based_on = []
        
        if symptoms.headache:
            suggestions.extend(self.suggestion_database["headache"])
            based_on.append("headache")
        
        if symptoms.cramps and symptoms.cramps in ["moderate", "strong"]:
            suggestions.extend(self.suggestion_database["cramps"])
            based_on.append("cramps")
        
        if symptoms.nausea:
            suggestions.extend(self.suggestion_database["nausea"])
            based_on.append("nausea")
        
        if symptoms.fatigue:
            suggestions.extend(self.suggestion_database["fatigue"])
            based_on.append("fatigue")
        
        if symptoms.mood in ["sad", "irritated", "anxious", "depressed"]:
            suggestions.extend(self.suggestion_database["mood"])
            based_on.append("mood")
        
        if symptoms.sleep_quality in ["poor", "fair"]:
            suggestions.extend(self.suggestion_database["sleep"])
            based_on.append("sleep_quality")
        
        return suggestions, based_on
    
    def _get_preventive_suggestions(self, predicted_symptoms: List[PredictedSymptom]) -> Tuple[List[Suggestion], List[str]]:
        """Get preventive suggestions for predicted symptoms"""
        suggestions = []
        based_on = []
        
        for pred in predicted_symptoms:
            if pred.probability > 0.7:  # High probability
                if pred.symptom in self.suggestion_database:
                    # Convert treatment suggestions to preventive ones
                    preventive = self._convert_to_preventive(self.suggestion_database[pred.symptom])
                    suggestions.extend(preventive)
                    based_on.append(f"predicted_{pred.symptom}")
        
        return suggestions, based_on
    
    def _load_suggestion_database(self) -> Dict[str, List[Suggestion]]:
        """Load the suggestion database"""
        return {
            "headache": [
                Suggestion(
                    category="remedy",
                    title="Stay Hydrated",
                    description="Drink plenty of water throughout the day. Dehydration is a common headache trigger.",
                    priority="high"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Rest in Dark Room",
                    description="Find a quiet, dark room to rest. Reduce screen time and bright lights.",
                    priority="high"
                ),
                Suggestion(
                    category="remedy",
                    title="Cold/Warm Compress",
                    description="Apply a cold compress to your forehead or a warm compress to your neck and shoulders.",
                    priority="medium"
                ),
                Suggestion(
                    category="medical",
                    title="Over-the-Counter Pain Relief",
                    description="Consider ibuprofen or acetaminophen as directed. Consult healthcare provider if frequent.",
                    priority="medium"
                )
            ],
            "cramps": [
                Suggestion(
                    category="remedy",
                    title="Heat Therapy",
                    description="Use a heating pad or hot water bottle on your lower abdomen or back.",
                    priority="high"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Gentle Exercise",
                    description="Try light walking, yoga, or stretching to help relieve cramps.",
                    priority="high"
                ),
                Suggestion(
                    category="remedy",
                    title="Warm Bath",
                    description="Take a warm bath with Epsom salts to relax muscles and reduce pain.",
                    priority="medium"
                ),
                Suggestion(
                    category="medical",
                    title="Anti-inflammatory Medication",
                    description="Consider ibuprofen or naproxen to reduce inflammation and pain.",
                    priority="medium"
                )
            ],
            "nausea": [
                Suggestion(
                    category="remedy",
                    title="Ginger Tea",
                    description="Drink ginger tea or chew on fresh ginger to help settle your stomach.",
                    priority="high"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Small, Frequent Meals",
                    description="Eat small, bland meals throughout the day. Avoid greasy or spicy foods.",
                    priority="high"
                ),
                Suggestion(
                    category="remedy",
                    title="Peppermint",
                    description="Try peppermint tea or aromatherapy to help reduce nausea.",
                    priority="medium"
                )
            ],
            "fatigue": [
                Suggestion(
                    category="lifestyle",
                    title="Prioritize Sleep",
                    description="Aim for 7-9 hours of quality sleep. Maintain a consistent sleep schedule.",
                    priority="high"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Iron-Rich Foods",
                    description="Include iron-rich foods like spinach, lean meats, and legumes in your diet.",
                    priority="high"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Light Exercise",
                    description="Gentle exercise can boost energy levels. Try a short walk or light stretching.",
                    priority="medium"
                )
            ],
            "mood": [
                Suggestion(
                    category="lifestyle",
                    title="Mindfulness Practice",
                    description="Try meditation, deep breathing, or mindfulness exercises for 10-15 minutes.",
                    priority="high"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Social Connection",
                    description="Reach out to friends or family. Social support can improve mood.",
                    priority="medium"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Sunlight Exposure",
                    description="Spend time outdoors or near a bright window to boost mood naturally.",
                    priority="medium"
                )
            ],
            "sleep": [
                Suggestion(
                    category="lifestyle",
                    title="Sleep Hygiene",
                    description="Create a relaxing bedtime routine. Avoid screens 1 hour before bed.",
                    priority="high"
                ),
                Suggestion(
                    category="remedy",
                    title="Herbal Tea",
                    description="Try chamomile or valerian root tea 30 minutes before bedtime.",
                    priority="medium"
                ),
                Suggestion(
                    category="lifestyle",
                    title="Cool, Dark Environment",
                    description="Keep your bedroom cool (65-68°F) and as dark as possible.",
                    priority="medium"
                )
            ]
        }
    
    def _analyze_symptom_sequences(self, symptoms: List[SymptomResponse]) -> Dict[str, float]:
        """Analyze patterns in symptom sequences"""
        patterns = defaultdict(int)
        total_days = len(symptoms)
        
        for symptom in symptoms:
            if symptom.headache:
                patterns["headache"] += 1
            if symptom.nausea:
                patterns["nausea"] += 1
            if symptom.fatigue:
                patterns["fatigue"] += 1
            if symptom.cramps and symptom.cramps != "none":
                patterns["cramps"] += 1
        
        # Convert to probabilities
        return {k: v / total_days for k, v in patterns.items()}
    
    def _find_last_flow_date(self, symptoms: List[SymptomResponse]) -> Optional[date]:
        """Find the last date with menstrual flow"""
        for symptom in reversed(symptoms):
            if symptom.flow_level and symptom.flow_level in ["light", "medium", "heavy"]:
                return symptom.date
        return None
    
    def _get_cycle_phase_predictions(self, cycle_day: int) -> List[PredictedSymptom]:
        """Get predictions based on cycle phase"""
        predictions = []
        
        if cycle_day in self.cycle_patterns["early_cycle"]:
            # Early cycle - more likely to have cramps, fatigue
            predictions.extend([
                PredictedSymptom(symptom="cramps", probability=0.7, confidence="medium"),
                PredictedSymptom(symptom="fatigue", probability=0.6, confidence="medium")
            ])
        elif cycle_day in self.cycle_patterns["late_cycle"]:
            # Late cycle - PMS symptoms
            predictions.extend([
                PredictedSymptom(symptom="mood_changes", probability=0.6, confidence="medium"),
                PredictedSymptom(symptom="headache", probability=0.5, confidence="low")
            ])
        
        return predictions
    
    def _get_sequence_predictions(self, yesterday: SymptomResponse) -> List[PredictedSymptom]:
        """Get predictions based on yesterday's symptoms"""
        predictions = []
        
        # If had strong cramps yesterday, might continue today
        if yesterday.cramps == "strong":
            predictions.append(PredictedSymptom(
                symptom="cramps", probability=0.6, confidence="medium"
            ))
        
        # If had poor sleep, likely to be fatigued
        if yesterday.sleep_quality == "poor":
            predictions.append(PredictedSymptom(
                symptom="fatigue", probability=0.8, confidence="high"
            ))
        
        return predictions
    
    def _get_general_wellness_suggestions(self) -> List[Suggestion]:
        """Get general wellness suggestions"""
        return [
            Suggestion(
                category="lifestyle",
                title="Stay Hydrated",
                description="Drink at least 8 glasses of water throughout the day.",
                priority="low"
            ),
            Suggestion(
                category="lifestyle",
                title="Balanced Nutrition",
                description="Include fruits, vegetables, and whole grains in your meals.",
                priority="low"
            )
        ]
    
    def _convert_to_preventive(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Convert treatment suggestions to preventive ones"""
        preventive = []
        for suggestion in suggestions:
            if suggestion.category == "lifestyle":
                preventive_suggestion = Suggestion(
                    category="preventive",
                    title=f"Prevent: {suggestion.title}",
                    description=f"To prevent symptoms: {suggestion.description}",
                    priority="low"
                )
                preventive.append(preventive_suggestion)
        return preventive
    
    def _merge_predictions(self, predictions: List[PredictedSymptom]) -> List[PredictedSymptom]:
        """Merge duplicate predictions and average probabilities"""
        symptom_groups = defaultdict(list)
        
        for pred in predictions:
            symptom_groups[pred.symptom].append(pred)
        
        merged = []
        for symptom, preds in symptom_groups.items():
            avg_prob = statistics.mean([p.probability for p in preds])
            confidence = "high" if avg_prob > 0.7 else "medium" if avg_prob > 0.4 else "low"
            
            merged.append(PredictedSymptom(
                symptom=symptom,
                probability=avg_prob,
                confidence=confidence
            ))
        
        return sorted(merged, key=lambda x: x.probability, reverse=True)
    
    def _calculate_confidence(self, recent_symptoms: List[SymptomResponse], 
                            predictions: List[PredictedSymptom]) -> float:
        """Calculate overall confidence score"""
        if not predictions:
            return 0.0
        
        # Base confidence on data availability and prediction strength
        data_confidence = min(len(recent_symptoms) / 7, 1.0)  # More data = higher confidence
        prediction_confidence = statistics.mean([p.probability for p in predictions])
        
        return (data_confidence + prediction_confidence) / 2
    
    def _deduplicate_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Remove duplicate suggestions and sort by priority"""
        seen = set()
        unique = []
        
        priority_order = {"high": 0, "medium": 1, "low": 2}
        
        # Sort by priority first
        sorted_suggestions = sorted(suggestions, key=lambda x: priority_order.get(x.priority, 3))
        
        for suggestion in sorted_suggestions:
            key = (suggestion.title, suggestion.category)
            if key not in seen:
                seen.add(key)
                unique.append(suggestion)
        
        return unique[:10]  # Limit to top 10 suggestions