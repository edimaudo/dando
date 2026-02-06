from utils import *
from data import *
from data_plot import *

st.title(APP_NAME)
st.header(SEGMENTATION_HEADER)

with st.sidebar:
    donor_segment_input = st.multiselect("Donor Segment", engagement_df['Donor Portfolio'], engagement_df['Donor Portfolio'])

@st.cache_data
def get_processed_segment(selected_segments):
    rfm_sub = get_rfm_segments(gift, selected_segments)
    processed_df = (
        gift[gift['GIFT_DATE'] >= '2015-01-01']
        .merge(rfm_sub, on='CONSTITUENT_ID', how='inner')
        .loc[:, ['CONSTITUENT_ID', 'segment', 'GIFT_DATE', 'AMOUNT']]
        .dropna()
    )
    return processed_df

crm_df = crm
rfm_df = get_rfm_segments(gift, donor_segment_input)
gift_segment_df = get_gift_segment_df(get_processed_segment(donor_segment_input))

# --- 1. STABLE NAVIGATION (Replacing st.tabs) ---
view_selection = st.radio(
    "Navigation",
    ["Donor Portfolio", "Donor Relationship", "Donor Engagement", "Donor Giving Level", "Donor Segment Agents"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# --- 2. VIEW LOGIC ---
if view_selection == "Donor Portfolio":
    st.plotly_chart(plot_rfm_treemap(rfm_df))
    st.table(engagement_df)

elif view_selection == "Donor Relationship":
    st.plotly_chart(plot_donor_growth(gift_segment_df))
    st.plotly_chart(get_donor_rates(gift_segment_df))

elif view_selection == "Donor Engagement":
    st.plotly_chart(plot_gift_crm(gift_segment_df, crm_df))

elif view_selection == "Donor Giving Level":
    st.plotly_chart(plot_gift_year(gift_segment_df))
    st.plotly_chart(plot_gift_year_count(gift_segment_df))
    st.plotly_chart(plot_gift_year_growth(gift_segment_df))
    st.plotly_chart(plot_gift_time_period(gift_segment_df, "Month"))
    st.plotly_chart(plot_gift_time_period(gift_segment_df, "DOW"))

elif view_selection == "Donor Segment Agents":
    st.subheader("Segmentation Insights")
    
    # 3. THE BRIDGE: Get IDs from the locally calculated RFM segments
    relevant_ids = gift_segment_df['CONSTITUENT_ID'].unique().tolist()
    
    if not relevant_ids:
        st.warning("No donors found in these segments to analyze.")
    else:
        # Create a safe ID string for ES|QL (numeric)
        ids_for_query = ", ".join([str(id) for id in relevant_ids[:5]])
        
        agent_choice = st.radio(
            "Select Active Agent",
            ["Major Gift Pipeline", "Donor Relationship Health","Campaign Simulator"],
            horizontal=True
        )
        st.divider()

        # --- AGENT 1: MAJOR GIFT PIPELINE ---
        if agent_choice == "Major Gift Pipeline":
            st.write("### Pipeline Agent")
            if st.button("Identify Hidden Capacity"):
                with st.spinner("Consulting AI Agent..."):
                    query = f"FROM constituent_profiles | WHERE CONSTITUENT_ID IN ({ids_for_query}) | LIMIT 10"
                    df = run_esql_to_dataframe(query)
                    agent_insight = call_agent("major-gift-agent", "Who is the #1 priority for discovery?", df)
                    st.info(f"**Agent Priority Strategy:** {agent_insight}")

        # --- AGENT 2: RELATIONSHIP HEALTH ---
        elif agent_choice == "Donor Relationship Health":
            st.write("### Donor Heartbeat")
            if st.button("Check Donor Health"):
                with st.spinner("Analyzing Donor Patterns..."):
                    # Use gift_date (lowercase) to avoid the BadRequestError seen in Forecasting
                    query = f"FROM gift_transactions | WHERE CONSTITUENT_ID IN ({ids_for_query}) | LIMIT 5"
                    df = run_esql_to_dataframe(query)
                    agent_insight = call_agent("retention-risk-agent", "Analyze these donor patterns for risk.", df)
                    st.warning(f"**Retention Risk Analysis:** {agent_insight}")
        
        # --- AGENT 3: CAMPAIGN SIMULATOR ---
        elif agent_choice == "Campaign Simulator":
            st.write("### Strategy Lab")
            st.info("Simulate ROI based on your current filtered donor pool.")

            # 1. Slider for Target Amount
            target_amount = st.slider(
                "Target Raise ($)", 
                min_value=100000, 
                max_value=1000000, 
                value=250000, 
                step=50000
            )
    
            if st.button("Simulate Campaign Impact"):
                donor_count = len(relevant_ids)
                donation_amt  = gift_segment_df['AMOUNT'].sum() if not gift_segment_df.empty else 0
                
                with st.spinner("Running simulation models..."):
                    simulation_insight = call_agent(
                        agent_key="campaign-simulator-agent",
                        user_request=f"Target: ${target_amount}. Segment: {donor_segment_input}. Context: {donor_count} donors, ${donation_amt:.2f} total donation amount.",
                        context_df=None  # We pass the stats in the request to keep it fast
                    )
                    
                    # Display result in a professional card
                    st.subheader("Simulation Results")
                    st.markdown(simulation_insight)