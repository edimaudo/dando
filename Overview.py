from utils import *
from data import *
from data_plot import *

st.title(APP_NAME)
st.header(OVERVIEW_HEADER)


with st.sidebar:
    year_selection = st.multiselect("Year", year_list,default=year_list)
    month_selection = st.multiselect("Month",month_list,default=month_list)

gift_df = get_gift_df(gift,year_selection,month_selection)
crm_df = crm
video_df = get_video_stats(video, year_selection, month_selection)

tab1, tab2, tab3, tab4 = st.tabs(["Donor Relationship", "Engagement",'Giving Level',"Online Performance"])

with tab1:
    # donor growth rate
    st.plotly_chart(plot_donor_growth(gift_df))
    # donor teturn & Churn rate
    st.plotly_chart(get_donor_rates(gift_df))
with tab2:
    # gift CRM plot
    st.plotly_chart(plot_gift_crm(gift_df,crm_df))
    # CRM plot
    st.plotly_chart(crm_outreach_plot(crm_df,year_selection,month_selection))
with tab3:
    # Donation Amount per year
    st.plotly_chart(plot_gift_year(gift_df))
    # Donation Count per year
    st.plotly_chart(plot_gift_year_count(gift_df))
    # Yearly Donation Growth
    st.plotly_chart(plot_gift_year_growth(gift_df))
    # Donation Amount Per Month
    st.plotly_chart(plot_gift_time_period(gift_df, "Month"))
    # Donation Amount Per Day of Week
    st.plotly_chart(plot_gift_time_period(gift_df, "DOW"))
with tab4:
     # video views per year
    st.plotly_chart(plot_video_views(video_df))
     # # of clicks per year
    st.plotly_chart(plot_video_clicks(video_df))
     # bounce and unsubscribe rate per year
    st.plotly_chart(plot_bounce_unsub_rate(video_df))