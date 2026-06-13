from typing import Dict, Any


class ReflectionAgent:

    def should_reflect(
        self,
        critic_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        recommendation = critic_result.get(
            "recommendation",
            "approved"
        )

        if recommendation in [
            "review",
            "manual_review"
        ]:
            return {
                "reflect": True,
                "reason":
                    "Critic detected uncertainty"
            }

        return {
            "reflect": False,
            "reason":
                "No reflection required"
        }