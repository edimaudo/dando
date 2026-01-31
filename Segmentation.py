from utils import *
from data import *

st.title(APP_NAME)
st.header(SEGMENTATION_HEADER)

with st.sidebar:
    donor_segment_input = st.multiselect("Donor Segment", engagement_df['Donor Portfolio'],engagement_df['Donor Portfolio'])

crm_df = crm
rfm_df = get_rfm_segments(gift, donor_segment_input)
gift_segment_df1 = (
    gift[gift['GIFT_DATE'] >= '2015-01-01']                     # 1. Filter
    .merge(rfm_df , on='CONSTITUENT_ID', how='inner')       # 2. Inner Join
    .loc[:, ['CONSTITUENT_ID', 'segment', 'GIFT_DATE', 'AMOUNT']] # 3. Select columns
    .dropna()                                                   # 4. na.omit()
)
gift_segment_df = get_gift_segment_df(gift_segment_df1)


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