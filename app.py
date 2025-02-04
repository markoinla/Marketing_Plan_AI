from flask import Flask, render_template, request, jsonify, send_file, make_response
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SubmitField, URLField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, URL, Optional
import os
import requests
import json
from dotenv import load_dotenv
from reportlab.lib import colors
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from bs4 import BeautifulSoup
from typing import Optional as OptionalType
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    raise

# Langflow API configuration
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "be55e836-3ca9-4c3e-bcbf-d4f23c4b4489"
APPLICATION_TOKEN = os.getenv("LANGFLOW_TOKEN")

app = Flask(__name__, static_url_path='/assets', static_folder='assets')
app.config['SECRET_KEY'] = os.urandom(24)

# Common B2B industries
B2B_INDUSTRIES = [
    ('', 'Select an Industry'),
    ('software_technology', 'Software & Technology'),
    ('it_services', 'IT Services & Consulting'),
    ('manufacturing', 'Manufacturing'),
    ('professional_services', 'Professional Services'),
    ('financial_services', 'Financial Services'),
    ('healthcare_technology', 'Healthcare Technology'),
    ('business_services', 'Business Services'),
    ('telecommunications', 'Telecommunications'),
    ('logistics_supply_chain', 'Logistics & Supply Chain'),
    ('industrial_equipment', 'Industrial Equipment'),
    ('cloud_solutions_services', 'Cloud Solutions & Services'),
    ('other', 'Other')
]

# Budget ranges
BUDGET_RANGES = [
    ('under_1k', 'Under $1,000'),
    ('1k_10k', '$1,000 - $10,000'),
    ('10k_25k', '$10,000 - $25,000'),
    ('25k_50k', '$25,000 - $50,000'),
    ('50k_75k', '$50,000 - $75,000'),
    ('75k_100k', '$75,000 - $100,000'),
    ('100k_150k', '$100,000 - $150,000'),
    ('150k_200k', '$150,000 - $200,000'),
    ('200k_250k', '$200,000 - $250,000'),
    ('over_250k', 'Over $250,000')
]

# Common B2B Marketing Goals
B2B_MARKETING_GOALS = [
    ('generate_qualified_leads', 'Generate More Qualified Leads'),
    ('increase_conversion_rate', 'Increase Conversion Rate'),
    ('expand_market_share', 'Expand Market Share'),
    ('enter_new_markets', 'Enter New Markets'),
    ('launch_new_product', 'Launch New Product/Service'),
    ('increase_customer_retention', 'Increase Customer Retention'),
    ('improve_customer_engagement', 'Improve Customer Engagement')
]

class MarketingPlanForm(FlaskForm):
    website_url = URLField('Company Website URL', validators=[Optional(), URL()])
    company_name = StringField('Company Name', validators=[DataRequired()])
    industry = SelectField('Industry', 
                         choices=B2B_INDUSTRIES,
                         validators=[DataRequired()])
    company_description = TextAreaField('Company Description', validators=[DataRequired()])
    target_audience = TextAreaField('Target Audience', validators=[DataRequired()])
    goals = SelectMultipleField('Marketing Goals',
                              choices=B2B_MARKETING_GOALS,
                              validators=[DataRequired()])
    budget = SelectField('Monthly Marketing Budget',
                     choices=BUDGET_RANGES,
                     validators=[DataRequired()])
    submit = SubmitField('Generate Marketing Plan')

def generate_marketing_plan(company, website, industry, description, goals, budget, audience):
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
            "input_value": ", ".join(goals) if isinstance(goals, list) else goals
        },
        "TextInput-ssGXF": {
            "input_value": str(budget)
        },
        "TextInput-FGepa": {
    "input_value": audience
  }
    }
    
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/generate-plan"
    
    payload = {
        "input_value": "",
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": TWEAKS
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {APPLICATION_TOKEN}"
    }
    
    try:
        print("\n=== Langflow API Request ===")
        print(f"URL: {api_url}")
        print("Payload:", json.dumps(payload, indent=2))
        print("Headers:", {k: v if k != 'Authorization' else '[REDACTED]' for k, v in headers.items()})
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        print("\n=== Langflow API Response ===")
        print(f"Status Code: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
        
        return response.json()["outputs"][0]["outputs"][0]["results"]["text"]["data"]["text"]
    except requests.exceptions.RequestException as e:
        print(f"\n=== Langflow API Error ===")
        print(f"Error making request to API: {str(e)}")
        print(f"Request URL: {api_url}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")
        return None

def normalize_url(url: str) -> str:
    """Normalize URL by adding https:// if missing."""
    url = url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    return url

def scrape_website(url: str) -> dict:
    """Scrape website content and extract relevant information using OpenAI."""
    try:
        print(f"Attempting to scrape website: {url}")
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print("Successfully fetched website")
        except requests.exceptions.SSLError:
            print("SSL Error, trying without verification")
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content from relevant tags
        title = soup.title.string if soup.title else ""
        meta_description = soup.find('meta', {'name': 'description'})
        meta_description = meta_description.get('content', '') if meta_description else ''
        
        # Get text from main content areas
        main_content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'div.about', 'div.company']):
            text = tag.get_text(strip=True)
            if len(text) > 10:  # Only include substantial content
                main_content.append(text)
        
        if not main_content:
            print("Warning: No substantial content found on the page")
            # Try to get any text content as fallback
            main_content = [text for text in soup.stripped_strings if len(text) > 10][:5]
            
        if not main_content:
            raise Exception("No content could be extracted from the website")
        
        # Combine the content
        content = f"""
        Title: {title}
        Meta Description: {meta_description}
        Main Content: {' '.join(main_content[:5])}  # Limit to first 5 substantial paragraphs
        """
        
        print("Content extracted, sending to OpenAI for analysis")
        print(f"Content being sent to OpenAI: {content[:200]}...")  # Print first 200 chars
        
        # Use OpenAI to analyze the content
        try:
            completion = openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a B2B industry analyst expert. Your task is to analyze website content and categorize companies into specific industries. Always select the most appropriate industry from the provided list, even if it's not a perfect match. Return your response as a JSON object WITHOUT markdown formatting."},
                    {"role": "user", "content": f"""Analyze this website content and extract the following information in JSON format:
                    1. Company name
                    2. Industry (IMPORTANT: select the most appropriate industry from this exact list - do not create new ones):
                       {', '.join([f'"{industry[1]}"' for industry in B2B_INDUSTRIES if industry[0]])}
                    3. Company description in 20-40 words. Use your knowledge of the company, reference the website content for updated information and if you don't have enough information. Start with 'Company Name' is a... for...

                    Website Content:
                    {content}

                    Return ONLY a JSON object with these exact keys: company_name, industry, company_description
                    The industry MUST be an EXACT match from the provided list.
                    DO NOT wrap the JSON in markdown code blocks."""}
                ],
                temperature=0.2
            )
            
            print("Received response from OpenAI")
            raw_response = completion.choices[0].message.content
            print(f"Raw OpenAI response: {raw_response}")
            
            # Clean the response if it contains markdown
            cleaned_response = raw_response
            if cleaned_response.startswith('```'):
                cleaned_response = '\n'.join(cleaned_response.split('\n')[1:-1])
            if cleaned_response.startswith('json'):
                cleaned_response = '\n'.join(cleaned_response.split('\n')[1:])
                
            print(f"Cleaned response: {cleaned_response}")
            
            try:
                result = json.loads(cleaned_response)
                print(f"Parsed OpenAI response: {result}")
            except json.JSONDecodeError as e:
                print(f"Error parsing cleaned response: {e}")
                # Try parsing with strict=False as fallback
                result = json.loads(cleaned_response.strip(), strict=False)
                print(f"Parsed response with loose parsing: {result}")
                
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise Exception(f"Error calling OpenAI API: {str(e)}")
        
        try:
            # Validate the response structure
            required_keys = ['company_name', 'industry', 'company_description']
            missing_keys = [key for key in required_keys if key not in result]
            if missing_keys:
                raise Exception(f"Missing required keys in OpenAI response: {missing_keys}")
                
        except json.JSONDecodeError as e:
            print(f"Error parsing OpenAI response: {e}")
            print(f"Raw response: {completion.choices[0].message.content}")
            raise Exception("Invalid JSON response from OpenAI")
        
        # Create a mapping of display names to values
        industry_map = {industry[1]: industry[0] for industry in B2B_INDUSTRIES if industry[0]}
        
        # Convert the industry name to its corresponding value
        if result['industry'] in industry_map:
            result['industry'] = industry_map[result['industry']]
        else:
            # If no exact match, try case-insensitive matching
            industry_lower = result['industry'].lower()
            for display_name, value in industry_map.items():
                if display_name.lower() == industry_lower:
                    result['industry'] = value
                    break
            else:
                print(f"Warning: Industry '{result['industry']}' not found in valid industries")
                result['industry'] = 'software_technology'
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching website: {str(e)}")
        raise Exception(f"Could not access website: {str(e)}")
    except Exception as e:
        print(f"Error in scrape_website: {str(e)}")
        raise

@app.route('/autofill', methods=['POST'])
def autofill():
    try:
        print("\n=== Starting autofill request ===")
        
        # Validate request
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request data: {request.get_data()}")
        
        if not request.is_json:
            print("Error: Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        print(f"Request JSON: {request.json}")
        website_url = request.json.get('url', '').strip()
        if not website_url:
            print("Error: No URL provided")
            return jsonify({"error": "No URL provided"}), 400
            
        print(f"Processing autofill request for URL: {website_url}")
        
        # Normalize the URL
        try:
            website_url = normalize_url(website_url)
            print(f"Normalized URL: {website_url}")
        except Exception as e:
            print(f"Error normalizing URL: {str(e)}")
            return jsonify({"error": f"Invalid URL format: {str(e)}"}), 400
        
        # Analyze the website
        try:
            print("Starting website analysis...")
            result = scrape_website(website_url)
            print(f"Scrape result: {result}")
            
            if not result:
                print("Error: No result from scrape_website")
                return jsonify({"error": "Could not extract information from website"}), 400
                
            # Validate result structure
            required_keys = ['company_name', 'industry', 'company_description']
            missing_keys = [key for key in required_keys if not result.get(key)]
            if missing_keys:
                print(f"Error: Missing keys in result: {missing_keys}")
                return jsonify({"error": f"Missing required information: {', '.join(missing_keys)}"}), 400
                
            print("Successfully processed website")
            return jsonify(result)
            
        except Exception as e:
            error_message = str(e)
            print(f"Error in scrape_website: {error_message}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {e.__dict__}")
            
            if "Could not access website" in error_message:
                return jsonify({"error": error_message}), 400
            elif "SSL" in error_message:
                return jsonify({"error": "Could not securely connect to website"}), 400
            elif "No content could be extracted" in error_message:
                return jsonify({"error": "No content could be extracted from the website"}), 400
            elif "Error calling OpenAI API" in error_message:
                return jsonify({"error": "Error analyzing website content"}), 500
            else:
                return jsonify({"error": "Failed to analyze website"}), 500
                
    except Exception as e:
        print(f"Unexpected error in autofill: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e.__dict__}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/generate-plan', methods=['POST'])
def generate_plan():
    try:
        data = request.get_json()
        
        company = data.get('company_name', '')
        website = data.get('website_url', '')
        industry = data.get('industry', '')
        description = data.get('company_description', '')
        goals = data.get('goals', [])
        budget = data.get('budget', '')
        audience = data.get('target_audience', '')
        
        # Convert goals list to comma-separated string
        goals_str = ", ".join(goals) if isinstance(goals, list) else goals
        
        plan = generate_marketing_plan(company, website, industry, description, goals_str, budget, audience)
        
        # Format the plan as markdown
        formatted_plan = f"""
{plan}
"""
        
        return jsonify({
            'success': True,
            'plan': formatted_plan
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        # Create a PDF document
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Define styles with dark theme colors
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CustomHeading1',
                                parent=styles['Heading1'],
                                fontSize=24,
                                spaceAfter=30,
                                textColor='#FFFFFF',
                                backColor='#212529'))
        styles.add(ParagraphStyle(name='CustomHeading2',
                                parent=styles['Heading2'],
                                fontSize=18,
                                spaceAfter=20,
                                textColor='#E9ECEF',
                                backColor='#212529'))
        styles.add(ParagraphStyle(name='CustomBody',
                                parent=styles['Normal'],
                                fontSize=12,
                                spaceAfter=12,
                                textColor='#E9ECEF',
                                backColor='#212529'))
        
        # Convert HTML to ReportLab elements
        elements = []
        
        # Parse the HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        for element in soup.find_all(['h1', 'h2', 'p', 'ul']):
            if element.name == 'h1':
                elements.append(Paragraph(element.get_text(), styles['CustomHeading1']))
            elif element.name == 'h2':
                elements.append(Paragraph(element.get_text(), styles['CustomHeading2']))
            elif element.name == 'p':
                elements.append(Paragraph(element.get_text(), styles['CustomBody']))
            elif element.name == 'ul':
                for li in element.find_all('li'):
                    bullet_text = '• ' + li.get_text()
                    elements.append(Paragraph(bullet_text, styles['CustomBody']))
        
        # Build the PDF document
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create the response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=marketing_plan.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MarketingPlanForm()
    example_plan = None
    
    if form.validate_on_submit():
        # This is where we'll integrate Langflow later
        # For now, we'll show an example response
        example_plan = {
            'executive_summary': f"Marketing Plan for {form.company_name.data}",
            'company_overview': form.company_description.data,
            'strategy': [
                "Social Media Marketing Campaign",
                "Content Marketing Initiative",
                "Email Marketing Strategy",
                "PPC Advertising"
            ],
            'budget_allocation': {
                'social_media': '30%',
                'content_marketing': '25%',
                'email_marketing': '20%',
                'ppc': '25%'
            },
            'timeline': "12-month implementation plan",
            'kpis': [
                "Increase website traffic by 150%",
                "Generate 50% more qualified leads",
                "Achieve 3x ROI on ad spend",
                "Grow social media engagement by 200%"
            ]
        }
        
    return render_template('index.html', form=form, plan=example_plan)

if __name__ == '__main__':
    app.run(debug=True, port=5050)