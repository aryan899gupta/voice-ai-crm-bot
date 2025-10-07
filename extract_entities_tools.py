
import re
import uuid
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
from dateparser.search import search_dates
from dateparser import parse as date_parse
import pytz
from logger_config import logger


# Load NER (dslim/bert-large-NER)
try:
    from transformers import pipeline
    ner = pipeline("ner", model="Davlan/xlm-roberta-base-ner-hrl", aggregation_strategy="simple")
except Exception as e:
    logger.info("[warn] Could not load NER model:", e)
    ner = None
logger.info("[info] Loading NER model: Davlan/xlm-roberta-base-ner-hrl")


# Load zero-shot model once (global)
try:
    status_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    logger.info("[warn] Could not load BART-MNLI model:", e)
    status_classifier = None
logger.info("[info] Loading NER model: zero-shot-classification")



# Extractors

def extract_email(text: str) -> Optional[str]:
    m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    if m:
        email = m.group(0)
        try:
            validate_email(email)
            return email
        except EmailNotValidError:
            return None
    return None


def extract_phone(text: str, default_region: str = "IN") -> Optional[str]:
    if not text:
        return None

    try:
        for match in phonenumbers.PhoneNumberMatcher(text, default_region):
            try:
                return phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
            except Exception:
                # fallback to raw national number if formatting fails
                return phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        # If phonenumbers fails for any reason, proceed to regex fallback
        pass

    # Regex fallback: find 8-15 digit sequences possibly separated by spaces, dashes, parentheses
    # e.g. "91234-56789", "+91 9123456789", "(91) 91234 56789"
    m = re.search(r"(?:\+?\d[\d\-\s\(\)]{6,}\d)", text)
    if m:
        raw = m.group(0)
        # keep leading + if present, remove everything else that's not a digit or plus
        cleaned = re.sub(r"[^\d+]", "", raw)
        # sanity: require at least 8 digits (after removing +)
        digits_only = re.sub(r"[^\d]", "", cleaned)
        if len(digits_only) >= 8:
            if cleaned.startswith("+") and 8 <= len(digits_only) <= 15:
                return cleaned
            return digits_only
    return None


def extract_datetime(text: str) -> Optional[str]:
    """Extract datetime from text with fallback for 'today/tomorrow/day after' + time."""
    if not text:
        return None

    # --- 1️⃣ Remove detected phone numbers ---
    try:
        for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
            phone_raw = match.raw_string
            text = text.replace(phone_raw, "")
    except Exception:
        pass

    # --- 2️⃣ Try normal parsing first ---
    try:
        found = search_dates(text, settings={"PREFER_DATES_FROM": "future"})
    except Exception:
        found = None

    if found:
        now = datetime.now()
        one_year = now + timedelta(days=365)
        valid_dates = [dt for _, dt in found if now <= dt <= one_year]
        if not valid_dates:
            valid_dates = [dt for _, dt in found if dt <= one_year]
        if valid_dates:
            earliest = min(valid_dates)
            return earliest.isoformat()

    #Fallback manual logic
    lower = text.lower()
    today = datetime.now().replace(second=0, microsecond=0)
    base_date = None

    # detect relative day
    if "day after tomorrow" in lower:
        base_date = today + timedelta(days=2)
        lower = lower.replace("day after tomorrow", "")
    elif "tomorrow" in lower:
        base_date = today + timedelta(days=1)
        lower = lower.replace("tomorrow", "")
    elif "today" in lower:
        base_date = today
        lower = lower.replace("today", "")

    # if no relative found, stop
    if not base_date:
        return None

    # Find time (e.g. 3pm, 3 pm, 9:30 am)
    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3)
        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
        base_date = base_date.replace(hour=hour, minute=minute)

    else:
        return None

    return base_date.isoformat()



def extract_name_city(text: str) -> Tuple[Optional[str], Optional[str]]:
    name, city = None, None

    if ner is not None:
        try:
            ents = ner(text)
            for e in ents:
                label = e.get("entity_group", "").upper().strip()
                word = e.get("word", "").strip().strip(",.")
                # Handle multi-word entities and punctuation cleanly
                if label in ("PER", "PERSON"):
                    name = (name + " " + word).strip() if name else word
                elif label in ("LOC", "GPE", "CITY", "LOCATION"):
                    city = (city + " " + word).strip() if city else word
        except Exception as ex:
            logger.info("[warn] NER extraction failed:", ex)

    # Regex fallbacks
    if not name:
        m = re.search(r"\b(?:name|lead)\s*(?:is|:)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", text)
        if not m:
            m = re.search(r"\badd(?: a| new)?(?: lead| contact)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", text, re.IGNORECASE)
        if m:
            name = m.group(1)

    if not city:
        m = re.search(r"\b(?:from|in|at|within|to)\s+([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+)?)\b", text)
        if m:
            city = m.group(1)

    return name, city



def extract_lead_id(text: str):
    if not text:
        return None
    
    #Remove any detected phone numbers from the text
    try:
        for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
            phone_raw = match.raw_string
            text = text.replace(phone_raw, "")
    except Exception:
        pass

    text_lower = text.lower()

    # Alphanumeric ID (UUID-like or short hex)
    match = re.search(r"\b[a-fA-F0-9]{4,36}\b", text)
    if match:
        candidate = match.group(0)
        # ensure it's not the full text itself
        if candidate.strip().lower() != text_lower:
            return candidate

    return None


def extract_source(text: str) -> Optional[str]:
    if not text:
        return None

    text_lower = text.lower()

    SOURCE_KEYWORDS = {
        "instagram": "Instagram",
        "insta": "Instagram",
        "facebook": "Facebook",
        "fb": "Facebook",
        "linkedin": "LinkedIn",
        "linkedin.com": "LinkedIn",
        "google": "Google",
        "whatsapp": "WhatsApp",
        "wa.me": "WhatsApp",
        "website": "Website",
        "form": "Website",
        "walk-in": "Walk-in",
        "walk in": "Walk-in",
        "referral": "Referral",
        "refer": "Referral",
        "call": "Call",
        "phone": "Call",
    }

    for keyword, label in SOURCE_KEYWORDS.items():
        if keyword in text_lower:
            return label
        

    match = re.search(r"(instagram\.com|linkedin\.com|facebook\.com|wa\.me|whatsapp\.com)", text_lower)
    if match:
        if "instagram" in match.group(1):
            return "Instagram"
        if "linkedin" in match.group(1):
            return "LinkedIn"
        if "facebook" in match.group(1):
            return "Facebook"
        if "whatsapp" in match.group(1) or "wa.me" in match.group(1):
            return "WhatsApp"

    return None


def extract_status(text: str) -> Optional[Dict[str, float]]:

    STATUS_LABELS = ["NEW", "IN_PROGRESS", "FOLLOW_UP", "WON", "LOST"]

    if not text or not text.strip():
        return None

    if status_classifier is None:
        return None

    try:
        result = status_classifier(text, candidate_labels=STATUS_LABELS)
        # Return label with highest confidence
        return result["labels"][0]
    except Exception as e:
        logger.info(f"[error] extract_status failed: {e}")
        return "UNKNOWN"


# Unified interface
def extract_entities_basic(text: str) -> Dict[str, Optional[Any]]:
    """Extracts core entities and returns a normalized dict."""
    name, city = extract_name_city(text)
    phone = extract_phone(text)
    email = extract_email(text)
    datetime_str = extract_datetime(text)
    lead_id = extract_lead_id(text)
    status = extract_status(text)
    source = extract_source(text)

    return {
        "name": name,
        "city": city,
        "phone": phone,
        "email": email,
        "visit_time": datetime_str,
        "lead_id": lead_id,
        "status": status,
        "source": source,
    }


# CLI (FOR TESTING)
if __name__ == "__main__":
    import argparse, json
    p = argparse.ArgumentParser(description="Minimal entity extractor")
    p.add_argument("--text", "-t", required=True)
    args = p.parse_args()

    out = extract_entities_basic(args.text)
    print(json.dumps(out, indent=2))