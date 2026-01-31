from utils import *
from data import *

st.title(APP_NAME)
st.header(FORECASTING_HEADER)

with st.sidebar:
    st.multiselect("Donor Segment", engagement_df['Donor Portfolio'],engagement_df['Donor Portfolio'])