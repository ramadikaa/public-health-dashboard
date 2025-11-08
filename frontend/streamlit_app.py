"""
COVID-19 Public Health Dashboard
Streamlit Frontend - Consumes REST API

Modul 6: Consumer Health Informatics
Modul 7: Data Analytics & BI
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import numpy as np 

# ===== CONFIGURATION =====
# Use 127.0.0.1 instead of localhost for better Windows compatibility
API_BASE_URL = "http://127.0.0.1:5000/api"
API_ROOT = "http://127.0.0.1:5000"

# ===== PAGE CONFIGURATION =====
st.set_page_config(
    page_title="COVID-19 Public Health Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    .main-header {
        font-size: 40px;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        padding: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .connection-status {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .status-success {
        background-color: #28a745;
        color: white;
    }
    .status-error {
        background-color: #dc3545;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ===== HELPER FUNCTIONS =====

def test_api_connection():
    """Test if Flask API server is running and accessible"""
    try:
        response = requests.get(f"{API_ROOT}/ping", timeout=3)
        if response.status_code == 200 and response.json().get('status') == 'pong':
            return True, "Connected"
    except requests.exceptions.ConnectionError:
        return False, "Connection Refused - Flask not running"
    except requests.exceptions.Timeout:
        return False, "Timeout - Server not responding"
    except Exception as e:
        return False, f"Error: {str(e)}"
    return False, "Unknown error"

def test_database_connection():
    """Test if database is connected and has data"""
    try:
        response = requests.get(f"{API_ROOT}/test-db", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return True, data
        return False, response.json()
    except Exception as e:
        return False, {"error": str(e)}

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_api(endpoint, params=None):
    """
    Fetch data from API with comprehensive error handling
    
    Args:
        endpoint: API endpoint path (without /api/ prefix)
        params: Query parameters
    
    Returns:
        JSON response or None on error
    """
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        st.error(f"""
        🔴 **Cannot Connect to Flask API Server**
        
        **Endpoint**: `{url}`
        
        **Troubleshooting Steps**:
        1. ✅ Open new terminal in `backend` folder
        2. ✅ Run: `python app.py`
        3. ✅ Wait for: "Running on http://127.0.0.1:5000"
        4. ✅ Test in browser: http://127.0.0.1:5000/health
        5. ✅ Refresh this Streamlit page
        
        **Quick Fix**: Check sidebar → API Connection Status
        """)
        return None
        
    except requests.exceptions.Timeout:
        st.warning(f"⏱️ API request timeout for endpoint: `{endpoint}`")
        st.info("Server might be processing large data. Try again in a moment.")
        return None
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error(f"❌ Endpoint not found: `{endpoint}`")
        elif e.response.status_code == 500:
            st.error(f"❌ Server error. Check Flask terminal for details.")
            with st.expander("View Error Details"):
                st.json(e.response.json())
        else:
            st.error(f"❌ HTTP {e.response.status_code}: {e.response.reason}")
        return None
        
    except requests.exceptions.JSONDecodeError:
        st.error("❌ Invalid JSON response from API")
        return None
        
    except Exception as e:
        st.error(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")
        return None

# ===== HEADER =====
st.markdown('<div class="main-header">🦠 COVID-19 Integrated Public Health Dashboard</div>', unsafe_allow_html=True)
st.markdown("**Real-time Outbreak Monitoring with AI-Powered Analytics | ITENAS Health Informatics**")
st.markdown("*Implementasi Modul 1-7: Health Informatics, Interoperability, Database, CDSS, Public Health, Consumer Health, Analytics*")
st.markdown("---")

# ===== SIDEBAR =====
st.sidebar.title("📊 Navigation")

# Connection Status Check
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 System Status")

with st.sidebar:
    # Test API connection
    api_connected, api_message = test_api_connection()
    
    if api_connected:
        st.success(f"✅ Flask API: {api_message}")
        
        # Test database connection
        db_connected, db_info = test_database_connection()
        
        if db_connected:
            st.success("✅ MySQL Database: Connected")
            
            # Show data statistics
            with st.expander("📊 Database Info"):
                tables = db_info.get('tables', {})
                st.write(f"**Database**: {db_info.get('database_name', 'N/A')}")
                st.write(f"**Latest Data**: {db_info.get('latest_data_date', 'N/A')}")
                
                if 'daily_cases' in tables:
                    st.write(f"**Daily Cases**: {tables['daily_cases'].get('row_count', 0):,} rows")
                if 'dashboard_metrics' in tables:
                    st.write(f"**Dashboard Metrics**: {tables['dashboard_metrics'].get('row_count', 0):,} rows")
        else:
            st.error("❌ MySQL Database: Failed")
            with st.expander("🔍 Database Error Details"):
                st.json(db_info)
    else:
        st.error(f"❌ Flask API: {api_message}")
        
        st.markdown("""
        **Start Flask Server:**
        ```
        cd backend
        python app.py
        ```
        
        **Verify Flask:**
        - Open: http://127.0.0.1:5000
        - Should show: API service info
        """)

st.sidebar.markdown("---")

# Page Navigation
page = st.sidebar.selectbox(
    "Select Dashboard Page",
    ["🌍 Real-time Monitoring", "📈 Country Analysis", "🗺️ WHO Regions", "🤖 Predictive Analytics", "🔬 FHIR API Demo", "ℹ️ About"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Available API Endpoints:**
- `/api/dashboard/metrics`
- `/api/dashboard/timeseries`
- `/api/dashboard/countries/top`
- `/api/cases/country/{name}`
- `/api/cases/who-regions`
- `/api/predictions/mortality`
- `/api/predictions/model-performance`
- `/api/fhir/observation`
- `/api/fhir/capability`
""")

# ==============================
# PAGE 1: REAL-TIME MONITORING
# ==============================
if page == "🌍 Real-time Monitoring":
    st.header("🌍 Real-time COVID-19 Global Outbreak Monitoring")
    st.markdown("**Modul 5**: Public Health Informatics | **Modul 7**: Data Analytics & Business Intelligence")
    
    # Check if API is connected before fetching data
    if not api_connected:
        st.warning("⚠️ Cannot load dashboard. Flask API is not running. Check sidebar for instructions.")
        st.stop()
    
    # Fetch dashboard metrics from API
    with st.spinner("📊 Loading dashboard metrics..."):
        metrics_data = fetch_api("dashboard/metrics")
    
    if metrics_data and metrics_data.get('status') == 'success':
        data = metrics_data['data']
        metrics = data['metrics']
        
        # Display date
        st.subheader(f"📅 Latest Update: {data['date']}")
        
        # KPI Metrics Row 1
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            new_cases = metrics['confirmed'].get('new_cases', 0)
            st.metric(
                label="🔴 Total Confirmed",
                value=f"{metrics['confirmed']['total']:,}",
                delta=f"+{new_cases:,}" if new_cases else None,
                delta_color="inverse"
            )
        
        with col2:
            new_deaths = metrics['deaths'].get('new_deaths', 0)
            st.metric(
                label="💀 Total Deaths",
                value=f"{metrics['deaths']['total']:,}",
                delta=f"+{new_deaths:,}" if new_deaths else None,
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                label="💚 Total Recovered",
                value=f"{metrics['recovered']['total']:,}"
            )
        
        with col4:
            st.metric(
                label="⚠️ Active Cases",
                value=f"{metrics['active']['total']:,}"
            )
        
        # KPI Metrics Row 2
        col5, col6 = st.columns(2)
        
        with col5:
            st.metric(
                label="📊 Global Mortality Rate",
                value=f"{metrics['rates']['mortality_rate']:.2f}%"
            )
        
        with col6:
            st.metric(
                label="📈 Global Recovery Rate",
                value=f"{metrics['rates']['recovery_rate']:.2f}%"
            )
        
        st.markdown("---")
        
        # Time Series Chart
        st.subheader("📈 Global COVID-19 Trend Analysis")
        
        with st.spinner("📊 Loading time series data..."):
            timeseries_data = fetch_api("dashboard/timeseries")
        
        if timeseries_data and timeseries_data.get('status') == 'success':
            df = pd.DataFrame(timeseries_data['data'])
            df['date'] = pd.to_datetime(df['date'])
            
            # Create 4-panel chart
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Confirmed Cases", "Deaths", "Recovered Cases", "Active Cases"),
                vertical_spacing=0.12,
                horizontal_spacing=0.1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['confirmed'],
                    name="Confirmed", 
                    line=dict(color='orange', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255,165,0,0.1)'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['deaths'],
                    name="Deaths", 
                    line=dict(color='red', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255,0,0,0.1)'
                ),
                row=1, col=2
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['recovered'],
                    name="Recovered", 
                    line=dict(color='green', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0,255,0,0.1)'
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['date'], 
                    y=df['active'],
                    name="Active", 
                    line=dict(color='blue', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0,0,255,0.1)'
                ),
                row=2, col=2
            )
            
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Cases")
            
            fig.update_layout(
                showlegend=False,
                height=700,
                template="plotly_dark",
                title_text="<b>COVID-19 Global Time Series Analysis</b>",
                title_font_size=18
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            with st.expander("📊 View Summary Statistics"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Days", len(df))
                    st.metric("Start Date", df['date'].min().strftime('%Y-%m-%d'))
                
                with col2:
                    st.metric("Peak Confirmed", f"{df['confirmed'].max():,}")
                    st.metric("Peak Date", df.loc[df['confirmed'].idxmax(), 'date'].strftime('%Y-%m-%d'))
                
                with col3:
                    avg_daily = df['confirmed'].diff().mean()
                    st.metric("Avg Daily New Cases", f"{avg_daily:,.0f}" if not pd.isna(avg_daily) else "N/A")
        
        st.markdown("---")
        
        # Top Countries
        st.subheader("🌍 Top 20 Countries by Confirmed Cases")
        
        # Country limit selector
        limit_options = [10, 20, 30, 50]
        limit = st.select_slider("Number of countries to display", options=limit_options, value=20)
        
        with st.spinner(f"📊 Loading top {limit} countries..."):
            countries_data = fetch_api("dashboard/countries/top", params={"limit": limit})
        
        if countries_data and countries_data.get('status') == 'success':
            df_countries = pd.DataFrame(countries_data['data'])
            df_countries_sorted = df_countries.sort_values('confirmed', ascending=True)
            
            fig2 = px.bar(
                df_countries_sorted,
                x='confirmed',
                y='country',
                orientation='h',
                text='confirmed',
                color='mortality_rate',
                color_continuous_scale='Reds',
                height=max(600, limit * 30),
                labels={'mortality_rate': 'Mortality Rate (%)'},
                hover_data={
                    'confirmed': ':,',
                    'deaths': ':,',
                    'recovered': ':,',
                    'mortality_rate': ':.2f'
                }
            )
            
            fig2.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig2.update_layout(
                template="plotly_dark",
                title=f"<b>Top {limit} Countries by Confirmed Cases (Color: Mortality Rate)</b>",
                xaxis_title="Confirmed Cases",
                yaxis_title="Country"
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Data table
            with st.expander("📋 View Detailed Data Table"):
                df_display = df_countries[['country', 'confirmed', 'deaths', 'recovered', 'active', 'mortality_rate']].copy()
                df_display.columns = ['Country', 'Confirmed', 'Deaths', 'Recovered', 'Active', 'Mortality Rate (%)']
                st.dataframe(
                    df_display.sort_values('Confirmed', ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.error("❌ Failed to load dashboard metrics. Check API connection.")

# ==============================
# PAGE 2: COUNTRY ANALYSIS
# ==============================
elif page == "📈 Country Analysis":
    st.header("📈 Country-Specific COVID-19 Analysis")
    st.markdown("**Modul 5**: Public Health Informatics - Epidemiological Analysis by Country")
    
    if not api_connected:
        st.warning("⚠️ Flask API is not running. Check sidebar for instructions.")
        st.stop()
    
    # Country input with suggestions
    st.markdown("### Select or Enter Country Name")
    
    # Popular countries dropdown
    popular_countries = [
        "Indonesia", "United States", "India", "Brazil", "Russia", 
        "United Kingdom", "France", "Germany", "Italy", "Spain",
        "China", "Japan", "South Korea", "Australia", "Canada"
    ]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        country = st.text_input("Country Name", value="Indonesia", help="Enter country name (case-sensitive)")
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        quick_select = st.selectbox("Quick Select", [""] + popular_countries, index=0)
        if quick_select:
            country = quick_select
    
    if st.button("🔍 Analyze Country", type="primary"):
        with st.spinner(f"📊 Loading data for {country}..."):
            country_data = fetch_api(f"cases/country/{country}")
        
        if country_data and country_data.get('status') == 'success':
            df = pd.DataFrame(country_data['data'])
            df['date'] = pd.to_datetime(df['date'])
            
            # ===== FIX: Convert to numeric =====
            numeric_cols = ['confirmed', 'deaths', 'recovered', 'active']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Latest metrics
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            
            st.success(f"✅ Data loaded for **{country}** ({len(df)} days)")
            
            # KPI Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_confirmed = int(latest['confirmed'] - previous['confirmed'])
                st.metric(
                    "Confirmed", 
                    f"{int(latest['confirmed']):,}",
                    delta=f"+{delta_confirmed:,}" if delta_confirmed > 0 else None
                )
            
            with col2:
                delta_deaths = int(latest['deaths'] - previous['deaths'])
                st.metric(
                    "Deaths", 
                    f"{int(latest['deaths']):,}",
                    delta=f"+{delta_deaths:,}" if delta_deaths > 0 else None,
                    delta_color="inverse"
                )
            
            with col3:
                st.metric("Recovered", f"{int(latest['recovered']):,}")
            
            with col4:
                st.metric("Active", f"{int(latest['active']):,}")
            
            # Calculated metrics
            mortality_rate = (latest['deaths'] / latest['confirmed'] * 100) if latest['confirmed'] > 0 else 0
            recovery_rate = (latest['recovered'] / latest['confirmed'] * 100) if latest['confirmed'] > 0 else 0
            
            col5, col6, col7 = st.columns(3)
            
            with col5:
                st.metric("Mortality Rate", f"{mortality_rate:.2f}%")
            
            with col6:
                st.metric("Recovery Rate", f"{recovery_rate:.2f}%")
            
            with col7:
                st.metric("Latest Date", latest['date'].strftime('%Y-%m-%d'))
            
            st.markdown("---")
            
            # Time series chart
            st.subheader(f"📈 COVID-19 Trend in {country}")
            
            fig = px.line(
                df,
                x='date',
                y=['confirmed', 'deaths', 'recovered', 'active'],
                title=f'<b>COVID-19 Time Series: {country}</b>',
                labels={'value': 'Number of Cases', 'variable': 'Category', 'date': 'Date'},
                color_discrete_map={
                    'confirmed': 'orange',
                    'deaths': 'red',
                    'recovered': 'green',
                    'active': 'blue'
                }
            )
            
            fig.update_layout(
                template="plotly_dark", 
                height=500,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily new cases chart
            st.subheader("📊 Daily New Cases")
            
            df['daily_confirmed'] = df['confirmed'].diff().fillna(0)
            df['daily_deaths'] = df['deaths'].diff().fillna(0)
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                x=df['date'],
                y=df['daily_confirmed'],
                name='Daily Confirmed',
                marker_color='orange'
            ))
            
            fig2.add_trace(go.Bar(
                x=df['date'],
                y=df['daily_deaths'],
                name='Daily Deaths',
                marker_color='red'
            ))
            
            fig2.update_layout(
                template="plotly_dark",
                height=400,
                title=f"<b>Daily New Cases: {country}</b>",
                xaxis_title="Date",
                yaxis_title="Daily New Cases",
                barmode='overlay',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Download data option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"covid19_{country.replace(' ', '_')}.csv",
                mime="text/csv"
            )
            
        else:
            st.error(f"❌ No data found for country: **{country}**")
            st.info("💡 **Tips**: \n- Check spelling (case-sensitive)\n- Try using full country name\n- Use Quick Select dropdown for popular countries")

# ==============================
# PAGE 3: WHO REGIONS
# ==============================
elif page == "🗺️ WHO Regions":
    st.header("🗺️ COVID-19 Cases by WHO Region")
    st.markdown("**Modul 5**: Public Health Informatics - Regional Epidemiological Surveillance")
    
    if not api_connected:
        st.warning("⚠️ Flask API is not running. Check sidebar for instructions.")
        st.stop()
    
    with st.spinner("📊 Loading WHO region data..."):
        regions_data = fetch_api("cases/who-regions")
    
    if regions_data and regions_data.get('status') == 'success':
        df_regions = pd.DataFrame(regions_data['data'])
        
        # ===== FIX: Convert to numeric =====
        numeric_cols = ['confirmed', 'deaths', 'recovered', 'active']
        for col in numeric_cols:
            df_regions[col] = pd.to_numeric(df_regions[col], errors='coerce').fillna(0)
        
        # Summary metrics
        total_confirmed = int(df_regions['confirmed'].sum())
        total_deaths = int(df_regions['deaths'].sum())
        total_recovered = int(df_regions['recovered'].sum())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Confirmed (All Regions)", f"{total_confirmed:,}")
        
        with col2:
            st.metric("Total Deaths (All Regions)", f"{total_deaths:,}")
        
        with col3:
            st.metric("Total Recovered (All Regions)", f"{total_recovered:,}")
        
        st.markdown("---")
        
        # Grouped bar chart
        st.subheader("📊 Cases by WHO Region")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_regions['region'],
            y=df_regions['confirmed'],
            name='Confirmed',
            marker_color='orange',
            text=df_regions['confirmed'],
            texttemplate='%{text:,.0f}',
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            x=df_regions['region'],
            y=df_regions['deaths'],
            name='Deaths',
            marker_color='red',
            text=df_regions['deaths'],
            texttemplate='%{text:,.0f}',
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            x=df_regions['region'],
            y=df_regions['recovered'],
            name='Recovered',
            marker_color='green',
            text=df_regions['recovered'],
            texttemplate='%{text:,.0f}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='<b>COVID-19 Cases by WHO Region</b>',
            xaxis_title='WHO Region',
            yaxis_title='Number of Cases',
            barmode='group',
            template="plotly_dark",
            height=600,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Pie chart for distribution
        st.subheader("🥧 Regional Distribution")
        
        fig_pie = px.pie(
            df_regions,
            values='confirmed',
            names='region',
            title='<b>Confirmed Cases Distribution by WHO Region</b>',
            color_discrete_sequence=px.colors.sequential.RdBu,
            hole=0.4
        )
        
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(template="plotly_dark", height=500)
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Data table
        st.subheader("📋 Detailed Regional Statistics")
        
        # Add calculated columns
        df_display = df_regions.copy()
        df_display['mortality_rate'] = (df_display['deaths'] / df_display['confirmed'] * 100).round(2)
        df_display['recovery_rate'] = (df_display['recovered'] / df_display['confirmed'] * 100).round(2)
        
        # Replace inf/nan
        df_display['mortality_rate'] = df_display['mortality_rate'].replace([np.inf, -np.inf], 0).fillna(0)
        df_display['recovery_rate'] = df_display['recovery_rate'].replace([np.inf, -np.inf], 0).fillna(0)
        
        # Reorder columns
        df_display = df_display[['region', 'confirmed', 'deaths', 'recovered', 'active', 'mortality_rate', 'recovery_rate']]
        df_display.columns = ['WHO Region', 'Confirmed', 'Deaths', 'Recovered', 'Active', 'Mortality Rate (%)', 'Recovery Rate (%)']
        
        st.dataframe(
            df_display.sort_values('Confirmed', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("❌ Failed to load WHO region data")

# ==============================
# PAGE 4: FHIR API DEMO
# ==============================
elif page == "🔬 FHIR API Demo":
    st.header("🔬 FHIR-Compatible API Demonstration")
    st.markdown("**Modul 2**: Data Standards & Interoperability - HL7 FHIR R4 Implementation")
    
    st.info("""
    📘 **About FHIR (Fast Healthcare Interoperability Resources)**
    
    This page demonstrates a FHIR R4-compatible API endpoint for COVID-19 surveillance data. 
    FHIR is the global standard for healthcare data exchange developed by HL7.
    
    **Use Cases:**
    - Health information exchange between systems
    - Integration with Electronic Health Records (EHR)
    - Public health surveillance reporting
    - Research data sharing
    """)
    
    if not api_connected:
        st.warning("⚠️ Flask API is not running. Check sidebar for instructions.")
        st.stop()
    
    # Input form
    st.subheader("🔍 Query FHIR Observation Resource")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fhir_country = st.text_input(
            "Country Name", 
            value="Indonesia",
            help="Enter country name to retrieve COVID-19 observation data"
        )
    
    with col2:
        fhir_date = st.date_input(
            "Observation Date", 
            value=datetime(2020, 3, 15),
            help="Select date for COVID-19 observation data"
        )
    
    if st.button("🔍 Fetch FHIR Observation", type="primary"):
        with st.spinner("📡 Fetching FHIR resource from API..."):
            fhir_data = fetch_api("fhir/observation", params={
                "country": fhir_country,
                "date": fhir_date.strftime('%Y-%m-%d')
            })
        
        if fhir_data:
            if fhir_data.get('resourceType') == 'Observation':
                st.success("✅ FHIR Observation Resource Retrieved Successfully")
                
                # Display key information
                st.subheader("📋 FHIR Observation Details")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Resource Type", fhir_data['resourceType'])
                    st.metric("Status", fhir_data['status'].upper())
                
                with col2:
                    st.metric("Subject (Location)", fhir_data['subject']['display'])
                    st.metric("Effective Date", fhir_data['effectiveDateTime'])
                
                with col3:
                    # ===== FIX: Convert to int before formatting =====
                    confirmed_value = int(fhir_data['valueQuantity']['value'])
                    st.metric("Confirmed Cases", f"{confirmed_value:,}")
                    
                    # Extract deaths from components
                    deaths = next(
                        (comp['valueQuantity']['value'] for comp in fhir_data.get('component', []) 
                         if 'Deaths' in comp['code'].get('text', '')),
                        0
                    )
                    
                    # Convert deaths to int
                    if isinstance(deaths, (int, float)):
                        deaths_int = int(deaths)
                        st.metric("Deaths", f"{deaths_int:,}")
                    else:
                        st.metric("Deaths", "N/A")

                
                st.markdown("---")
                
                # FHIR Components
                if 'component' in fhir_data:
                    st.subheader("🧩 FHIR Observation Components")
                    
                    for comp in fhir_data['component']:
                        comp_name = comp['code'].get('text', 'Unknown')
                        comp_value = comp['valueQuantity']['value']
                        
                        # ===== FIX: Convert to int before formatting =====
                        if isinstance(comp_value, (int, float)):
                            comp_value_int = int(comp_value)
                            st.write(f"**{comp_name}**: {comp_value_int:,}")
                        else:
                            st.write(f"**{comp_name}**: {comp_value}")

                
                st.markdown("---")
                
                # Display full JSON
                st.subheader("📄 Full FHIR JSON Response")
                st.json(fhir_data)
                
                # Postman instructions
                st.markdown("---")
                st.subheader("📮 Test with Postman")
                
                postman_url = f"http://127.0.0.1:5000/api/fhir/observation?country={fhir_country}&date={fhir_date.strftime('%Y-%m-%d')}"
                
                st.code(f"""
GET {postman_url}

Headers:
Accept: application/fhir+json
Content-Type: application/fhir+json
                """, language="http")
                
                st.info("""
                💡 **How to test in Postman:**
                1. Open Postman application
                2. Create new GET request
                3. Paste the URL above
                4. Add headers: `Accept: application/fhir+json`
                5. Click Send
                6. View FHIR-compliant JSON response
                """)
                
            elif fhir_data.get('resourceType') == 'OperationOutcome':
                st.error("❌ FHIR OperationOutcome - Error occurred")
                
                if 'issue' in fhir_data:
                    for issue in fhir_data['issue']:
                        st.error(f"**{issue.get('severity', 'error').upper()}**: {issue.get('diagnostics', 'Unknown error')}")
                
                with st.expander("View Full Response"):
                    st.json(fhir_data)
            else:
                st.error("❌ Unexpected response format")
                st.json(fhir_data)
    
    # FHIR Capability Statement
    st.markdown("---")
    st.subheader("📋 FHIR Capability Statement")
    
    if st.button("📄 View FHIR CapabilityStatement"):
        with st.spinner("📡 Fetching FHIR CapabilityStatement..."):
            capability_data = fetch_api("fhir/capability")
        
        if capability_data:
            st.success("✅ FHIR CapabilityStatement Retrieved")
            
            st.write(f"**FHIR Version**: {capability_data.get('fhirVersion', 'N/A')}")
            st.write(f"**Publisher**: {capability_data.get('publisher', 'N/A')}")
            st.write(f"**Status**: {capability_data.get('status', 'N/A')}")
            
            with st.expander("View Full CapabilityStatement"):
                st.json(capability_data)

# ==============================
# PAGE 4.5: PREDICTIVE ANALYTICS (ML MODEL)
# ==============================
elif page == "🤖 Predictive Analytics":
    st.header("🤖 AI-Powered COVID-19 Mortality Risk Prediction")
    st.markdown("**Modul 4**: Clinical Decision Support Systems | **Modul 7**: Predictive Analytics & Machine Learning")
    
    st.info("""
    📊 **Machine Learning Model for COVID-19 Mortality Risk Assessment**
    
    This page demonstrates predictive analytics using a trained Random Forest Classifier
    to assess mortality risk based on epidemiological features and outbreak patterns.
    
    **Clinical Decision Support:**
    - Risk stratification (Low/Medium/High)
    - Evidence-based recommendations
    - Real-time prediction API
    """)
    
    if not api_connected:
        st.warning("⚠️ Flask API is not running. Cannot load ML model.")
        st.stop()
    
    # ===== MODEL PERFORMANCE SECTION =====
    st.subheader("📈 Model Performance Metrics")
    
    with st.spinner("📊 Loading model evaluation metrics..."):
        perf_data = fetch_api("predictions/model-performance")
    
    if perf_data and perf_data.get('status') == 'success':
        metrics = perf_data['metrics']
        
        # Display metrics in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Accuracy", f"{metrics['accuracy']:.1%}", 
                     help="Overall model accuracy on test set")
        
        with col2:
            st.metric("Precision", f"{metrics['precision']:.1%}",
                     help="Proportion of positive predictions that were correct")
        
        with col3:
            st.metric("Recall", f"{metrics['recall']:.1%}",
                     help="Proportion of actual positives correctly identified")
        
        with col4:
            st.metric("F1-Score", f"{metrics['f1_score']:.1%}",
                     help="Harmonic mean of precision and recall")
        
        with col5:
            st.metric("AUC-ROC", f"{metrics['auc_roc']:.3f}",
                     help="Area under ROC curve (0.5=random, 1.0=perfect)")
        
        st.markdown("---")
        
        # ===== ROC CURVE =====
        st.subheader("📊 ROC Curve Analysis")
        
        st.markdown("""
        **ROC (Receiver Operating Characteristic) Curve** shows the trade-off between 
        True Positive Rate and False Positive Rate at various classification thresholds.
        A higher AUC indicates better model performance.
        """)
        
        roc = perf_data['roc_curve']
        
        fig_roc = go.Figure()
        
        # ROC Curve
        fig_roc.add_trace(go.Scatter(
            x=roc['fpr'],
            y=roc['tpr'],
            mode='lines',
            name=f'ROC Curve (AUC = {roc["auc"]:.3f})',
            line=dict(color='cyan', width=3),
            fill='tozeroy',
            fillcolor='rgba(0,255,255,0.1)',
            hovertemplate='<b>FPR</b>: %{x:.3f}<br><b>TPR</b>: %{y:.3f}<extra></extra>'
        ))
        
        # Random classifier baseline
        fig_roc.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            name='Random Classifier (AUC = 0.500)',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Add annotations
        fig_roc.add_annotation(
            x=0.5, y=0.5,
            text=f"AUC = {roc['auc']:.3f}",
            showarrow=False,
            font=dict(size=16, color='cyan'),
            bgcolor='rgba(0,0,0,0.5)'
        )
        
        fig_roc.update_layout(
            xaxis_title='False Positive Rate (1 - Specificity)',
            yaxis_title='True Positive Rate (Sensitivity)',
            template="plotly_dark",
            height=500,
            title="<b>ROC Curve: COVID-19 Mortality Risk Prediction Model</b>",
            hovermode='closest',
            showlegend=True,
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="right",
                x=0.99
            )
        )
        
        fig_roc.update_xaxes(range=[0, 1], constrain='domain')
        fig_roc.update_yaxes(range=[0, 1], scaleanchor="x", scaleratio=1)
        
        st.plotly_chart(fig_roc, use_container_width=True)
        
        # Model interpretation
        with st.expander("📖 How to Interpret ROC Curve"):
            st.markdown("""
            **ROC Curve Interpretation:**
            
            - **Perfect Model (AUC = 1.0)**: Curve follows the left and top edges
            - **Good Model (AUC > 0.8)**: Curve is well above the diagonal
            - **Random Model (AUC = 0.5)**: Curve follows the diagonal line
            - **Poor Model (AUC < 0.5)**: Curve is below the diagonal
            
            **Our Model Performance:**
            - AUC = {auc:.3f} indicates **{performance}** discriminative ability
            - The model can distinguish between high-risk and low-risk cases effectively
            """.format(
                auc=roc['auc'],
                performance="excellent" if roc['auc'] > 0.9 else "good" if roc['auc'] > 0.8 else "fair"
            ))
        
        st.markdown("---")
        
        # ===== CONFUSION MATRIX =====
        st.subheader("🎯 Confusion Matrix")
        
        st.markdown("""
        **Confusion Matrix** shows the model's predictions vs actual outcomes,
        helping identify types of errors (false positives vs false negatives).
        """)
        
        cm = perf_data['confusion_matrix']
        
        # Create confusion matrix visualization
        cm_matrix = [
            [cm['true_negative'], cm['false_positive']],
            [cm['false_negative'], cm['true_positive']]
        ]
        
        # Calculate percentages
        total = sum([cm['true_negative'], cm['false_positive'], cm['false_negative'], cm['true_positive']])
        cm_pct = [[val/total*100 for val in row] for row in cm_matrix]
        
        # Create heatmap
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm_matrix,
            x=['Predicted: Low Risk', 'Predicted: High Risk'],
            y=['Actual: Low Risk', 'Actual: High Risk'],
            text=[[f'{cm_matrix[i][j]}<br>({cm_pct[i][j]:.1f}%)' for j in range(2)] for i in range(2)],
            texttemplate='%{text}',
            textfont={"size": 14},
            colorscale='Blues',
            showscale=True,
            hovertemplate='%{x}<br>%{y}<br>Count: %{z}<extra></extra>'
        ))
        
        fig_cm.update_layout(
            title='<b>Confusion Matrix: Model Predictions vs Actual Outcomes</b>',
            template="plotly_dark",
            height=500,
            xaxis=dict(side='bottom'),
            yaxis=dict(autorange='reversed')
        )
        
        st.plotly_chart(fig_cm, use_container_width=True)
        
        # Confusion matrix metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("True Negatives", f"{cm['true_negative']:,}",
                     help="Correctly predicted low risk cases")
        
        with col2:
            st.metric("False Positives", f"{cm['false_positive']:,}",
                     help="Incorrectly predicted as high risk")
        
        with col3:
            st.metric("False Negatives", f"{cm['false_negative']:,}",
                     help="Incorrectly predicted as low risk")
        
        with col4:
            st.metric("True Positives", f"{cm['true_positive']:,}",
                     help="Correctly predicted high risk cases")
        
        st.markdown("---")
        
        # ===== FEATURE IMPORTANCE =====
        st.subheader("🔍 Feature Importance Analysis")
        
        st.markdown("""
        **Feature Importance** shows which epidemiological factors contribute most
        to the model's mortality risk predictions.
        """)
        
        feature_imp = perf_data.get('feature_importance', [])[:10]  # Top 10
        
        if feature_imp:
            df_fi = pd.DataFrame(feature_imp)
            
            fig_fi = px.bar(
                df_fi,
                x='importance',
                y='feature',
                orientation='h',
                title='<b>Top 10 Most Important Features</b>',
                text='importance',
                color='importance',
                color_continuous_scale='Viridis',
                height=500
            )
            
            fig_fi.update_traces(texttemplate='%{text:.4f}', textposition='outside')
            fig_fi.update_layout(
                template="plotly_dark",
                xaxis_title="Importance Score",
                yaxis_title="Feature",
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig_fi, use_container_width=True)
            
            with st.expander("📋 Feature Descriptions"):
                st.markdown("""
                **Feature Definitions:**
                
                - **mortality_rate**: Deaths per 100 confirmed cases
                - **confirmed/deaths/recovered/active**: Absolute case counts
                - **recovery_rate**: Recovered per 100 confirmed cases
                - **confirmed_lag1/deaths_lag1**: Previous day values
                - **daily_*_change**: Day-over-day changes
                - ***_rolling_7d**: 7-day moving averages
                - **growth_rate**: Percentage growth rate
                - **who_region_encoded**: WHO region classification
                """)
        
        st.markdown("---")
        
        # ===== TRAINING INFO =====
        with st.expander("🎓 Model Training Information"):
            training_info = perf_data.get('training_info', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Training Samples", f"{training_info.get('training_samples', 0):,}")
            
            with col2:
                st.metric("Test Samples", f"{training_info.get('test_samples', 0):,}")
            
            with col3:
                st.metric("Mortality Threshold", f"{training_info.get('mortality_threshold', 0):.2f}%")
            
            st.markdown("""
            **Model Details:**
            - **Algorithm**: Random Forest Classifier
            - **Features**: 15 epidemiological indicators
            - **Training Method**: Stratified 80/20 train-test split
            - **Class Balancing**: Balanced class weights
            - **Cross-validation**: None (single holdout)
            """)
    
    else:
        st.error("❌ Failed to load model metrics. Ensure model has been trained.")
        st.info("Run: `python train_model.py` in backend directory")
    
    st.markdown("---")
    
    # ===== INTERACTIVE PREDICTION TOOL =====
    st.subheader("🔮 Interactive Mortality Risk Prediction Tool")
    
    st.markdown("""
    Enter epidemiological data below to predict COVID-19 mortality risk using our trained ML model.
    This tool simulates a **Clinical Decision Support System (CDSS)**.
    """)
    
    # Create input form
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Current Outbreak Metrics")
            confirmed = st.number_input(
                "Total Confirmed Cases", 
                min_value=0, 
                value=1000, 
                step=100,
                help="Total cumulative confirmed COVID-19 cases"
            )
            
            deaths = st.number_input(
                "Total Deaths", 
                min_value=0, 
                value=50, 
                step=10,
                help="Total cumulative deaths from COVID-19"
            )
            
            recovered = st.number_input(
                "Total Recovered", 
                min_value=0, 
                value=700, 
                step=50,
                help="Total patients recovered from COVID-19"
            )
            
            active = confirmed - deaths - recovered
            st.info(f"**Calculated Active Cases**: {active:,}")
        
        with col2:
            st.markdown("##### Historical Context (Optional)")
            
            confirmed_lag1 = st.number_input(
                "Previous Day Confirmed", 
                min_value=0, 
                value=int(confirmed * 0.95), 
                step=100,
                help="Confirmed cases from previous day"
            )
            
            deaths_lag1 = st.number_input(
                "Previous Day Deaths", 
                min_value=0, 
                value=int(deaths * 0.95), 
                step=10,
                help="Deaths from previous day"
            )
            
            who_region = st.selectbox(
                "WHO Region",
                ["Americas", "Europe", "Western Pacific", 
                 "Eastern Mediterranean", "South-East Asia", "Africa", "Unknown"],
                index=0,
                help="WHO regional classification"
            )
            
            region_mapping = {
                'Americas': 0, 'Europe': 1, 'Western Pacific': 2, 
                'Eastern Mediterranean': 3, 'South-East Asia': 4, 'Africa': 5, 'Unknown': 6
            }
            who_region_encoded = region_mapping[who_region]
        
        # Submit button
        submitted = st.form_submit_button("🔮 Predict Mortality Risk", type="primary", use_container_width=True)
    
    if submitted:
        # Prepare payload
        payload = {
            "confirmed": confirmed,
            "deaths": deaths,
            "recovered": recovered,
            "active": active,
            "confirmed_lag1": confirmed_lag1,
            "deaths_lag1": deaths_lag1,
            "who_region_encoded": who_region_encoded
        }
        
        with st.spinner("🤖 Running ML model prediction..."):
            try:
                # POST request to prediction API
                response = requests.post(
                    f"{API_ROOT}/api/predictions/mortality",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    pred_data = response.json()
                    
                    if pred_data.get('status') == 'success':
                        prediction = pred_data['prediction']
                        
                        st.success("✅ Prediction Complete!")
                        
                        st.markdown("---")
                        
                        # Display risk level with color coding
                        risk_level = prediction['risk_level']
                        risk_color = prediction['risk_color']
                        risk_score = prediction['risk_score']
                        
                        # Color mapping
                        color_emoji_map = {
                            "red": "🔴",
                            "orange": "🟡",
                            "green": "🟢"
                        }
                        
                        # Large risk display
                        st.markdown(f"""
                        <div style='background-color: {risk_color}; padding: 30px; border-radius: 15px; text-align: center;'>
                            <h1 style='color: white; margin: 0;'>{color_emoji_map.get(risk_color, '⚪')} {risk_level} RISK</h1>
                            <h2 style='color: white; margin: 10px 0 0 0;'>Risk Score: {risk_score:.1%}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("")
                        
                        # Metrics display
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Risk Score", f"{risk_score:.1%}")
                        
                        with col2:
                            st.metric("Model Confidence", f"{prediction['confidence']:.1%}")
                        
                        with col3:
                            mortality_rate = prediction.get('mortality_rate', 0)
                            st.metric("Current Mortality Rate", f"{mortality_rate:.2f}%")
                        
                        st.markdown("---")
                        
                        # Clinical recommendation
                        st.subheader("💡 Clinical Decision Support Recommendation")
                        
                        recommendation = prediction.get('recommendation', 'No recommendation available')
                        
                        if risk_level == "HIGH":
                            st.error(recommendation)
                        elif risk_level == "MEDIUM":
                            st.warning(recommendation)
                        else:
                            st.success(recommendation)
                        
                        st.markdown("---")
                        
                        # Input features used
                        with st.expander("🔍 View Input Features"):
                            input_data = pred_data.get('input_data', {})
                            model_info = pred_data.get('model_info', {})
                            
                            st.json({
                                "Input Data": input_data,
                                "Model Information": model_info
                            })
                        
                        # Download prediction report
                        report = f"""
COVID-19 MORTALITY RISK PREDICTION REPORT
==========================================

Prediction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INPUT DATA:
-----------
Confirmed Cases: {confirmed:,}
Deaths: {deaths:,}
Recovered: {recovered:,}
Active: {active:,}
WHO Region: {who_region}

PREDICTION RESULTS:
-------------------
Risk Level: {risk_level}
Risk Score: {risk_score:.3f} ({risk_score*100:.1f}%)
Model Confidence: {prediction['confidence']:.3f} ({prediction['confidence']*100:.1f}%)
Current Mortality Rate: {mortality_rate:.2f}%

RECOMMENDATION:
---------------
{recommendation}

MODEL INFORMATION:
------------------
Algorithm: Random Forest Classifier
Training Accuracy: {model_info.get('training_accuracy', 0):.3f}
Features Used: {model_info.get('features_count', 0)}

Generated by: COVID-19 Health Informatics Dashboard
ITENAS Health Informatics - IFB-499 Informatika Terapan
                        """
                        
                        st.download_button(
                            label="📥 Download Prediction Report",
                            data=report,
                            file_name=f"covid19_risk_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    else:
                        st.error(f"❌ Prediction failed: {pred_data.get('message', 'Unknown error')}")
                
                else:
                    st.error(f"❌ API Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {str(e)}")
                st.info("Ensure Flask API is running on http://127.0.0.1:5000")


# ==============================
# PAGE 5: ABOUT
# ==============================
elif page == "ℹ️ About":
    st.header("ℹ️ About This Dashboard")
    
    st.markdown("""
    ## 🎯 Project Overview
    
    **Integrated COVID-19 Public Health Dashboard with Predictive Analytics**
    
    This dashboard is developed as part of **IFB-499 Informatika Terapan (Health Informatics Focus)** 
    midterm project for Academic Year 2025/2026 at Institut Teknologi Nasional (ITENAS) Bandung.
    
    ### 📚 Module Integration (Modul 1-7)
    
    #### **Module 1: Health Informatics Foundation**
    - DIKW pyramid implementation (Data → Information → Knowledge → Wisdom)
    - Ethical considerations in health data usage
    - De-identified data compliance
    
    #### **Module 2: Data Standards & Interoperability**
    - FHIR R4 API implementation for COVID-19 data exchange
    - HL7 standards compliance
    - RESTful API architecture
    
    #### **Module 3: Database Management & EHR**
    - MySQL relational database design
    - ETL pipeline for data integration
    - Normalized schema with indexing
    
    #### **Module 4: Clinical Decision Support Systems (CDSS)**
    - AI-powered mortality risk prediction
    - Risk stratification algorithms
    - Clinical alerts and recommendations
    
    #### **Module 5: Public Health Informatics**
    - Real-time outbreak monitoring
    - Syndromic surveillance dashboard
    - Geographic and temporal trend analysis
    - WHO regional analysis
    
    #### **Module 6: Consumer Health Informatics**
    - User-friendly interface for health officials
    - Interactive visualizations
    - Accessible health information presentation
    
    #### **Module 7: Data Analytics & Business Intelligence**
    - Descriptive analytics (KPIs, trends, distributions)
    - Predictive analytics (ML models)
    - BI dashboard with real-time metrics
    - Data-driven decision support
    
    ---
    
    ### 🛠️ Technology Stack
    
    **Backend:**
    - Flask (Python web framework)
    - MySQL (Relational database)
    - Flask-CORS (Cross-origin resource sharing)
    
    **Frontend:**
    - Streamlit (Python dashboard framework)
    - Plotly (Interactive visualizations)
    - Pandas (Data manipulation)
    
    **API & Interoperability:**
    - RESTful API architecture
    - FHIR R4 compliance
    - Postman (API testing)
    
    **Data Processing:**
    - Python (pandas, numpy)
    - ETL pipelines
    - Data validation & quality checks
    
    ---
    
    ### 📊 Data Sources
    
    - **Primary Dataset**: COVID-19 de-identified public datasets (Kaggle)
    - **Data Coverage**: Global (by country/region)
    - **Data Types**: Time series (Confirmed, Deaths, Recovered cases)
    - **Compliance**: HIPAA de-identification standards
    
    ---
    
    ### 👥 Development Team
    
    **Course**: IFB-499 Informatika Terapan (Health Informatics)  
    **Institution**: Institut Teknologi Nasional (ITENAS) Bandung  
    **Academic Year**: 2025/2026  
    **Instructor**: Dr. Edi Nuryatno, PhD, MSc, MACS CT, BSc
    
    ---
    
    ### 📞 Support & Documentation
    
    - **API Documentation**: http://127.0.0.1:5000/
    - **Health Check**: http://127.0.0.1:5000/health
    - **Database Test**: http://127.0.0.1:5000/test-db
    - **FHIR Capability**: http://127.0.0.1:5000/api/fhir/capability
    
    ---
    
    ### 📝 License & Attribution
    
    This project is developed for educational purposes as part of the Health Informatics curriculum.
    Data sources are properly attributed and de-identified according to privacy regulations.
    
    ---
    
    ### 🙏 Acknowledgments
    
    Special thanks to:
    - Dr. Edi Nuryatno for comprehensive Health Informatics modules
    - ITENAS Informatics Department for academic support
    - Open-source community for tools and libraries
    - Public health organizations for COVID-19 data
    """)
    
    st.markdown("---")
    st.success("✅ Dashboard successfully implements all Modul 1-7 requirements")