from utils import *
from data import *
from donor_agent_service import DonorAgentService

st.title(APP_NAME)
st.header(SEGMENTATION_HEADER)

with st.sidebar:
    donor_segment_input = st.multiselect("Donor Segment", engagement_df['Donor Portfolio'],engagement_df['Donor Portfolio'])

@st.cache_data
def get_processed_segment(selected_segments):
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

crm_df = crm
rfm_df = get_rfm_segments(gift, donor_segment_input)
gift_segment_df = get_gift_segment_df(get_processed_segment(donor_segment_input))


tab1, tab2, tab3, tab4,tab5 = st.tabs(['Donor Portfolio',"Donor Relationship", "Engagement",'Giving Level',"Segment Agent"])
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
    relevant_ids = rfm_df['CONSTITUENT_ID'].unique().tolist()
    
    if not relevant_ids:
        st.warning("No donors found in these segments to analyze.")
    else:
        # Create a safe ID string for ES|QL (limiting to 1000 for performance)
        ids_for_query = ", ".join([f"'{str(i)}'" for i in relevant_ids[:1000]])
        
        # 2. AGENT SELECTION
        agent_choice = st.radio(
            "Select Active Agent",
            ["Major Gift Pipeline", "Donor Relationship Health", "Campaign Simulator"],
            horizontal=True
        )
        st.divider()

        # --- AGENT 1: MAJOR GIFT PIPELINE ---
        if agent_choice == "Major Gift Pipeline":
            st.write("### Pipeline Agent")
            if st.button("Identify Hidden Capacity"):
                with st.spinner("Querying constituent profiles in Elastic..."):
                    # We query the 'constituent_profiles' index for the people in our local segment
                    query = f"""
                    FROM constituent_profiles
                    | WHERE CONSTITUENT_ID IN ({ids_for_query})
                    | WHERE CAPACITY_ESTIMATE > 50000
                    | KEEP CONSTITUENT_ID, CAPACITY_ESTIMATE, WEALTH_SCORE
                    | SORT CAPACITY_ESTIMATE DESC
                    | LIMIT 10
                    """
                    df = run_esql_to_dataframe(query)
                    st.dataframe(df, use_container_width=True)
                    
                    # AI Analysis
                    client = get_gemini_client()
                    prompt = f"Analyze these high-capacity donors from our {donor_segment_input} segments: {df.to_json()}. Who is the #1 priority for a discovery call today?"
                    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                    st.info(f"**Agent Priority Strategy:** {response.text}")

        # --- AGENT 2: STEWARDSHIP VELOCITY ---
        elif agent_choice == "Donor Relationship Health":
            st.write("### Stewardship Heartbeat")
            if st.button("Check Donor Health"):
                with st.spinner("Analyzing interaction density..."):
                    query = f"""
                    FROM gift_transactions
                    | WHERE CONSTITUENT_ID IN ({ids_for_query})
                    | STATS total_gifts = COUNT(*), last_gift = MAX(GIFT_DATE) BY CONSTITUENT_ID
                    | SORT total_gifts DESC
                    | LIMIT 5
                    """
                    df = run_esql_to_dataframe(query)
                    
                    client = get_gemini_client()
                    prompt = f"Review these donor patterns: {df.to_json()}. If they are in the {donor_segment_input} group but haven't been contacted lately, what's our retention risk?"
                    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                    st.warning(f"**Retention Risk Analysis:** {response.text}")

        # --- AGENT 3: CAMPAIGN SIMULATOR ---
        elif agent_choice == "Campaign Simulator":
            st.write("### Strategy Lab")
            target_amount = st.number_input("Target Raise ($)", value=25000)
            if st.button("Simulate Campaign Impact"):
                donor_count = len(relevant_ids)
                avg_gift = gift_segment_df['AMOUNT'].mean()
                
                client = get_gemini_client()
                prompt = f"We have {donor_count} donors in the {donor_segment_input} segments with an average gift of ${avg_gift:.2f}. Can we raise ${target_amount} with a 5% response rate?"
                response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                st.success(f"**Simulation Result:** {response.text}")
