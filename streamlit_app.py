import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# -------------------
# Streamlit Page Setup
# -------------------
st.set_page_config(page_title="SBIR Awards Dashboard", layout="wide")
st.title("SBIR Awards Dashboard")
st.markdown("Analyze SBIR grant awards across agencies and geographies.")

# -------------------
# Function to Fetch Data from SBIR.gov API
# -------------------
@st.cache_data
def fetch_sbir_awards(company_name):
    url = f"https://api.www.sbir.gov/public/api/awards?firm={company_name}&start=0&rows=1000"
    response = requests.get(url)
    try:
        data = response.json()
        # If the response is a list, just return it
        if isinstance(data, list):
            return data
        # If it's a dictionary and has 'results', return 'results'
        elif isinstance(data, dict) and 'results' in data:
            return data['results']
        else:
            return []  # Handle unexpected structure
    except Exception as e:
        st.error(f"Error parsing JSON: {e}")
        return []


# -------------------
# Sidebar Filters
# -------------------
company_name = st.sidebar.text_input("Enter Company Name:", "ExampleCompany")
agency_filter = st.sidebar.multiselect("Select Agency:", 
                                       options=["DOD", "HHS", "NASA", "NSF", "DOE", 
                                                "USDA", "EPA", "DOC", "ED", "DOT", "DHS"])
phase_filter = st.sidebar.multiselect("Select Phase:", options=["Phase I", "Phase II"])

# -------------------
# Fetch and Prepare Data
# -------------------
data = fetch_sbir_awards(company_name)
if not data:
    st.warning("No data found. Please check the company name or try a different query.")
else:
    df = pd.DataFrame(data)
    df['award_amount'] = pd.to_numeric(df['award_amount'], errors='coerce')
    
    # Optional Filters
    if agency_filter:
        df = df[df['agency'].isin(agency_filter)]
    if phase_filter:
        df = df[df['phase'].isin(phase_filter)]
    
    # -------------------
    # KPIs and Summary
    # -------------------
    total_awarded = df['award_amount'].sum()
    total_projects = len(df)

    st.metric("Total Awarded ($)", f"${total_awarded:,.2f}")
    st.metric("Total Funded Projects", total_projects)

    # -------------------
    # Map Visualization
    # -------------------
    st.subheader("Award Distribution by State")
    if 'state' in df.columns:
        state_summary = df.groupby('state')['award_amount'].sum().reset_index()
        fig_map = px.choropleth(state_summary,
                                locations='state',
                                locationmode='USA-states',
                                color='award_amount',
                                scope='usa',
                                color_continuous_scale='Blues',
                                labels={'award_amount': 'Total Awarded ($)'},
                                title='Total Awarded by State')
        st.plotly_chart(fig_map, use_container_width=True)

    # -------------------
    # Awards by Agency and Phase
    # -------------------
    st.subheader("Award Breakdown by Agency")
    agency_summary = df.groupby('agency')['award_amount'].sum().reset_index()
    fig_agency = px.bar(agency_summary, x='agency', y='award_amount', 
                        labels={'award_amount': 'Total Awarded ($)', 'agency': 'Agency'},
                        title='Total Awarded by Agency')
    st.plotly_chart(fig_agency, use_container_width=True)

    st.subheader("Award Breakdown by Phase")
    phase_summary = df.groupby('phase')['award_amount'].sum().reset_index()
    fig_phase = px.pie(phase_summary, names='phase', values='award_amount', 
                       title='Award Distribution by Phase')
    st.plotly_chart(fig_phase, use_container_width=True)

    # -------------------
    # Data Table
    # -------------------
    st.subheader("Award Details")
    st.dataframe(df[['agency', 'phase', 'program', 'award_amount', 
                     'award_year', 'city', 'state']])

