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

# --- 3. THE "STABLE" NAVIGATION ---
# Replacing st.tabs with a keyed radio to prevent the "jump" behavior
view_selection = st.radio(
    "Navigation",
    ["Donation Forecast", "Donation Modeling Agent"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# --- 4. VIEW LOGIC ---
if view_selection == "Donation Forecast":
    # Visualizations
    st.plotly_chart(create_forecast_chart(forecast_df))
    st.plotly_chart(create_forecast_table(forecast_df))

elif view_selection == "Donation Modeling Agent":
    st.subheader("CFO Strategic Outlook")
    st.write(f"The Agent is analyzing the {forecast_horizon_input}-month projected trend.")

    # Execute Analysis
    if st.button("Run Strategic Analysis"):
        with st.spinner("Donation Modeling Agent is reviewing the forecast..."):
            try:
                agent_insight = call_forecast_agent(
                forecast_df=forecast_df,
                horizon=forecast_horizon_input,
                user_request="Summarize the donation trend, see if the trend is sustainabile and could meet donation target."
            )
                
                st.success("Strategic Analysis Retrieved")
                st.markdown(agent_insight)
                
            except Exception as e:
                print(e)
                st.error("Donation Modeling Agent is currently unavailable. Please try again.")