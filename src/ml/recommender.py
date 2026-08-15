from typing import List, Set
from src.config.settings import settings
from src.domain.entities import RiskLevel, AttritionFactor, HRRecommendation

class HRRecommender:
    """
    Actionable HR Recommendation Engine.
    Translates machine learning risk levels and top SHAP risk factors into targeted,
    practical HR interventions to retain valuable talent.
    Deduplicates recommendations to ensure clear, clean HR guidance.
    """

    def __init__(self):
        pass

    def classify_risk_level(self, probability: float) -> RiskLevel:
        """Classifies attrition probability into Low, Medium, or High Risk tier."""
        if probability < settings.RISK_THRESHOLD_LOW:
            return RiskLevel.LOW
        elif probability <= settings.RISK_THRESHOLD_HIGH:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def generate_recommendations(
        self,
        probability: float,
        top_factors: List[AttritionFactor]
    ) -> List[HRRecommendation]:
        """
        Generates a curated, strictly deduplicated list of HR recommendations based on model output.
        Adjusts priority and urgency based on whether employee is High Risk (Likely to Leave) or Low/Medium Risk (Likely to Stay).
        """
        risk_level = self.classify_risk_level(probability)
        is_high_risk = (risk_level == RiskLevel.HIGH)

        recommendations: List[HRRecommendation] = []
        added_titles: Set[str] = set()

        # Filter factors that specifically increase risk (shap_value > 0)
        risk_drivers = [f for f in top_factors if f.shap_value > 0]

        for factor in risk_drivers:
            feat_name = factor.feature_name.lower()
            feat_val = str(factor.feature_value).lower()

            # 1. Overtime Risk Driver
            if ("frequent overtime" in feat_name or "overtime" in feat_name) and "no overtime" not in feat_name and feat_val != "no":
                title = "Overtime Review & Flexible Schedule"
                if title not in added_titles:
                    action_text = (
                        "Employee is experiencing frequent overtime. Conduct a workload audit, cap mandatory extra hours, and offer flexible working hours or remote days."
                        if is_high_risk else
                        "Review overtime distribution during routine schedule reviews to prevent future burnout."
                    )
                    recommendations.append(
                        HRRecommendation(
                            category="Work-Life Balance",
                            title=title,
                            action=action_text,
                            priority="High" if is_high_risk else "Medium"
                        )
                    )
                    added_titles.add(title)

            # 2. Work-Life Balance Risk Driver
            elif "worklife" in feat_name or "work-life" in feat_name or "balance" in feat_name:
                title = "Work-Life Balance Assessment"
                if title not in added_titles:
                    action_text = (
                        "Evaluate current workload distribution and offer remote work flexibility or wellness support program."
                        if is_high_risk else
                        "Maintain healthy work-life balance through standard team wellness initiatives."
                    )
                    recommendations.append(
                        HRRecommendation(
                            category="Work-Life Balance",
                            title=title,
                            action=action_text,
                            priority="High" if is_high_risk else "Low"
                        )
                    )
                    added_titles.add(title)

            # 3. Satisfaction / Engagement Risk Driver
            elif "satisfaction" in feat_name or "involvement" in feat_name or "environment" in feat_name:
                title = "Manager 1-on-1 & Engagement Check"
                if title not in added_titles:
                    action_text = (
                        "Schedule an urgent 1-on-1 feedback session ASAP to discuss workplace concerns, team dynamics, and role alignment."
                        if is_high_risk else
                        "Schedule a routine semi-annual career check-in to ensure continued role alignment and satisfaction."
                    )
                    recommendations.append(
                        HRRecommendation(
                            category="Employee Engagement",
                            title=title,
                            action=action_text,
                            priority="High" if is_high_risk else "Low"
                        )
                    )
                    added_titles.add(title)

            # 4. Promotion Lag / Stagnation Driver
            elif "promotion" in feat_name or "stagnation" in feat_name:
                title = "Career Progression Roadmap"
                if title not in added_titles:
                    action_text = (
                        "Employee has experienced promotion lag. Review career development milestone plan and discuss clear criteria for upcoming advancement."
                        if is_high_risk else
                        "Include career advancement goals in standard annual review planning."
                    )
                    recommendations.append(
                        HRRecommendation(
                            category="Career Growth",
                            title=title,
                            action=action_text,
                            priority="High" if is_high_risk else "Medium"
                        )
                    )
                    added_titles.add(title)

            # 5. Income / Compensation Driver
            elif "income" in feat_name or "salary" in feat_name or "pay" in feat_name:
                title = "Salary Benchmark Review"
                if title not in added_titles:
                    action_text = (
                        "Perform a competitive market salary review against industry standards and consider merit bonus or equity adjustment."
                        if is_high_risk else
                        "Review salary benchmarks during standard annual merit cycles."
                    )
                    recommendations.append(
                        HRRecommendation(
                            category="Compensation & Benefits",
                            title=title,
                            action=action_text,
                            priority="High" if is_high_risk else "Low"
                        )
                    )
                    added_titles.add(title)

            # 6. Distance / Commute Driver
            elif "commute" in feat_name or "distance" in feat_name:
                title = "Hybrid / Remote Work Option"
                if title not in added_titles:
                    recommendations.append(
                        HRRecommendation(
                            category="Work Arrangements",
                            title=title,
                            action="Address long commute stress by enabling hybrid work-from-home options or commuter stipend.",
                            priority="Medium" if is_high_risk else "Low"
                        )
                    )
                    added_titles.add(title)

            # 7. Frequent Business Travel Driver
            elif "travel" in feat_name and "frequent" in feat_name:
                title = "Travel Schedule Optimization"
                if title not in added_titles:
                    recommendations.append(
                        HRRecommendation(
                            category="Work Arrangements",
                            title=title,
                            action="Rebalance business travel load across team members to reduce travel fatigue.",
                            priority="Medium" if is_high_risk else "Low"
                        )
                    )
                    added_titles.add(title)

        # Baseline recommendation if risk is High but no specific triggers matched
        if is_high_risk and len(recommendations) == 0:
            recommendations.append(
                HRRecommendation(
                    category="Retention Strategy",
                    title="Proactive Stay Interview",
                    action="Conduct an executive stay interview with HR Lead and Department Manager to assess key retention factors.",
                    priority="High"
                )
            )

        # Baseline recommendation for Low risk employees
        if risk_level == RiskLevel.LOW and len(recommendations) == 0:
            recommendations.append(
                HRRecommendation(
                    category="Employee Recognition",
                    title="Maintain Positive Engagement",
                    action="Continue current positive management practices and include employee in key team recognition programs.",
                    priority="Low"
                )
            )

        return recommendations
