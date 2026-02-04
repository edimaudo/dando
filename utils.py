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
from google import genai
from elasticsearch import Elasticsearch
from dotenv import load_dotenv, dotenv_values 
load_dotenv() 

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

def get_es_client():
    return Elasticsearch(
        os.getenv("ELASTIC_URL"),
        api_key=os.getenv("ELASTIC_API_KEY")
    )

def get_gemini_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_esql_to_dataframe(query):
    """Executes ES|QL and returns a Pandas DataFrame for the Agent to read."""
    es = get_es_client()
    res = es.esql.query(query=query, format="arrow")
    return res.to_pandas()