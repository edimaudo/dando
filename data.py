from utils import *

# Load data
@st.cache_data
def load_data(DATA_URL):
    data = pd.read_csv(DATA_URL)
    # Convert dates immediately upon loading to save downstream memory
    for col in ['GIFT_DATE', 'CRM_INTERACTION_DATE', 'SENT_DATE']:
        if col in data.columns:
            data[col] = pd.to_datetime(data[col])
    return data

path = "data/"
crm = load_data(path + "CRM_interacions_table.csv")
gift = load_data(path + "gift_transactions_table.csv")
video = load_data(path + "video_email_data_table.csv")

year_list = [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024]
month_list = ['January','February','March','April','May','June','July','August','September','October','November','December']

load_dotenv() 

# Elasticsearch and gemini info
def get_es_client():
    return Elasticsearch(
        os.getenv("ELASTIC_URL"),
        api_key=os.getenv("ELASTIC_API_KEY")
    )

def get_gemini_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@st.cache_data
def run_esql_to_dataframe(query):
    """Executes ES|QL and returns a Pandas DataFrame for the Agent to read."""
    es = get_es_client()
    res = es.esql.query(query=query, format="arrow")
    return res.to_pandas()

# Data transcribed from the provided images
engagement_data = {
    "Donor Portfolio": [
        "Champions", "Loyal Customers", "Potential Loyalist", "Recent Donors",
        "Promising Donors", "Requires Assistance", "Getting Less Frequent",
        "At Risk", "Can't Lose them", "Lost"
    ],
    "Description": [
        "Donors who have visited most recently, visited most frequently and spent the most.",
        "Donors who visited recently visited often and spent a great amount",
        "A recent donor, who spent a good amount",
        "Donors visited most recently, but not often, and have not spent much",
        "Average recency, frequency, and monetary scores",
        "Donors who have spent a good amount but long ago (not visited recently)",
        "Below-average recency, frequency, and monetary values",
        "The donor has spent a great amount and visited often but long ago (not visited recently)",
        "The donor makes large donations and often but has not returned in a long time",
        "Lowest recency, frequency, and monetary scores."
    ],
    "Engagement Strategy": [
        "Reward these", "These donors", "Engage them", "For new donors",
        "Make them loyal", "Need to bring", "The donor will",
        "Listen to their", "Win them back", "Make your presence"
    ]
}

# Creating the DataFrame
engagement_df = pd.DataFrame(engagement_data)


# Gift Data setup
def get_gift_df(gift, years, months):
    df = gift.copy()
    df['GIFT_DATE'] = pd.to_datetime(df['GIFT_DATE'])
    
    # Extract Year, Month, Day of Week
    df['Year'] = df['GIFT_DATE'].dt.year
    df['Month'] = df['GIFT_DATE'].dt.month_name()
    df['DOW'] = df['GIFT_DATE'].dt.day_name()
    
    # Filter based on inputs
    mask = (df['Year'].isin(years) & df['Month'].isin(months))
    return df[mask]

def get_gift_segment_df(gift):
    df = gift.copy()
    df['GIFT_DATE'] = pd.to_datetime(df['GIFT_DATE'])
    
    # Extract Year, Month, Day of Week
    df['Year'] = df['GIFT_DATE'].dt.year
    df['Month'] = df['GIFT_DATE'].dt.month_name()
    df['DOW'] = df['GIFT_DATE'].dt.day_name()
    
    return df





# Customer Segmentation
@st.cache_data
def get_rfm_segments(gift_df, segments_input):
    # 1. Ensure dates are datetime and apply 2015 filter
    #gift_df['GIFT_DATE'] = pd.to_datetime(gift_df['GIFT_DATE'])
    gift_df = gift_df[gift_df['GIFT_DATE'] >= '2015-01-01'].copy()
    
    # 2. Raw RFM Calculation
    analysis_date = gift_df['GIFT_DATE'].max() + pd.Timedelta(days=1)
    
    rfm = gift_df.groupby('CONSTITUENT_ID').agg({
        'GIFT_DATE': lambda x: (analysis_date - x.max()).days,
        'CONSTITUENT_ID': 'count',
        'AMOUNT': 'sum'
    }).rename(columns={
        'GIFT_DATE': 'recency_days',
        'CONSTITUENT_ID': 'transaction_count',
        'AMOUNT': 'amount'
    })

    # 3. Forced Ranking + NaN Protection
    # method='first' ensures no bins collapse, guaranteeing scores 1-5 exist
    rfm['r_score'] = pd.qcut(rfm['recency_days'].rank(method='first'), 5, labels=[5, 4, 3, 2, 1]).astype(float).fillna(0).astype(int)
    rfm['f_score'] = pd.qcut(rfm['transaction_count'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(float).fillna(0).astype(int)
    rfm['m_score'] = pd.qcut(rfm['amount'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(float).fillna(0).astype(int)

# 4. Exhaustive Hierarchical Mapping
    def find_segment(row):
        r, f, m = row['r_score'], row['f_score'], row['m_score']
        
        # CHAMPIONS: Best of the best
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        
        # LOYAL CUSTOMERS: High frequency/money, still active
        elif f >= 4 and r >= 3:
            return "Loyal Customers"
            
        # POTENTIAL LOYALIST: Mid-range, consistent
        elif r >= 3 and f >= 3:
            return "Potential Loyalist"
            
        # PROMISING DONORS: Very recent, but just starting out
        elif r == 5 and f <= 2:
            return "Promising Donors"
            
        # RECENT DONORS: Recent, low frequency
        elif r == 4 and f <= 2:
            return "Recent Donors"
            
        # REQUIRES ASSISTANCE: Former high frequency, but haven't given in a while
        elif r == 2 and f >= 4:
            return "Requires Assistance"
            
        # GETTING LESS FREQUENT: Mid-range frequency, but slipping away
        elif r == 2 and f == 3:
            return "Getting Less Frequent"
            
        # AT RISK: Haven't given in a long time, but were high value
        elif r <= 2 and f >= 3:
            return "At Risk"
            
        # CAN'T LOSE THEM: Long time since last gift, but donated large amounts
        elif r <= 2 and m >= 4:
            return "Can't Lose them"
            
        # LOST: Everyone else (Low Recency, Low Frequency, Low Money)
        else:
            return "Lost"

    rfm['segment'] = rfm.apply(find_segment, axis=1)

    # 5. Filter based on user selection
    return rfm[rfm['segment'].isin(segments_input)]




def get_final_filtered_data(gift, rfm_output, segments_input):
    # Ensure dates are datetime for the filter to work
    gift['GIFT_DATE'] = pd.to_datetime(gift['GIFT_DATE'])
    
    # Process the chain
    final_df = (
        gift[gift['GIFT_DATE'] >= '2015-01-01']
        .merge(rfm_output, on='CONSTITUENT_ID', how='inner')
        .loc[lambda x: x['segment'].isin(segments_input)] # Alternative filter method
        .loc[:, ['CONSTITUENT_ID', 'segment', 'GIFT_DATE', 'AMOUNT']]
        .dropna()
    )
    
    return final_df

# forecasting
def forecast_donations(gifts_segment_df, horizon):
    # Resample to monthly sums
    monthly = gifts_segment_df.set_index('GIFT_DATE')['AMOUNT'].resample('MS').sum()
    
    # Fit ARIMA model
    model = auto_arima(monthly, seasonal=True, m=12)
    forecast, conf_int = model.predict(n_periods=horizon, return_conf_int=True)
    
    # Create forecast dataframe
    forecast_dates = pd.date_range(start=monthly.index[-1] + pd.DateOffset(months=1), 
                                   periods=horizon, freq='MS')
    
    return pd.DataFrame({
        'Month': forecast_dates,
        'Forecasted Donations': forecast.values.round(1)
    })


# def get_elastic_agent_response(inference_id, user_input, context_df=None):
#     """
#     Calls an agent defined in the Elasticsearch Agent Builder.
#     """
#     es = get_es_client()
    
#     # 1. Prepare context (converts DataFrame to a readable string for the AI)
#     context_str = context_df.to_json() if context_df is not None else "No data provided."
    
#     # 2. Call the Inference API
#     # Note: 'chat_completion' is the standard task_type for Agents
#     response = es.inference.inference(
#         inference_id=inference_id,
#         task_type="chat_completion", 
#         input=f"DATA CONTEXT: {context_str}\n\nUSER REQUEST: {user_input}"
#     )
    
#     # 3. Extract the result safely
#     # For Agent Builder, the response usually lives here:
#     try:
#         return response['completion'][0]['result']
#     except (KeyError, IndexError):
#         # Fallback for different provider response structures
#         return response.get('result', "Agent connected, but no text was returned.")

def get_elastic_agent_response(inference_id, user_input, context_df=None):
    es = get_es_client()
    context_str = context_df.to_json() if context_df is not None else "No data provided."
    
    # Using 'chat' matches the Agent Builder UI requirement
    response = es.inference.inference(
        inference_id=inference_id,
        task_type="chat", 
        input=f"DATA CONTEXT: {context_str}\n\nUSER REQUEST: {user_input}"
    )
    return response['completion'][0]['result']

def call_elastic_agent(inference_id, user_input, context_df):
    """
    Generic bridge to the Elastic Agent Builder.
    inference_id: matches the name you saved in the Elastic UI.
    """
    es = get_es_client()
    
    # Format data for the agent's context
    context_str = context_df.to_json()
    
    response = es.inference.inference(
        inference_id=inference_id,
        task_type="chat",
        input=f"CONTEXT DATA: {context_str}\n\nUSER REQUEST: {user_input}"
    )
    
    # Return the text generated by the agent
    return response['completion'][0]['result']