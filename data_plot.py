from utils import *


## Donor Growth Rate
def plot_donor_growth(df):
    stats = df.groupby('Year')['CONSTITUENT_ID'].nunique().reset_index()
    stats.columns = ['Year', 'Unique_Constituents']
    
    # Calculate Growth Rate
    stats['prev'] = stats['Unique_Constituents'].shift(1)
    stats['donorGrowth'] = ((stats['Unique_Constituents'] - stats['prev']) / stats['prev'] * 100).round(1).fillna(0)
    
    fig = px.bar(stats, x='Year', y='donorGrowth', 
                 title="Donor Growth by Year",
                 labels={'donorGrowth': 'Donor Growth (%)'},
                 hover_data={'Year': True, 'donorGrowth': ':.1f%'},
                 color_discrete_sequence=["#4393EF"]
                 )
    
    fig.update_layout(

        title={'font': {'size': 20}, 'x': 0.5, 'xanchor': 'center'},
        #yaxis={'categoryorder':'total ascending', 'title': ''}, 
            title_font_size=20,
            template='plotly_white',
        title_x=0.5,
        xaxis_title="Year",
        yaxis_title="Donor Growth",
        margin=dict(l=200, r=10, t=40, b=10), # Increased left margin for long descriptions
        height=600
    )

    return fig

## Donor Retention and Churn
def get_donor_rates(df):
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
    
    #return yearly_donors[['Year', 'retention_rate', 'churn_rate']]
    rates_df = yearly_donors
    
    # 2. Initialize the Plotly Figure
    fig = go.Figure()

    # 3. Add Retention Rate Trace (Solid Green)
    fig.add_trace(go.Scatter(
        x=rates_df['Year'], 
        y=rates_df['retention_rate'],
        mode='lines+markers',
        name='Retention Rate (%)',
        line=dict(color='darkgreen', width=3),
        hovertemplate="Year: %{x}<br>Retention Rate: %{y}%<extra></extra>"
    ))

    # 4. Add Churn Rate Trace (Dashed Red)
    fig.add_trace(go.Scatter(
        x=rates_df['Year'], 
        y=rates_df['churn_rate'],
        mode='lines+markers',
        name='Churn Rate (%)',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate="Year: %{x}<br>Churn Rate: %{y}%<extra></extra>"
    ))

    # 5. Apply Layout and Styling to match the original dashboard
    fig.update_layout(
        title="Donor Retention vs Churn Rate by Year",
        title_font_size=20,
        title_x=0.5,
        height=600,
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(title="Percentage (%)"),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1
        )
        
    )
    
    return fig

# Engagement
def plot_gift_crm(gift, crm):
    merged = gift.merge(crm, on='CONSTITUENT_ID')
    stats = merged.groupby('CRM_INTERACTION_TYPE')['AMOUNT'].sum().round(1).reset_index()
    stats = stats.sort_values('AMOUNT', ascending=True)
    
    fig = px.bar(stats, x='AMOUNT', y='CRM_INTERACTION_TYPE', orientation='h',
                 title="CRM Interaction & Donation Amount",
                 labels={'AMOUNT': 'Donation Amount', 'CRM_INTERACTION_TYPE': 'CRM Interaction Type'})
    
    fig.update_layout(
    template='plotly_white',
    title_font_size=20,
    title_x=0.5,
    xaxis_title='Interaction Type',
    yaxis_title='Donation Amount',
    height=600)
    return fig


def crm_outreach_plot(crm, years, months):
    # 1. Create the filtered CRM dataframe (matching get_gift_df logic)
    df = crm.copy()
    df['CRM_INTERACTION_DATE'] = pd.to_datetime(df['CRM_INTERACTION_DATE'])
    
    # Extract components to match your gift function
    df['Year'] = df['CRM_INTERACTION_DATE'].dt.year
    df['Month'] = df['CRM_INTERACTION_DATE'].dt.month_name()
    
    # Apply the mask using the lists provided
    mask = (df['Year'].isin(years) & df['Month'].isin(months))
    filtered_crm = df[mask]

    # 2. Aggregate data for the "Outreach Rate"
    stats = (
        filtered_crm.groupby('CRM_INTERACTION_TYPE')
        .size()
        .reset_index(name='Total')
    )
    
    # Calculate percentage of total interactions
    if not stats.empty:
        stats['Percent'] = (stats['Total'] / stats['Total'].sum() * 100).round(2)
        stats = stats.sort_values(by='Percent', ascending=True)
    else:
        return px.bar(title="No CRM Data for Selected Period")

    # 3. Create the Styled Plot
    fig = px.bar(
        stats, 
        x='Percent', 
        y='CRM_INTERACTION_TYPE', 
        orientation='h',
        #text='Percent',
        title="<b>CRM Interaction Outreach Rate</b>",
        labels={'CRM_INTERACTION_TYPE': 'Interaction Type', 'Percent': 'Outreach Rate (%)'}
        #,color_discrete_sequence=['#4393EF']
    )


    fig.update_layout(
        template='plotly_white',
        title_font_size=20,
        #xaxis=dict(showticklabels=True, range=[0, stats['Percent'].max() * 1.2]),
        yaxis_title=None,
        title_x=0.5,
        margin=dict(l=20, r=50, t=60, b=40), 
        height = 600
    )

    return fig

# Giving Level
## Avg Gift Amount
def plot_gift_year(df):
    # Aggregation
    plot_df = df.groupby('Year')['AMOUNT'].sum().round(1).reset_index()
    plot_df = plot_df.dropna()

    fig = px.bar(
        plot_df, x='Year', y='AMOUNT',
        title="Donation Amount by Year",
        labels={'AMOUNT': 'Donation Amount', 'Year': 'Year'}
    )

    fig.update_traces(
        hovertemplate="<b>Year:</b> %{x}<br><b>Donation Amount:</b> %{y:$,.0f}<extra></extra>"
    )
    fig.update_yaxes(tickformat="$,.2s")

    fig.update_layout(
        template='plotly_white',
        title_font_size=20,
        title_x=0.5,
        height=600,
    )

    return fig

## Gift Count by Year
def plot_gift_year_count(df):
    # Aggregation
    plot_df = df.groupby('Year').size().reset_index(name='Total')
    plot_df = plot_df.dropna()

    fig = px.bar(
        plot_df, x='Year', y='Total',
        title="Donations by Year",
        labels={'Total': 'Donations', 'Year': 'Year'}
    )
    

    fig.update_layout(
    template='plotly_white',
    title_font_size=20,
    yaxis_title='Donations',
    title_x=0.5,
    height=600)


    return fig

## Gift Amouny Growth
def plot_gift_year_growth(df):
    # Aggregation and Growth Calculation
    stats = df.groupby('Year')['AMOUNT'].sum().sort_index()
    growth = stats.pct_change().fillna(0) * 100
    plot_df = growth.round(1).reset_index(name='AvgGiftGrowth')

    fig = px.bar(
        plot_df, x='Year', y='AvgGiftGrowth',
        title="Donation Amount Growth by Year",
        labels={'AvgGiftGrowth': 'Growth (%)', 'Year': 'Year'},
        custom_data=['Year', 'AvgGiftGrowth']
    )

    fig.update_xaxes(dtick=1)

    fig.update_layout(
    template='plotly_white',
    title_font_size=20,
    yaxis_title='Donations',
    title_x=0.5,
    height=600)
    return fig

## Gift by time period
def plot_gift_time_period(df, period_col):
    """Handles both Month and Day of Week (DOW)"""
    
    # Ensure correct ordering
    if period_col == 'Month':
        order = ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December']
        title = "Donation Amount by Month"
    else:
        order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        title = "Donation Amount by Day of Week"

    # Aggregation
    plot_df = df.groupby(period_col)['AMOUNT'].sum().round(1).reindex(order).reset_index()
    plot_df = plot_df.dropna()

    fig = px.bar(
        plot_df, x=period_col, y='AMOUNT',
        title=title,
        labels={'AMOUNT': 'Donation Amount'},
        hover_data={period_col: True, 'AMOUNT': ':$:.1f'}
    )

    fig.update_yaxes(tickformat=",")
    fig.update_layout(
    template='plotly_white',     
    title_font_size=20,
    yaxis_title='Donations',
    title_x=0.5,
    height=600)
    
    return fig

# Online Performance
def get_video_stats(video_df, years, months):
    # Filter and setup (video_df reactive)
    df = video_df.copy()
    df['SENT_DATE'] = pd.to_datetime(df['SENT_DATE'])
    df['Year'] = df['SENT_DATE'].dt.year
    df['Month'] = df['SENT_DATE'].dt.month_name()
    
    mask = (df['Year'].isin(years) & df['Month'].isin(months))
    filtered_df = df[mask]
    
    # Aggregation (video_df1 reactive)
    stats = filtered_df.groupby('Year').agg(
        Total_Sent=('SENT_DATE', 'count'),
        Total_Bounced=('BOUNCED', 'sum'),
        Total_Unsub=('UNSUBSCRIBED', 'sum'),
        Video_views=('VIDEO_VIEWS', 'sum'),
        Video_clicks=('CLICKS', 'sum')
    ).reset_index()
    
    stats['Bounce_Rate'] = (stats['Total_Bounced'] / stats['Total_Sent'] * 100).round(2)
    stats['Unsub_Rate'] = (stats['Total_Unsub'] / stats['Total_Sent'] * 100).round(2)
    
    return stats


def plot_video_views(stats):
    fig = px.bar(stats, x='Year', y='Video_views', 
                 title="Video Views by Year",
                 labels={'Video_views': 'Views'})
    fig.update_traces(marker_color='#3B82F6', hovertemplate="Year: %{x}<br>Video Views: %{y}")
    fig.update_layout(
    template='plotly_white',     
    title_font_size=20,
    yaxis_title='Donations',
    title_x=0.5,
    height=600)
    return fig

def plot_video_clicks(stats):
    """Equivalent to output$clickPlot"""
    # Note: Fixed to use Video_clicks on the y-axis
    fig = px.bar(stats, x='Year', y='Video_clicks', 
                 title="Video Clicks by Year",
                 labels={'Video_clicks': 'Clicks'})
    fig.update_traces(marker_color='#3B82F6', hovertemplate="Year: %{x}<br>Video Clicks: %{y}")
    fig.update_layout(
    template='plotly_white',     
    title_font_size=20,
    yaxis_title='Donations',
    title_x=0.5,
    height=600)
    return fig


def plot_bounce_unsub_rate(stats):
    """Equivalent to output$bounceUnsubPlot"""
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add Bounce Rate (Bars)
    fig.add_trace(
        go.Bar(x=stats['Year'], y=stats['Bounce_Rate'], name="Bounce Rate (%)", 
               marker_color='#3B82F6', opacity=0.8),
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
        template='plotly_white',#template='minimal',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,),
        title_font_size=20,
        title_x=0.5,
        height=600
    )

    fig.update_yaxes(title_text="Bounce Rate (%)", secondary_y=False)
    fig.update_yaxes(title_text="Unsubscribe Rate (%)", secondary_y=True, color="red")
    
    return fig

def plot_rfm_treemap(rfm_df):
    """Equivalent to output$rfmTreemap"""
    counts = rfm_df['segment'].value_counts().reset_index()
    counts.columns = ['Segment', 'Count']
    
    fig = px.treemap(counts, path=['Segment'], values='Count',
                     title="Donor Portfolios",
                     color='Segment')
    

    fig.update_layout(
        template='plotly_white',
        title_font_size=20,
        title_x=0.5,
        height=600
    )
    return fig

def create_forecast_chart(forecast_df):
    fig = px.bar(
        forecast_df, 
        x='Month', 
        y='Forecasted Donations',
        title="Projected Donations Forecast",
        labels={'Forecasted Donations': 'Amount ($)', 'Month': 'Month'},
        text_auto='.2s' # Adds formatted values on top of bars
    )

    fig.update_layout(
        template='plotly_white',
        title_font_size=20,
        title_x=0.5,
        height=600
    )
    
    # Clean up x-axis to show Month Year (e.g., Jan 2026)
    fig.update_xaxes(dtick="M1", tickformat="%b %Y", tickangle=-45)
    
    return fig

def create_forecast_table(forecast_df):
    # Format the date for display
    display_df = forecast_df.copy()
    display_df['Month'] = display_df['Month'].dt.strftime('%B %Y')
    display_df['Forecasted Donations'] = display_df['Forecasted Donations'].apply(lambda x: f"${x:,.2f}")

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["<b>Month</b>", "<b>Forecasted Amount</b>"],
            fill_color='dodgerblue',
            align='center',
            font=dict(color='white', size=18)
        ),
        cells=dict(
            values=[display_df['Month'], display_df['Forecasted Donations']],
            fill_color='whitesmoke',
            align='center',
            font=dict(color='black', size=14),
            height=50
        )
    )])
    
    fig.update_layout(margin=dict(l=0, r=0, b=10, t=10))
    return fig