from utils import *

class DonorAgentService:
    def __init__(self):
        # Initialize Google GenAI Client
        self.ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Initialize Elasticsearch 9.x Client
        self.es_client = Elasticsearch(
            os.getenv("ELASTIC_URL"),
            api_key=os.getenv("ELASTIC_API_KEY")
        )

    def get_major_gift_pipeline(self, target_segment="Champions"):
        """Uses ES|QL to find top prospects and Gemini to summarize the 'Why'."""
        
        # 1. Native ES|QL Query (Power of Elastic 9.x)
        query = f"""
        FROM donor_profiles
        | WHERE segment == '{target_segment}'
        | STATS total_given = SUM(lifetime_giving) BY constituent_id, capacity_estimate
        | SORT total_given DESC
        | LIMIT 5
        """
        
        res = self.es_client.esql.query(query=query, format="arrow")
        df = res.to_pandas()

        # 2. Native Gemini Call (Native google-genai 1.61.0)
        prompt = f"Analyze these top prospects for a major gift campaign: {df.to_json()}. " \
                 "Identify the top 3 and explain why their giving history makes them 'ready' now."
        
        response = self.ai_client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return df, response.text

    def generate_personalized_outreach(self, donor_id):
        """Fetches donor context and uses Gemini to draft a bespoke email."""
        
        # Fetch donor context from Elastic
        donor_data = self.es_client.get(index="donor_profiles", id=donor_id)['_source']
        
        prompt = f"Draft a personalized email to donor {donor_data['name']}. " \
                 f"They are a {donor_data['segment']} who recently gave ${donor_data['last_gift_amount']}. " \
                 "Tone: Warm, urgent, and focused on the impact of their gift."
        
        response = self.ai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text