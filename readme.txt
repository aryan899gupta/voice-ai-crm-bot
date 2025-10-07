1. Project Overview

The Voice Bot AI Assistant is an intelligent NLP-driven system that interprets STT and converts it into structured CRM-ready data.
The aim is to replicate in some magnitude how modern AI assistants function in enterprise CRMs.
This has been achieved by utilizing a conjunction of methods including NLP, Transformers, some classic ML techniques and  Rule Based Heuristics


2. Core Objectives
	•	Interpret natural language input (simulating STT)
	•	At a high-level, detect the user's intent amongst 3 categories:
        •	LEAD_CREATE (Add new lead)
        •	VISIT_SCHEDULE (Schedule meeting or visit)
        •	LEAD_UPDATE (Update lead status)
	•	Extract structured data entities like:
	    •	Name, Phone, City, Email, Datetime, Lead ID, Source, Status
	•	Validate that all required information is present
	•	Log, handle, and return consistent JSON responses in real time
	•	Integrate with a mock CRM for endpoint simulation (to represent backend connectivity)


3. Technologies Used

Machine Learning & NLP
	•	Sentence-Transformers (all-mpnet-base-v2) – for generating semantic embeddings that represent user text meaningfully.
	•	Hugging Face Transformers (Davlan/xlm-roberta-base-ner-hrl) – multilingual NER model for extracting names and cities.
	•	Zero-Shot Classifier (facebook/bart-large-mnli) – for classifying "status" to labels such as NEW, IN_PROGRESS, WON, or LOST using NLI
    •	K-Nearest Neighbors (kNN) – used to compare input embeddings against predefined intent vectors (ADDING, SCHEDULING, UPDATING).
    •   Cosine similarity - Between the input and known intent phrases, producing normalized intent confidence scores.
	•	Regex + Rule-Based Parsing – for phone numbers, emails, dates, and CRM IDs.
	•	Dateparser – for natural language date and time extraction (e.g., “tomorrow at 3 pm”).

Backend & API Framework
	•	FastAPI – modern, high-performance web framework for defining the /bot/handle endpoint.
	•	Pydantic – for request validation and schema enforcement.
	•	Uvicorn – ASGI server to run the FastAPI application.

Testing & Validation
	•	pytest – for automated end-to-end pipeline testing across multiple sample transcripts.
	•	Custom Validators – for enforcing intent-specific entity requirements (phone, date, etc.).
	•	Error Handler Module – for standardized JSON error responses such as VALIDATION_ERROR, PARSING_ERROR, or CRM_ERROR.

Logging & Observability
	•	Python Logging Module – with centralized rotated log file management in /logs/app.log.
	•	Each request, response, and CRM call is timestamped and logged for debugging and traceability.


4. File structure:

voice_bot/
│
├── app.py                         # FastAPI entrypoint
├── main_bot.py                    # Core intent + entity pipeline
├── intent_transformer_knn.py      # Sentence Transformers + KNN Based Scorer to identify intent of the user
├── extract_entities_tools.py      # Extracting entities using zero shot models, NERs, classic ML scrapers and rule based approaches
├── logger_config.py               # Config for the logger
├── mock_crm.py                    # Mock backend CRM provided in the assignment
├── validators/
│   └── validate_output.py         # Output validation and error generation
│   └── error_handler.py           # Contains the error handling logic
├── syntheticData/
│   ├── verb_intent_data.py
│   └── keyword_intent_data.py
│   └── regex_parser.py
├── logs/
│   └── app.log                    # Rotating logs
├── tests/
│   └── test_intent_outputs.py     # Pytest suite
└── requirements.txt


5. Setup and Installation

	1.	CREATE & ACTIVATE A VIRTUAL ENVIRONMENT

        Create:
        python3 -m venv botVenv

        Activate (macOS / Linux):
        source botVenv/bin/activate

        For Windows PowerShell:
        .\botVenv\Scripts\Activate.ps1


	2.	UPGRADE PIP & INSTALL DEPENDENCIES

        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt
    

    3. RUN TESTS

        pytest -q -s

    4. RUN THE API

        For the model: uvicorn app:app --reload --port 8000
        For the dummy backend API:  uvicorn mock_crm:app --host 0.0.0.0 --port 8001 --reload 

    5. Test a query
        curl -X POST "http://127.0.0.1:8000/bot/handle" \
        -H "Content-Type: application/json" \
        -d '{"transcript": "Add a new lead: Rohan Sharma from Gurgaon, phone 9876543210, source Instagram."}'


6. Sample Input-Output
Input JSON:
{
  "transcript": "Add a new lead: Rohan Sharma from Gurgaon, phone 9876543210, source Instagram.",
  "metadata": {
    "user_id": "pytest-demo"
  }
}
Output JSON:
{
  "intent": "LEAD_CREATE",
  "entities": {
    "name": "Rohan Sharma",
    "city": "Gurgaon",
    "phone": "+919876543210",
    "email": null,
    "visit_time": null,
    "lead_id": null,
    "status": "NEW",
    "source": "Instagram"
  },
  "crm_call": {
    "endpoint": "/crm/lead/create",
    "method": "POST",
    "status_code": 200
  },
  "result": {
    "message": "Successfully processed intent 'LEAD_CREATE' for user pytest-demo."
  }
}
