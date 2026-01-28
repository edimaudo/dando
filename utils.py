"""
Libraries
"""
import streamlit as st
import pandas as pd
import numpy as np
import os, os.path
import warnings
import random
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import datetime
from datetime import datetime
import time
import matplotlib
import statistics
import scipy
from scipy.stats import linregress
import sklearn
from sklearn.linear_model import LinearRegression
from pmdarima import auto_arima

"""
App Information
"""
APP_NAME = 'Dando'
ABOUT_HEADER = 'About'
OVERVIEW_HEADER = 'Overview'
SEGMENTATION_HEADER = "Donor Segmentation"
FORECASTING_HEADER = 'Donation Forecasting'
APP_FILTERS = 'Filters'
NO_DATA_INFO = 'No data available to display based on the filters'

warnings.simplefilter(action='ignore', category=FutureWarning)
st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)
