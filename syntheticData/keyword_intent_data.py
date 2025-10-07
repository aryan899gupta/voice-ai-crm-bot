"""
Synthetic keywords groupings for intent detection.
"""

# ---------- ADDING keywords ----------
base_adding_keywords = [
    "name", "email", "phone", "number", "city", "location", "street", "new"
    "source", "instagram", "facebook", "linkedin", "signup", "form", "details",
]
adding_phrases = base_adding_keywords

# ---------- SCHEDULING keywords ----------
base_visiting_keywords = [
    "calendar", "reminder", "set up", "meeting", "scheduling"
    "today", "tomorrow", "next week", "evening", "morning", "afternoon",
    "call", "demo", "tour", "inspection", "slot", "time", "day", "date",
]
visiting_phrases = base_visiting_keywords

# ---------- UPDATING keywords ----------
base_updating_keywords = [
    "won", "lost", "closed", "converted", "pending", "completed", "cancelled", "delete",
    "remove", "adjust", "remark", "comment", "feedback", "note", "notes", "details",
    "reopened", "archive"
]
updating_phrases = base_updating_keywords

# ---------- Combined intent mapping ----------
INTENT_KEYWORDS = {
    "ADDING": adding_phrases,
    "SCHEDULING": visiting_phrases,
    "UPDATING": updating_phrases,
}