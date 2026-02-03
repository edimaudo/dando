from utils import *

class DonorAgentService:
    def __init__(self):
        self.ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.es_client = Elasticsearch(os.getenv("ELASTIC_URL"), api_key=os.getenv("ELASTIC_API_KEY"))

    # AGENT 1: Major Gift Pipeline (Prioritization)
    def run_pipeline_agent(self):
        query = """
        FROM constituent_profiles
        | WHERE CAPACITY_ESTIMATE IS NOT NULL 
        | WHERE LIFETIME_GIVING < 50000
        | SORT CAPACITY_ESTIMATE DESC
        | LIMIT 10
        """
        res = self.es_client.esql.query(query=query, format="arrow")
        df = res.to_pandas()
        
        prompt = f"Identify the top 3 prospects from this list for a 'Discovery Visit': {df.to_json()}. Focus on the gap between capacity and current giving."
        analysis = self.ai_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return df, analysis.text

    # AGENT 2: Stewardship Velocity (Health Check)
    def run_velocity_agent(self):
        query = """
        FROM constituent_profiles
        | EVAL ratio = LIFETIME_GIFT_COUNT / (LIFETIME_CRM_INTERACTIONS + 1.0)
        | WHERE ratio > 3.0 AND LAST_GIFT_DATE > NOW() - INTERVAL 90 DAY
        | SORT ratio DESC
        | LIMIT 5
        """
        res = self.es_client.esql.query(query=query, format="arrow")
        df = res.to_pandas()
        
        prompt = f"Analyze these 'transactional' donors: {df.to_json()}. Why is a high gift-to-interaction ratio a risk for long-term retention?"
        analysis = self.ai_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return df, analysis.text

    # AGENT 3: Campaign Simulator (What-If)
    def run_simulator(self, crm_type, min_cap):
        # We query Elastic to see how many donors meet the 'What-if' criteria
        query = f"""
        FROM constituent_profiles
        | WHERE CAPACITY_ESTIMATE IS NOT NULL
        | STATS total_pool = COUNT(CONSTITUENT_ID)
        """
        # Note: In a real app, you'd parse your capacity strings to numeric values first
        res = self.es_client.esql.query(query=query, format="arrow")
        count = res.to_pandas()['total_pool'].iloc[0]
        
        prompt = f"Simulate a {crm_type} campaign for {count} high-capacity donors. " \
                 "What is the projected emotional and financial ROI? Provide a 3-sentence summary."
        analysis = self.ai_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return count, analysis.text

    # AGENT 4: The Closer (Hyper-Personalized Outreach)
    def get_closer_draft(self, donor_id):
        # Fetch the specific context for RAG
        donor = self.es_client.get(index="constituent_profiles", id=donor_id)['_source']
        
        prompt = f"Draft a personalized email for Donor {donor_id}. Context: " \
                 f"Last gift: {donor['LAST_GIFT_DATE']}, " \
                 f"Total Giving: ${donor['LIFETIME_GIVING']}, " \
                 f"Last Interaction: {donor['LAST_CRM_INTERACTION_DATE']}. " \
                 "Reference these dates to show we are paying attention."
        
        draft = self.ai_client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return draft.text