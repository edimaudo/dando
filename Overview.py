from utils import *
from data import *

st.title(APP_NAME)
st.header(OVERVIEW_HEADER)


with st.sidebar():
    year_selection = st.multiselect("Year", year_list,default=year_list)
    month_selection = st.multiselect("Month",month_list,default=month_list)


