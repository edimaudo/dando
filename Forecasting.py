from utils import *
from data import *

st.title(APP_NAME)
st.header(FORECASTING_HEADER)

with st.sidebar:
    donor_segment_input = st.multiselect("Donor Segment", engagement_df['Donor Portfolio'],engagement_df['Donor Portfolio'])
    forecast_horizon_input = st.slider("Forecast Horizon (in months)", min_value=1, max_value=24, value=12, step=1)


@st.cache_data
def get_processed_segment_data(selected_segments):
    """
    Optimized merge: Filters before joining and caches the result 
    to prevent memory spikes on every interaction.
    """
    # Calculate RFM only for segments selected in sidebar
    rfm_sub = get_rfm_segments(gift, selected_segments)
    
    # Filter 'gift' by date first to reduce the memory footprint of the merge
    processed_df = (
        gift[gift['GIFT_DATE'] >= '2015-01-01']
        .merge(rfm_sub, on='CONSTITUENT_ID', how='inner')
        .loc[:, ['CONSTITUENT_ID', 'segment', 'GIFT_DATE', 'AMOUNT']]
        .dropna()
    )
    return processed_df

@st.cache_data
def get_cached_forecast(df, horizon):
    """Caches the statistical model to save CPU and RAM."""
    monthly_df = get_gift_segment_df(df)
    return forecast_donations(monthly_df, horizon)

rfm_df = get_rfm_segments(gift, donor_segment_input)
forecast_df = get_cached_forecast(get_processed_segment_data(donor_segment_input) , forecast_horizon_input)

tab1, tab2 = st.tabs(['Donation Forecasting',"Donation Forecast Agent"])
with tab1:
    # plot forecast chart
    st.plotly_chart(create_forecast_chart(forecast_df))
    # forecast chart table
    st.plotly_chart(create_forecast_table(forecast_df))

with tab2:
    st.subheader("Donation Amount Insights")
    st.write(f"This agent evaluates the sustainability of a {forecast_horizon_input}-month growth trend by querying record-level history in Elasticsearch.")
    
    if st.button("Run Strategic Analysis"):
        # 1. THE BRIDGE: Identify IDs from the local Python segments
        target_ids = rfm_df['CONSTITUENT_ID'].unique().tolist()
        
        if not target_ids:
            st.error("No donors found in the selected segments.")
        else:
            with st.spinner("Accessing Elastic and consulting Gemini..."):
                # 2. Format IDs for ES|QL (limiting to 1000 for query efficiency)
                ids_str = ", ".join([f"'{str(i)}'" for i in target_ids[:1000]])
                
                # 3. DYNAMIC ES|QL: Matches the historical window to your forecast horizon
                es_query = f"""
                FROM gift_transactions
                | WHERE CONSTITUENT_ID IN ({ids_str})
                | EVAL month = DATE_TRUNC(1 MONTH, GIFT_DATE)
                | STATS total_rev = SUM(AMOUNT), donor_count = COUNT_DISTINCT(CONSTITUENT_ID) BY month
                | SORT month DESC
                | LIMIT {forecast_horizon_input}
                """
                
                # 4. Fetch and Analyze
                raw_data = run_esql_to_dataframe(es_query)
                client = get_gemini_client()
                
                prompt = f"""
                System: You are a Non-Profit CFO and data scientist. 
                User Input: Analyzing segments: {donor_segment_input}. 
                Forecast Horizon: {forecast_horizon_input} months.
                
                Data from Elasticsearch (Last {forecast_horizon_input} months):
                {raw_data}
                
                Task: 
                1. Identify if revenue velocity is increasing or decreasing for these IDs.
                2. Evaluate if the donor count supports the current forecast.
                3. Recommend one specific stewardship action for the {donor_segment_input} groups.
                """
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=prompt
                )
                
                st.info(f"Donation Data for {len(target_ids[:1000])} donors retrieved via ES|QL.")
                st.markdown("### Strategic Outlook")
                st.write(response.text)