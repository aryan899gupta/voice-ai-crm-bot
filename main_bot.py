import json
import argparse
from intent_transformer_knn import score_intents_avg 
from extract_entities_tools import extract_entities_basic  
from validators.validate_output import validate_intent_output
from logger_config import logger

# Intent normalization 
def normalize_intent(intent_scores: dict) -> str:
    """Return mapped intent if top score > 0.5, else UNKNOWN."""
    if not intent_scores:
        return "UNKNOWN"

    top_intent = max(intent_scores, key=intent_scores.get)
    top_score = round(intent_scores[top_intent], 1)

    if top_score <= 0.5:
        return "UNKNOWN"

    mapping = {
        "ADDING": "LEAD_CREATE",
        "SCHEDULING": "VISIT_SCHEDULE",
        "UPDATING": "LEAD_UPDATE"
    }

    return mapping.get(top_intent, "UNKNOWN")


# CRM endpoint resolver 
def crm_endpoint_for_intent(intent: str) -> dict:
    if intent == "LEAD_CREATE":
        return {"endpoint": "/crm/lead/create", "method": "POST", "status_code": 200}
    elif intent == "VISIT_SCHEDULE":
        return {"endpoint": "/crm/visit/schedule", "method": "POST", "status_code": 200}
    elif intent == "LEAD_UPDATE":
        return {"endpoint": "/crm/lead/update", "method": "POST", "status_code": 200}
    else:
        return {"endpoint": "/crm/unknown", "method": "POST", "status_code": 400}


#Main handler
def process_request(data: dict) -> dict:
    logger.info(f"[BOT] Processing request for transcript='{data.get('transcript', '')[:100]}...'")
    transcript = data.get("transcript", "")
    metadata = data.get("metadata", {})

    #Detect intent
    _, _, _, intent_scores = score_intents_avg(transcript)
    intent = normalize_intent(intent_scores)
    logger.info(
    "[model] Intent scores: LEAD_CREATE=%.2f, VISIT_SCHEDULE=%.2f, LEAD_UPDATE=%.2f",
    intent_scores.get("ADDING", 0),
    intent_scores.get("SCHEDULING", 0),
    intent_scores.get("UPDATING", 0),
)
    

    #Extract entities
    entities = extract_entities_basic(transcript)
    if intent == "LEAD_CREATE":
        entities["status"] = "NEW"
    logger.info(f"[BOT] Extracted entities: {entities}")

    #CRM endpoint
    crm_info = crm_endpoint_for_intent(intent)
    logger.info(
    "CRM call → %s (%s) [%s OK]",
    crm_info["endpoint"],
    crm_info["method"],
    crm_info.get("status_code", 200),
    )

    #Handling UNKNOWN
    if intent == "UNKNOWN":
        return {
            "intent": "UNKNOWN",
            "entities": entities, 
            "crm_call": {"endpoint": None, "method": None, "status_code": 200},
            "result": {
                "message": "Intent could not be identified. No CRM action taken."
            }
        }

    #Final JSON
    result = {
        "intent": intent,
        "entities": entities,
        "crm_call": crm_info,
        "result": {
            "message": f"Successfully processed intent '{intent}' for user {metadata.get('user_id', 'anonymous')}."
        }
    }
    

    # Validate output before returning
    validation_error = validate_intent_output(result)
    if validation_error:
        return validation_error

    logger.info("Response returned to client.")
    return result


# CLI (FOR TESTING)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intent + Entity processor")
    parser.add_argument("--json", type=str, required=True, help="Input JSON string")
    args = parser.parse_args()

    try:
        input_data = json.loads(args.json)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON input.")

    output = process_request(input_data)
    print(json.dumps(output, indent=2))