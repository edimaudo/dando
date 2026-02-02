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