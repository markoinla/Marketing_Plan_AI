from langflow.load import run_flow_from_json
from dotenv import load_dotenv
import requests
from typing import Optional
import os

load_dotenv()

BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "be55e836-3ca9-4c3e-bcbf-d4f23c4b4489"
APPLICATION_TOKEN = os.getenv("LANGFLOW_TOKEN")

# Langflow integration

def ask_ai(company, website, industry, description, goals, budget):
    TWEAKS = {
    "TextInput-VZluo": {
        "input_value": company
    },
    "TextInput-jYjvb": {
        "input_value": website
    },
    "TextInput-GoayS": {
        "input_value": industry
    },
    "TextInput-1A8tY": {
        "input_value": description
    },
    "TextInput-UR0OT": {
        "input_value": goals
    },
    "Prompt-mOIJB": {},
    "TextInput-ssGXF": {
        "input_value": budget
    },
    "OpenAIModel-HpsyY": {},
    "TextOutput-5HzQl": {}
    }

    result = run_flow_from_json(flow="MarketingPlanApp.json",
                                input_value="message",
                                session_id="", # provide a session id if you want to use session state
                                fallback_to_env_vars=True, # False by default
                                tweaks=TWEAKS)

    return result[0].outputs[0].results["text"].data["text"]


# LANGFLOW API





# You can tweak the flow by adding a tweaks dictionary
# e.g {"OpenAI-XXXXX": {"model_name": "gpt-4"}}

def generate_plan(company, website, industry, description, goals, budget):
    TWEAKS = {
        "TextInput-VZluo": {
            "input_value": company
        },
        "TextInput-jYjvb": {
            "input_value": website
        },
        "TextInput-GoayS": {
            "input_value": industry
        },
        "TextInput-1A8tY": {
            "input_value": description
        },
        "TextInput-UR0OT": {
            "input_value": goals
        },
        "TextInput-ssGXF": {
            "input_value": budget
        }
    }
    return run_flow("", tweaks=TWEAKS, application_token=APPLICATION_TOKEN)

def run_flow(message: str,
  output_type: str = "chat",
  input_type: str = "chat",
  tweaks: Optional[dict] = None,
  application_token: Optional[str] = None) -> dict:

    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/generate-plan"

    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
    }
    
    if tweaks:
        payload["tweaks"] = tweaks
    
    headers = {"Content-Type": "application/json"}
    if application_token:
        headers["Authorization"] = f"Bearer {application_token}"
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()["outputs"][0]["outputs"][0]["results"]["text"]["data"]["text"]
    except requests.exceptions.RequestException as e:
        print(f"Error making request to API: {str(e)}")
        print(f"Request URL: {api_url}")
        print(f"Headers (redacted): {headers}")
        raise

result = generate_plan("Zenlayer","zenlayer.com","internet","Zenlayer is a cloud infrastructure company","grow leads","5000")
print(result)