import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from folium.plugins import MarkerCluster

# ======================
# CONSTANTS AND SETTINGS
# ======================
LOGO_LEFT_URL = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/Ubuntu.png"
LOGO_RIGHT_URL = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/Kenya_Flag.jpg"

# ======================
# HTML/CSS FOR STATIC HEADER
# ======================
header_html = f"""
<style>
    .fixed-header {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 90px;
        background-color: white;
        z-index: 1000;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 20px;
    }}
    .header-logo {{
        height: 60px;
        object-fit: contain;
    }}
</style>

<div class="fixed-header">
    <img class="header-logo" src="{LOGO_LEFT_URL}" alt="Ubuntu Impact Labs">
    <img class="header-logo" src="{LOGO_RIGHT_URL}" alt="Kenya Flag" style="height: 50px;">
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ======================
# DATA LOADING FUNCTIONS
# ======================
@st.cache_data
def load_city_data():
    url = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/ke.csv"
    df = pd.read_csv(url)
    df['admin_name'] = df['admin_name'].fillna('Unknown')
    df['population'] = pd.to_numeric(df['population'], errors='coerce').fillna(0).astype(int)
    return df

@st.cache_data
def load_county_geojson():
    url = "https://ckan.africadatahub.org/dataset/32b18687-6e88-43b3-94ec-34846b89575f/resource/108ca393-d26d-450d-ac5d-4474ac04212a/download/kenya-counties-simplified.geojson"
    return requests.get(url).json()

# ======================
# PAGE CONTENT FUNCTIONS
# ======================
def intro_page():
    st.title("Kenya Agricultural Monitoring System")
    st.markdown("""
    ## Welcome to the Kenya Agricultural Monitoring System
    
    **Project Overview:**
    - Interactive visualization of agricultural risks
    - County-level analysis of crop production
    - Real-time monitoring of food security indicators
    
    **Key Features:**
    - Explore agricultural risks by county
    - View detailed city-level data
    - Access summary statistics and trends
    """)
    
    st.image("https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/sample_map.jpg", 
             caption="Sample Agricultural Map", use_column_width=True)

def map_page():
    st.title("Interactive Agricultural Risk Map")
    
    # Load data
    city_df = load_city_data()
    county_geojson = load_county_geojson()
    
    # Risk data setup
    risk_color_map = {"Critical": "red", "High": "orange", "Moderate": "green"}
    region_agricultural_risks = {
        # ... (same agricultural risk dictionary as before)
    }
    
    # Map creation
    m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')
    
    # Add map layers and markers (same as previous implementation)
    # ... (existing map code here)
    
    # Display map
    st_folium(m, width=1000, height=600)

def summary_page():
    st.title("Agricultural Risk Summary")
    
    # Load data
    city_df = load_city_data()
    county_counts = city_df['admin_name'].value_counts().reset_index()
    county_counts.columns = ['County', 'Number of Cities']
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cities", len(city_df))
    with col2:
        st.metric("Counties Covered", len(county_counts))
    with col3:
        st.metric("Total Population", f"{city_df['population'].sum():,}")
    
    # Show dataframes
    st.subheader("County Distribution")
    st.dataframe(county_counts, height=300)
    
    st.subheader("Sample City Data")
    st.dataframe(city_df.head(10), height=300)

# ======================
# MAIN APP STRUCTURE
# ======================
def main():
    # Add space for fixed header
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    
    # Create tabs
    page = st.sidebar.radio("Navigation", ["Introduction", "Interactive Map", "Data Summary"])
    
    if page == "Introduction":
        intro_page()
    elif page == "Interactive Map":
        map_page()
    elif page == "Data Summary":
        summary_page()

if __name__ == "__main__":
    main()
