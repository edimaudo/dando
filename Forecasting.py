from utils import *
from data import *

st.title(APP_NAME)
st.header(FORECASTING_HEADER)



with st.sidebar:
    donor_segment_input = st.multiselect("Donor Segment", engagement_df['Donor Portfolio'],engagement_df['Donor Portfolio'])
    forecast_horizon_input = st.slider("Forecast Horizon (in months)", min_value=1, max_value=24, value=12, step=1)

rfm_df = get_rfm_segments(gift, donor_segment_input)
gift_segment_df1 = (
    gift[gift['GIFT_DATE'] >= '2015-01-01']                     # 1. Filter
    .merge(rfm_df , on='CONSTITUENT_ID', how='inner')       # 2. Inner Join
    .loc[:, ['CONSTITUENT_ID', 'segment', 'GIFT_DATE', 'AMOUNT']] # 3. Select columns
    .dropna()                                                   # 4. na.omit()
)
gift_segment_df = get_gift_segment_df(gift_segment_df1)
forecast_df = forecast_donations(gift_segment_df, forecast_horizon_input)

tab1, tab2 = st.tabs(['Donation Forecasting',"Donation Forecast Agent"])
with tab1:
    # plot forecast chart
    st.plotly_chart(create_forecast_chart(forecast_df))
    # forecast chart table
    st.plotly_chart(create_forecast_table(forecast_df))

with tab2:
    st.subheader("Forecast Agent")
    
    if st.button("Query Elasticsearch & Analyze"):
        with st.spinner(f"Fetching last {forecast_horizon_input} months from Elastic..."):
            # 1. Format segments for the query
            segments_str = ", ".join([f"'{s}'" for s in donor_segment_input])
            
            # 2. DYNAMIC ES|QL Query
            # We now use the forecast_horizon_input to determine how much history to fetch
            es_query = f"""
            FROM gift_transactions
            | WHERE segment IN ({segments_str})
            | EVAL month = DATE_TRUNC(1 MONTH, GIFT_DATE)
            | STATS total_rev = SUM(AMOUNT), donor_count = COUNT_DISTINCT(CONSTITUENT_ID) BY month
            | SORT month DESC
            | LIMIT {forecast_horizon_input} 
            """
            
            # 3. Execute and Analyze
            raw_data = run_esql_query(es_query)
            client = get_gemini_client()
            
            prompt = f"""
            System: You are a Non-Profit Data Scientist.
            Context: The user is looking at a {forecast_horizon_input}-month forecast.
            Historical Data (Last {forecast_horizon_input} months): {raw_data}
            
            Task: Based on this historical data from Elasticsearch, evaluate if a 
            {forecast_horizon_input}-month growth trend is sustainable for the {donor_segment_input} segments.
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt
            )
            
            st.info(f"Analyzing {forecast_horizon_input} months of donation data via ES|QL.")
            st.markdown(response.text)