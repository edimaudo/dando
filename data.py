from utils import *

# Load data
@st.cache_data
def load_data(DATA_URL):
    """Loads files based on file type (CSV only)."""
    data = pd.read_csv(DATA_URL)
    return data

path = "data/"
crm = load_data(path + "CRM_interacions_table.csv")
gift = load_data(path + "gift_transactions_table.csv")
video = load_data(path + "video_email_data_table.csv")

year_list = [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024]
month_list = ['January','February','March','April','May','June','July','August','September','October','November','December']

