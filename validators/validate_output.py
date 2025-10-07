from typing import Dict, Any, List
from validators.error_handler import ErrorHandler
from dataclasses import dataclass


@dataclass
class OutputValidationError(Exception):
    error: Dict[str, Any]

    def as_dict(self):
        return self.error

# Required entity fields for each intent
REQUIRED_FIELDS = {
    "LEAD_CREATE": ["name", "phone", "city"],
    "VISIT_SCHEDULE": ["lead_id", "visit_time"],
    "LEAD_UPDATE": ["lead_id", "status"],
}

def validate_intent_output(output: Dict[str, Any]) -> Dict[str, Any]:
    
    intent = output.get("intent", "UNKNOWN")
    entities = output.get("entities", {})

    # No validation needed for UNKNOWN intent
    if intent == "UNKNOWN":
        return None
    
    # LEAD_CREATE: require phone, name, city
    if intent == "LEAD_CREATE":
        if not entities.get("phone"):
            return ErrorHandler.phone_incomplete(intent)
        if not entities.get("name") or not entities.get("city"):
            return ErrorHandler.data_incomplete(intent, "name/city")

    # VISIT_SCHEDULE: require datetime
    if intent == "VISIT_SCHEDULE":
        if not entities.get("visit_time"):
            return ErrorHandler.visit_date_incomplete(intent)

    # LEAD_UPDATE: require status
    if intent == "LEAD_UPDATE":
        if not entities.get("status"):
            return ErrorHandler.status_incomplete(intent)
            

    return None