import json
import os
import pytest

import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main_bot import process_request 

TEST_QUERIES = [
    # --- ADDING / Lead Creation ---
    "Add a new lead: Rohan Sharma from Gurgaon, phone 9876543210, source Instagram.",
    "Create lead name Priya Nair, city Mumbai, contact 91234-56789.",
    "Add a customer profile for Aarav Mehta in Pune, source LinkedIn.",
    "Register new client Sneha Kapoor, number 8899776655, from Delhi.",

    # --- SCHEDULING / Visit ---
    "Update client 9c2d meeting on 12-10-2025 10am.",
    "Schedule inspection 2025-10-15 18:30 for 3w2rq2345tt in Bengaluru.",
    "Schedule a visit for lead 7b1b8f54 at 3 pm tomorrow.",
    "Fix a site visit for lead 8f2a on Oct the 15th of 2025 at 5:00 pm IST.",
    "Book an appointment with client 9c2d for property tour next Monday.",

    # --- UPDATING / Status Change ---
    "Update lead 7b1b8f54 to in progress.",
    "Mark lead 7b1b8f54 as won. Notes: booked unit A2.",
    "Change status of lead 7b1b8f54 to lost.",
    "Modify lead 8c1d to follow up tomorrow.",

    # --- Misc / Ambiguous ---
    "Can you help me?",
    "Check the status of lead 7b1b8f54.",
    "Show me all leads created today."
]

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "intent_test_outputs.txt")
# Clear output file once before all tests
if os.path.exists(OUTPUT_PATH):
    os.remove(OUTPUT_PATH)

@pytest.mark.parametrize("query", TEST_QUERIES)
def test_generate_intent_outputs(query):
    out_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(out_dir, exist_ok=True)

    # Write to file
    input_json = {"transcript": query, "metadata": {"user_id": "pytest-demo"}}
    output_json = process_request(input_json)

    block = []
    block.append("Input JSON:")
    block.append(json.dumps(input_json, indent=2))
    block.append("Output JSON:")
    block.append(json.dumps(output_json, indent=2))
    block.append("-" * 60)
    text_block = "\n".join(block) + "\n"

    with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
        f.write(text_block)
