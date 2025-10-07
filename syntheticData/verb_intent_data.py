# synthetic_data/verb_intent_data.py
"""
Synthetic verb and phrase groupings for intent detection.
Used by kNN intent scorer in intent_verbs_knn.py
"""

# ---------- ADDING verbs ----------
base_adding_verbs = [
    "add", "create", "register", "onboard", "enroll", "insert", "open", "save", "generate"
]
adding_phrases = base_adding_verbs

# ---------- SCHEDULING verbs ----------
base_visiting_verbs = [
    "schedule", "book", "arrange", "plan", "meet", "visit", "go", "see", "fix"
]
visiting_phrases = base_visiting_verbs

# ---------- UPDATING verbs ----------
base_updating_verbs = [
    "update", "change", "modify", "mark", "edit", "convert", "revise", "check", "alter", "move"
]
updating_phrases = base_updating_verbs

# ---------- Combined intent mapping ----------
INTENT_VERBS = {
    "ADDING": adding_phrases,
    "SCHEDULING": visiting_phrases,
    "UPDATING": updating_phrases,
}