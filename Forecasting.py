from utils import *
from data import *
from data_plot import *

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
        with st.spinner("Accessing Elastic Agent..."):
            es_query = f"""
                        FROM gift_transactions 
                        | STATS SUM(AMOUNT) BY BUCKET(GIFT_DATE, 1 month) 
                        | SORT GIFT_DATE DESC 
                        | LIMIT {forecast_horizon_input}
                        """
            raw_data = run_esql_to_dataframe(es_query)
            
            # Call the Forecast Agent
            agent_insight = get_elastic_agent_response(
                inference_id="revenue-forecaster-agent",
                user_input=f"Analyze the {forecast_horizon_input} month outlook.",
                context_df=raw_data
            )
            
            st.info("Analysis retrieved from Elastic Agent Builder.")
            st.markdown(f"### Strategic Outlook\n{agent_insight}")