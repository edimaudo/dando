from utils import *
from data import *

st.title(APP_NAME)
st.header(OVERVIEW_HEADER)


with st.sidebar:
    year_selection = st.multiselect("Year", year_list,default=year_list)
    month_selection = st.multiselect("Month",month_list,default=month_list)

gift_df = get_gift_df(gift,year_selection,month_selection)

tab1, tab2, tab3, tab4 = st.tabs(["Donor Relationship", "Engagement",'Giving Level',"Online Performance"])

with tab1:
    # donor growth rate
    st.plotly_chart(plot_donor_growth(gift_df))
    # donor teturn & Churn rate
    st.plotly_chart(get_donor_rates(gift_df))
with tab2:
    # gift CRM plot
    
    # CRM plot

#with tab3:
    # Donation Amount per year

    # Donation Count per year

    # Yearly Donation Growth

    # Donation Amount Per Month

    # Donation Amount Per Day of Week

#with tab4:
     # video views per year

     # # of clicks per year

     # bounce and unsubscribe rate per year
