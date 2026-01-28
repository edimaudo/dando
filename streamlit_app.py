from utils import *

pg = st.navigation([
    st.Page("About.py"),
    st.Page("Overview.py"),
    st.Page("Segmentation.py"),
    st.Page("Forecasting.py"),
])
pg.run()
