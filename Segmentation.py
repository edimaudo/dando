from utils import *
from data import *
from data_plot import *

st.title(APP_NAME)
st.header(SEGMENTATION_HEADER)

with st.sidebar:
    donor_segment_input = st.multiselect("Donor Segment", engagement_df['Donor Portfolio'],engagement_df['Donor Portfolio'])

@st.cache_data
def get_processed_segment(selected_segments):
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

crm_df = crm
rfm_df = get_rfm_segments(gift, donor_segment_input)
gift_segment_df = get_gift_segment_df(get_processed_segment(donor_segment_input))


tab1, tab2, tab3, tab4,tab5 = st.tabs(['Donor Portfolio',"Donor Relationship", "Donor Engagement",'Donor Giving Level',"Donor Segment Agent"])
with tab1:
    # rfm treemap
    st.plotly_chart(plot_rfm_treemap(rfm_df))
    # engagement strategy
    st.table(engagement_df)
with tab2:
    # donor growth rate
    st.plotly_chart(plot_donor_growth(gift_segment_df))
    # donor teturn & Churn rate
    st.plotly_chart(get_donor_rates(gift_segment_df))
with tab3:
    # gift CRM plot
    st.plotly_chart(plot_gift_crm(gift_segment_df,crm_df))
with tab4:
    # Donation Amount per year
    st.plotly_chart(plot_gift_year(gift_segment_df))
    # Donation Count per year
    st.plotly_chart(plot_gift_year_count(gift_segment_df))
    # Yearly Donation Growth
    st.plotly_chart(plot_gift_year_growth(gift_segment_df))
    # Donation Amount Per Month
    st.plotly_chart(plot_gift_time_period(gift_segment_df, "Month"))
    # Donation Amount Per Day of Week
    st.plotly_chart(plot_gift_time_period(gift_segment_df, "DOW"))
with tab5:
    st.subheader("Segmentation Agentic Insights")
    
    # 1. THE BRIDGE: Get IDs from the locally calculated RFM segments
    # This ensures the Agent is looking at the exact donors you see in the charts
    relevant_ids = gift_segment_df['CONSTITUENT_ID'].unique().tolist()
    
    if not relevant_ids:
        st.warning("No donors found in these segments to analyze.")
    else:
        # Create a safe ID string for ES|QL (limiting to 1000 for performance)
        ids_for_query = ", ".join([str(id) for id in relevant_ids[:5]])
        
        # 2. AGENT SELECTION
        agent_choice = st.radio(
            "Select Active Agent",
            ["Major Gift Pipeline", "Donor Relationship Health"],
            horizontal=True
        )
        st.divider()

        # --- AGENT 1: MAJOR GIFT PIPELINE ---
        if agent_choice == "Major Gift Pipeline":
            st.write("### Pipeline Agent")
            if st.button("Identify Hidden Capacity"):
                with st.spinner("Consulting Elastic AI Agent..."):
                    # 1. Get the raw data from ES|QL
                    query = f"FROM constituent_profiles | WHERE CONSTITUENT_ID IN ({ids_for_query}) | LIMIT 10"
                    df = run_esql_to_dataframe(query)
                    
                    
                    # agent_insight = get_elastic_agent_response(
                    #     inference_id="major-gift-agent", 
                    #     user_input="Who is the #1 priority for discovery?",
                    #     context_df=df
                    # )
                    agent_insight = call_agent("major-gift-agent","Who is the #1 priority for discovery?",df)
                    st.info(f"**Agent Priority Strategy:** {agent_insight}")

        # --- AGENT 2: STEWARDSHIP VELOCITY ---
        elif agent_choice == "Donor Relationship Health":
            st.write("### Donor Heartbeat")
            if st.button("Check Donor Health"):
                with st.spinner("Analyzing via Elastic..."):
                    # Fetch data and pass to your Retention Agent ID
                    query = f"FROM gift_transactions | WHERE CONSTITUENT_ID IN ({ids_for_query}) | LIMIT 5"
                    df = run_esql_to_dataframe(query)
                    
                    # agent_insight = get_elastic_agent_response(
                    #     inference_id="retention-risk-agent", 
                    #     user_input="Analyze these donor patterns for risk.",
                    #     context_df=df
                    #)
                    agent_insight = call_agent("retention-risk-agent","Analyze these donor patterns for risk.",df)

                    st.warning(f"**Retention Risk Analysis:** {agent_insight}")

