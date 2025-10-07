# regex_parser.py
"""
Regex parser module with built-in patterns for ADDING / SCHEDULING / UPDATING.
"""

import re
from typing import Dict, List, Tuple, Optional


ADDING_REGEX = [
    # international / local phone numbers (10 digits, optional country code + separators)
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{6,12}\b",
    # strict 10-digit phones
    r"\b(?:\+91|0)?\d{10}\b",
    # email addresses
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    # obvious "phone number combinations" mention with digits
    r"(?:\+?\d{1,3}[-.\s]*)?(?:\d[-.\s]*){6,14}\d",
    # explicit "country code" mention like +91, +1
    r"\+\d{1,3}\b",
]

SCHEDULING_REGEX = [
    # ISO date YYYY-MM-DD
    r"\b\d{4}-\d{2}-\d{2}\b",
    # common numeric date formats: DD/MM/YYYY or DD-MM-YYYY or D/M/YY
    r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b",
    # textual dates: 12th March, 12 March, March 12, Mar 12
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}\b",
    # days of week
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    # times: 3pm, 3:30pm, 15:00, 3.30 p.m., 3 o'clock
    r"\b\d{1,2}(?::\d{2})?\s?(?:am|pm|a\.m\.|p\.m\.|hrs|hours)?\b",
    r"\b\d{1,2}:\d{2}\b",
    r"\b\d{1,2}\s+o'?clock\b",
    # time ranges or 'at' preposition
    r"\bat\s+\d{1,2}(?::\d{2})?\b",
]

INTENT_REGEX = {
    "ADDING": ADDING_REGEX,
    "SCHEDULING": SCHEDULING_REGEX
}

_COMPILED = {}
for intent, patterns in INTENT_REGEX.items():
    compiled_list = []
    for p in patterns:
        try:
            compiled_list.append(re.compile(p, flags=re.IGNORECASE))
        except re.error:
            # if someone adds a bad regex, ignore it but warn in runtime
            print(f"[regex_parser] Warning: failed to compile pattern for {intent}: {p!r}")
    _COMPILED[intent] = compiled_list


def regex_score(
    text: str,
    per_match_score: float = 0.5,
    max_per_intent: Optional[float] = None,
    count_overlapping: bool = False,
) -> Tuple[Dict[str, float], List[Tuple[str, str, str]]]:

    # quick empty text check
    if not text:
        return ({intent: 0.0 for intent in _COMPILED.keys()}, [])

    increments = {intent: 0.0 for intent in _COMPILED.keys()}
    matches_meta: List[Tuple[str, str, str]] = []

    for intent, compiled_list in _COMPILED.items():
        total = 0.0
        for cre in compiled_list:
            pattern = cre.pattern
            if count_overlapping:
                # attempt overlapping matches via lookahead
                try:
                    lookahead = re.compile(r"(?=(" + pattern + r"))", flags=re.IGNORECASE)
                    found = [m.group(1) for m in lookahead.finditer(text)]
                except re.error:
                    # fallback to non-overlapping finditer if lookahead fails
                    found = [m.group(0) for m in cre.finditer(text)]
            else:
                found = [m.group(0) for m in cre.finditer(text)]

            for m in found:
                total += per_match_score
                matches_meta.append((intent, pattern, m))

        if (max_per_intent is not None) and (total > max_per_intent):
            total = float(max_per_intent)
        increments[intent] = float(total)

    # Normalize
    total_inc = sum(increments.values())
    if total_inc <= 0:
        normalized = {intent: 0.0 for intent in increments.keys()}
    else:
        normalized = {intent: float(increments[intent] / total_inc) for intent in increments.keys()}

    return normalized, matches_meta



# CLI (FOR TESTING)
if __name__ == "__main__":
    import argparse, json
    p = argparse.ArgumentParser(description="Regex parser debug tool")
    p.add_argument("--text", type=str, required=True, help="Text to parse")
    p.add_argument("--score", type=float, default=0.5, help="Per-match score (default 0.5)")
    p.add_argument("--cap", type=float, default=None, help="Optional cap per intent (float)")
    p.add_argument("--overlap", action="store_true", help="Count overlapping matches")
    args = p.parse_args()

    incs, meta = regex_score(args.text, per_match_score=args.score, max_per_intent=args.cap, count_overlapping=args.overlap)
    print("Increments:")
    print(json.dumps(incs, indent=2))
    if meta:
        print("\nMatches:")
        for intent, pat, m in meta:
            print(f" - [{intent}] pattern={pat!r} matched={m!r}")
    else:
        print("\nNo regex matches found.")