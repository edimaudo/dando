from utils import *

# Load data
@st.cache_data
def load_data(DATA_URL):
    """Loads files based on file type (CSV only)."""
    data = pd.read_csv(DATA_URL)
    return data

path = "data/"
constituent = load_data(path + "constituent_profiles_table.csv")
crm = load_data(path + "CRM_interacions_table.csv")
gift = load_data(path + "gift_transactions_table.csv")
video = load_data(path + "video_email_data_table.csv")

year_list = [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024]
month_list = ['January','February','March','April','May','June','July','August','September','October','November','December']

theme_config = {
    'template': 'simple_white',
    'title_x': 0.5,
    'font': dict(size=12),
}

bar_style = {'marker_color': 'black'}

# Gift Data setup
def get_gift_df(gift, year_range, months):
    df = gift.copy()
    df['GIFT_DATE'] = pd.to_datetime(df['GIFT_DATE'])
    
    # Extract Year, Month, Day of Week
    df['Year'] = df['GIFT_DATE'].dt.year
    df['Month'] = df['GIFT_DATE'].dt.month_name()
    df['DOW'] = df['GIFT_DATE'].dt.day_name()
    
    # Filter based on inputs
    mask = (df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1]) & (df['Month'].isin(months))
    return df[mask]

# Donor Relationship

## Donor Growth Rate
def plot_donor_growth(df):
    """Equivalent to output$donorGrowthRatePlot"""
    stats = df.groupby('Year')['CONSTITUENT_ID'].nunique().reset_index()
    stats.columns = ['Year', 'Unique_Constituents']
    
    # Calculate Growth Rate
    stats['prev'] = stats['Unique_Constituents'].shift(1)
    stats['donorGrowth'] = ((stats['Unique_Constituents'] - stats['prev']) / stats['prev'] * 100).round(1).fillna(0)
    
    fig = px.bar(stats, x='Year', y='donorGrowth', 
                 title="Donor Growth by Year",
                 labels={'donorGrowth': 'Donor Growth (%)'},
                 hover_data={'Year': True, 'donorGrowth': ':.1f%'})
    fig.update_traces(marker_color='black')
    return fig

## Donor Retention and Churn
def get_donor_rates(df):
    """Equivalent to donor_churn_retention <- reactive({...})"""
    # Group by year and create sets of unique IDs
    yearly_donors = df.groupby('Year')['CONSTITUENT_ID'].apply(set).reset_index()
    yearly_donors['n_donors'] = yearly_donors['CONSTITUENT_ID'].apply(len)
    
    # Calculate retention via set intersection
    yearly_donors['prev_donors'] = yearly_donors['CONSTITUENT_ID'].shift(1)
    yearly_donors['prev_n'] = yearly_donors['n_donors'].shift(1)
    
    def calc_retained(row):
        if row['prev_donors'] is None or pd.isna(row['prev_donors']): return 0
        return len(row['CONSTITUENT_ID'].intersection(row['prev_donors']))

    yearly_donors['retained'] = yearly_donors.apply(calc_retained, axis=1)
    yearly_donors['retention_rate'] = (yearly_donors['retained'] / yearly_donors['prev_n'] * 100).round(1).fillna(0)
    yearly_donors['churn_rate'] = (100 - yearly_donors['retention_rate']).round(1)
    
    return yearly_donors[['Year', 'retention_rate', 'churn_rate']]

# Engagement
def plot_gift_crm(df, crm):
    """Equivalent to output$giftCRMPlot"""
    merged = df.merge(crm, on='CONSTITUENT_ID')
    stats = merged.groupby('CRM_INTERACTION_TYPE')['AMOUNT'].mean().round(1).reset_index()
    stats = stats.sort_values('AMOUNT', ascending=True)
    
    fig = px.bar(stats, x='AMOUNT', y='CRM_INTERACTION_TYPE', orientation='h',
                 title="CRM Interaction & Avg. Gift Amount",
                 labels={'AMOUNT': 'Avg. Gift Amount', 'CRM_INTERACTION_TYPE': 'Type'})
    fig.update_traces(marker_color='black')
    return fig


def gift_crm_plot(gift_df, crm_df):
    # Data manipulation equivalent to the R pipe
    df_plot = (
        pd.merge(gift_df, crm_df, on='CONSTITUENT_ID', how='left')
        .groupby('CRM_INTERACTION_TYPE')['AMOUNT']
        .mean()
        .round(1)
        .reset_index()
        .rename(columns={'AMOUNT': 'Total'})
        .dropna()
        .sort_values(by='Total', ascending=True) # reorder equivalent
    )

    # Creating the horizontal bar chart
    fig = px.bar(
        df_plot, 
        x='Total', 
        y='CRM_INTERACTION_TYPE', 
        orientation='h',
        title="CRM Interaction & Avg. Gift Amount",
        labels={'CRM_INTERACTION_TYPE': 'CRM Interaction Type', 'Total': 'Avg. Gift Amount'},
        text_auto=True # Optional: shows values on bars
    )

    # Styling and Tooltip
    fig.update_traces(
        marker_color='black',
        hovertemplate="CRM Interaction Type: %{y}<br>Amount: $%{x:,.1f}<extra></extra>"
    )

    fig.update_layout(
        template="simple_white", # Minimal theme
        xaxis_tickformat=",", # Commas for thousands
        title_x=0.5,
        font=dict(size=10)
    )

    return fig

def crm_outreach_plot(crm_df, year_range, month_list):
    # Ensure date is datetime object
    crm_df['CRM_INTERACTION_DATE'] = pd.to_datetime(crm_df['CRM_INTERACTION_DATE'])
    
    # Extract Year and Month (Label = True equivalent)
    crm_df['Year'] = crm_df['CRM_INTERACTION_DATE'].dt.year
    crm_df['Month'] = crm_df['CRM_INTERACTION_DATE'].dt.strftime('%b') # 'Jan', 'Feb', etc.

    # Filter data based on input ranges
    filtered_crm = crm_df[
        (crm_df['Year'] >= year_range[0]) & 
        (crm_df['Year'] <= year_range[1]) & 
        (crm_df['Month'].isin(month_list))
    ].copy()

    # Calculate Percentages
    stats = (
        filtered_crm.groupby('CRM_INTERACTION_TYPE')
        .size()
        .reset_index(name='Total')
    )
    stats['Percent'] = ((stats['Total'] / stats['Total'].sum()) * 100).round(2)
    
    # Drop NAs and sort for horizontal plotting
    stats = stats.dropna().sort_values(by='Percent', ascending=True)

    # Create Plot
    fig = px.bar(
        stats, 
        x='Percent', 
        y='CRM_INTERACTION_TYPE', 
        orientation='h',
        title="CRM Interaction Outreach Rate",
        labels={'CRM_INTERACTION_TYPE': 'CRM Interaction Type', 'Percent': 'OutReach Rate'}
    )

    # Styling and Tooltip
    fig.update_traces(
        marker_color='black',
        hovertemplate="CRM Interaction Type: %{y}<br>OutReach Rate: %{x}%<extra></extra>"
    )

    fig.update_layout(
        template="simple_white",
        xaxis_tickformat=".2f",
        title_x=0.5,
        font=dict(size=10)
    )

    return fig

# Giving Level
## Avg Gift Amount
def plot_gift_year(df):
    # Aggregation
    plot_df = df.groupby('Year')['AMOUNT'].mean().round(1).reset_index()
    plot_df = plot_df.dropna()

    fig = px.bar(
        plot_df, x='Year', y='AMOUNT',
        title="Avg. Gift Amount by Year",
        labels={'AMOUNT': 'Avg. Gift Amount', 'Year': 'Year'},
        hover_data={'Year': True, 'AMOUNT': ':$:.1f'}
    )

    
    return fig

## Gift Count by Year
def plot_gift_year_count(df):
    # Aggregation
    plot_df = df.groupby('Year').size().reset_index(name='Total')
    plot_df = plot_df.dropna()

    fig = px.bar(
        plot_df, x='Year', y='Total',
        title="Gift Count by Year",
        labels={'Total': 'Gift Count', 'Year': 'Year'}
    )

    #fig.update_traces(**bar_style)
    #fig.update_layout(**theme_config)
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(tickformat=",")
    return fig

## Gift Amouny Growth
def plot_gift_year_growth(df):
    # Aggregation and Growth Calculation
    stats = df.groupby('Year')['AMOUNT'].mean().sort_index()
    growth = stats.pct_change().fillna(0) * 100
    plot_df = growth.round(1).reset_index(name='AvgGiftGrowth')

    fig = px.bar(
        plot_df, x='Year', y='AvgGiftGrowth',
        title="Avg. Gift Amount Growth by Year",
        labels={'AvgGiftGrowth': 'Growth (%)', 'Year': 'Year'},
        custom_data=['Year', 'AvgGiftGrowth']
    )

    # Replicating the custom tooltip text
    #fig.update_traces(
    #    **bar_style,
    #    hovertemplate="Year: %{customdata[0]}<br>Donor Growth: %{customdata[1]}%"
    #)
    
    #fig.update_layout(**theme_config)
    fig.update_xaxes(dtick=1)
    return fig

## Gift by time period
def plot_gift_time_period(df, period_col):
    """Handles both Month and Day of Week (DOW)"""
    
    # Ensure correct ordering
    if period_col == 'Month':
        order = ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December']
        title = "Avg. Gift Amount by Month"
    else:
        order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        title = "Avg. Gift Amount by Day of Week"

    # Aggregation
    plot_df = df.groupby(period_col)['AMOUNT'].mean().round(1).reindex(order).reset_index()
    plot_df = plot_df.dropna()

    fig = px.bar(
        plot_df, x=period_col, y='AMOUNT',
        title=title,
        labels={'AMOUNT': 'Avg. Gift Amount'},
        hover_data={period_col: True, 'AMOUNT': ':$:.1f'}
    )

    #fig.update_traces(**bar_style)
    #fig.update_layout(**theme_config)
    fig.update_yaxes(tickformat=",")
    return fig

# Online Performance
def plot_video_views(stats):
    """Equivalent to output$videoViewPlot"""
    fig = px.bar(stats, x='Year', y='Video_views', 
                 title="Video Views by Year",
                 labels={'Video_views': 'Views'})
    fig.update_traces(marker_color='black', hovertemplate="Year: %{x}<br>Video Views: %{y}")
    fig.update_layout(template='minimal')
    return fig

def plot_video_clicks(stats):
    """Equivalent to output$clickPlot"""
    # Note: Fixed to use Video_clicks on the y-axis
    fig = px.bar(stats, x='Year', y='Video_clicks', 
                 title="Video Clicks by Year",
                 labels={'Video_clicks': 'Clicks'})
    fig.update_traces(marker_color='black', hovertemplate="Year: %{x}<br>Video Clicks: %{y}")
    fig.update_layout(template='minimal')
    return fig


def plot_bounce_unsub_rate(stats):
    """Equivalent to output$bounceUnsubPlot"""
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add Bounce Rate (Bars)
    fig.add_trace(
        go.Bar(x=stats['Year'], y=stats['Bounce_Rate'], name="Bounce Rate (%)", 
               marker_color='black', opacity=0.8),
        secondary_y=False,
    )

    # Add Unsubscribe Rate (Line)
    fig.add_trace(
        go.Scatter(x=stats['Year'], y=stats['Unsub_Rate'], name="Unsubscribe Rate (%)",
                   mode='lines+markers', line=dict(color='red', width=3)),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="Bounce Rate vs Unsubscribe Rate by Year",
        xaxis_title="Year",
        template='minimal',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_yaxes(title_text="Bounce Rate (%)", secondary_y=False)
    fig.update_yaxes(title_text="Unsubscribe Rate (%)", secondary_y=True, color="red")
    
    return fig


# Customer Segmentation
def get_rfm_segments(gift_df, segments_input):
    """Equivalent to rfm_info <- reactive({...})"""
    
    # 1. Raw RFM Calculation
    analysis_date = pd.to_datetime('today')
    rfm = gift_df.groupby('CONSTITUENT_ID').agg({
        'GIFT_DATE': lambda x: (analysis_date - x.max()).days,
        'CONSTITUENT_ID': 'count',
        'AMOUNT': 'sum'
    }).rename(columns={
        'GIFT_DATE': 'recency_days',
        'CONSTITUENT_ID': 'transaction_count',
        'AMOUNT': 'amount'
    })

    # 2. Assign Scores 1-5 (Quintiles)
    # Recency: Lower is better (5), Higher is worse (1)
    rfm['r_score'] = pd.qcut(rfm['recency_days'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    # Frequency & Monetary: Higher is better (5)
    rfm['f_score'] = pd.qcut(rfm['transaction_count'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm['m_score'] = pd.qcut(rfm['amount'], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    # 3. Define the 10 Segments (from your R code)
    # This matches your r_low, r_high, etc. vectors
    segment_map = [
        {'segment': 'Champions', 'r': (5,5), 'f': (5,5), 'm': (5,5)},
        {'segment': 'Loyal Customers', 'r': (3,5), 'f': (3,5), 'm': (2,5)},
        {'segment': 'Potential Loyalist', 'r': (2,4), 'f': (2,4), 'm': (2,4)},
        {'segment': 'Recent Customers', 'r': (3,4), 'f': (1,3), 'm': (3,5)},
        {'segment': 'Promising', 'r': (4,5), 'f': (1,3), 'm': (1,5)},
        {'segment': 'Customers Needing Attention', 'r': (1,2), 'f': (3,4), 'm': (4,5)},
        {'segment': 'About To Sleep', 'r': (1,2), 'f': (2,5), 'm': (4,5)},
        {'segment': 'At Risk', 'r': (1,3), 'f': (3,5), 'm': (3,5)},
        {'segment': 'Cant Lose Them', 'r': (2,3), 'f': (1,3), 'm': (1,4)},
        {'segment': 'Lost', 'r': (1,1), 'f': (1,5), 'm': (1,5)}
    ]

    def assign_segment(row):
        for s in segment_map:
            if (s['r'][0] <= row['r_score'] <= s['r'][1] and
                s['f'][0] <= row['f_score'] <= s['f'][1] and
                s['m'][0] <= row['m_score'] <= s['m'][1]):
                return s['segment']
        return 'Others'

    rfm['segment'] = rfm.apply(assign_segment, axis=1)
    
    # Filter by user input (equivalent to input$rfmInput)
    return rfm[rfm['segment'].isin(segments_input)]

def plot_rfm_treemap(rfm_df):
    """Equivalent to output$rfmTreemap"""
    counts = rfm_df['segment'].value_counts().reset_index()
    counts.columns = ['Segment', 'Count']
    
    fig = px.treemap(counts, path=['Segment'], values='Count',
                     title="Donor Portfolios",
                     color='Segment')
    return fig

import pandas as pd

# Data transcribed from the provided images
engagement_data = {
    "Donor Portfolio": [
        "Champions", "Loyal Customers", "Potential Loyalist", "Recent Donors",
        "Promising Donors", "Requires Assistance", "Getting Less Frequent",
        "At Risk", "Can't Lose them", "Lost"
    ],
    "Description": [
        "Donors who have visited most recently, visited most frequently and spent the most.",
        "Donors who visited recently visited often and spent a great amount",
        "A recent donor, who spent a good amount",
        "Donors visited most recently, but not often, and have not spent much",
        "Average recency, frequency, and monetary scores",
        "Donors who have spent a good amount but long ago (not visited recently)",
        "Below-average recency, frequency, and monetary values",
        "The donor has spent a great amount and visited often but long ago (not visited recently)",
        "The donor makes large donations and often but has not returned in a long time",
        "Lowest recency, frequency, and monetary scores."
    ],
    "Engagement Strategy": [
        "Reward these", "These donors", "Engage them", "For new donors",
        "Make them loyal", "Need to bring", "The donor will",
        "Listen to their", "Win them back", "Make your presence"
    ]
}

# Creating the DataFrame
engagement_df = pd.DataFrame(engagement_data)
