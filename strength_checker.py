import re

class PasswordStrengthChecker:
    """Evaluates password strength based on security criteria."""

    def __init__(self):
        self.criteria = {
            'length': {'weight': 2, 'min': 8},
            'uppercase': {'weight': 1, 'pattern': r'[A-Z]'},
            'lowercase': {'weight': 1, 'pattern': r'[a-z]'},
            'digits': {'weight': 1, 'pattern': r'\d'},
            'symbols': {'weight': 2, 'pattern': r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]'}
        }

    def check_criteria(self, password):
        """Check password against all criteria. Returns dict with results."""
        results = {
            'length': len(password) >= self.criteria['length']['min'],
            'uppercase': bool(re.search(self.criteria['uppercase']['pattern'], password)),
            'lowercase': bool(re.search(self.criteria['lowercase']['pattern'], password)),
            'digits': bool(re.search(self.criteria['digits']['pattern'], password)),
            'symbols': bool(re.search(self.criteria['symbols']['pattern'], password))
        }
        return results

    def calculate_score(self, password):
        """Calculate password strength score (0-100)."""
        if not password:
            return 0

        score = 0
        criteria_results = self.check_criteria(password)

        # Length contribution
        length_score = min(len(password) / 12 * 20, 20)
        score += length_score

        # Character type contributions
        if criteria_results['uppercase']:
            score += self.criteria['uppercase']['weight'] * 15
        if criteria_results['lowercase']:
            score += self.criteria['lowercase']['weight'] * 15
        if criteria_results['digits']:
            score += self.criteria['digits']['weight'] * 15
        if criteria_results['symbols']:
            score += self.criteria['symbols']['weight'] * 20

        return min(score, 100)

    def get_strength_level(self, password):
        """
        Determine strength level: Weak, Medium, Strong.
        Returns: (strength_level: str, score: int, feedback: list)
        """
        score = self.calculate_score(password)
        criteria = self.check_criteria(password)
        feedback = []

        # Build feedback
        if len(password) < 8:
            feedback.append(f"Use at least 8 characters (currently {len(password)})")
        if not criteria['uppercase']:
            feedback.append("Add uppercase letters")
        if not criteria['lowercase']:
            feedback.append("Add lowercase letters")
        if not criteria['digits']:
            feedback.append("Add numbers")
        if not criteria['symbols']:
            feedback.append("Add special characters")

        # Determine level
        if score >= 70:
            strength = "Strong"
        elif score >= 40:
            strength = "Medium"
        else:
            strength = "Weak"

        return strength, score, feedback

    def get_strength_color(self, password):
        """Return color code for password strength (for UI)."""
        score = self.calculate_score(password)
        if score >= 70:
            return "#00AA00"  # Green
        elif score >= 40:
            return "#FFAA00"  # Orange
        else:
            return "#CC0000"  # Red
