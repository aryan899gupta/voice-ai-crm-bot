class ErrorHandler:
    """Centralized error handler for standardized validation errors."""

    @staticmethod
    def data_incomplete(intent: str, field: str):
        return {
            "intent": intent,
            "error": {
                "type": "VALIDATION_ERROR",
                "details": {
                    "field": field,
                    "reason": "data_incomplete",
                    "hint": f"Missing or incomplete data for field '{field}'."
                }
            }
        }

    @staticmethod
    def visit_date_incomplete(intent: str):
        return {
            "intent": intent,
            "error": {
                "type": "VALIDATION_ERROR",
                "details": {
                    "field": "visit_time",
                    "reason": "visit_date_incomplete",
                    "hint": "Visit datetime missing or invalid (expected ISO, future date)."
                }
            }
        }

    @staticmethod
    def phone_incomplete(intent: str):
        return {
            "intent": intent,
            "error": {
                "type": "VALIDATION_ERROR",
                "details": {
                    "field": "phone",
                    "reason": "phone_incomplete",
                    "hint": "Phone number missing or invalid (include +91 or 10 digits)."
                }
            }
        }

    @staticmethod
    def status_incomplete(intent: str):
        return {
            "intent": intent,
            "error": {
                "type": "VALIDATION_ERROR",
                "details": {
                    "field": "status",
                    "reason": "status_incomplete",
                    "hint": "Missing or invalid status (use NEW, IN_PROGRESS, FOLLOW_UP, WON, or LOST)."
                }
            }
        }