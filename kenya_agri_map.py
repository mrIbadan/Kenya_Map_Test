import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html

# --- STATIC LOGOS AND FLAG (ALWAYS VISIBLE AND BIGGER) ---
LOGO_LEFT_URL = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/Ubuntu.png"
LOGO_RIGHT_URL = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/Kenya_Flag.jpg"

html(f"""
<style>
.fixed-logo-left {{
    position: fixed;
    top: 0.5rem;
    left: 1.2rem;
    z-index: 10000;
    width: 120px;
    height: 120px;
}}
.fixed-logo-right {{
    position: fixed;
    top: 0.5rem;
    right: 1.2rem;
    z-index: 10000;
    width: 120px;
    height: 85px;
}}
body {{
    padding-top: 130px;
}}
</style>
<img src="{LOGO_LEFT_URL}" class="fixed-logo-left" alt="Ubuntu Impact Labs Logo">
<img src="{LOGO_RIGHT_URL}" class="fixed-logo-right" alt="Kenya Flag">
""", height=0)

# Add a spacer so nothing is hidden under the logos
st.markdown("<div style='height: 130px;'></div>", unsafe_allow_html=True)

# ======================
# DATA LOADING
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
# AGRICULTURAL RISKS
# ======================
region_agricultural_risks = {
    "Nairobi": {"risks": ["Urban agriculture water scarcity", "Food supply chain disruptions", "Land pressure"], "severity": "Moderate", "type": "Urban", "details": "Urban farming faces water constraints and pollution risks"},
    "Mombasa": {"risks": ["Coastal erosion", "Saltwater intrusion", "Marine ecosystem threats"], "severity": "High", "type": "Marine", "details": "Coastal farming affected by rising sea levels and saltwater"},
    "Nakuru": {"risks": ["Soil erosion", "Maize diseases (MLND)", "Water pollution"], "severity": "High", "type": "Maize", "details": "MLND can cause losses of over 80% in maize crops"},
    "Uasin Gishu": {"risks": ["Maize disease", "Erratic rainfall", "Market access issues"], "severity": "Critical", "type": "Maize", "details": "Kenya's breadbasket facing increased disease pressure"},
    "Kisumu": {"risks": ["Lake pollution", "Flooding", "Fish stock decline"], "severity": "High", "type": "Fishery", "details": "Lake ecosystem degradation affects fishing livelihoods"},
    "Kakamega": {"risks": ["Deforestation", "Maize diseases", "Land fragmentation"], "severity": "Moderate", "type": "Maize", "details": "High population density straining agricultural land"},
    "Kiambu": {"risks": ["Coffee Berry Disease", "Coffee Leaf Rust", "Urban encroachment"], "severity": "High", "type": "Coffee", "details": "Coffee diseases can reduce yields by up to 50%"},
    "Machakos": {"risks": ["Drought frequency", "Soil erosion", "Limited irrigation"], "severity": "Critical", "type": "Weather", "details": "Semi-arid region dependent on water conservation"},
    "Kitui": {"risks": ["Severe drought cycles", "Crop failure", "Charcoal dependence"], "severity": "Critical", "type": "Weather", "details": "Drought-resistant crops needed for food security"},
    "Garissa": {"risks": ["Severe drought", "Livestock diseases", "Security issues"], "severity": "Critical", "type": "Livestock", "details": "Pastoralist communities vulnerable to climate shocks"},
    "Turkana": {"risks": ["Severe drought", "Livestock mortality", "Resource conflicts"], "severity": "Critical", "type": "Livestock", "details": "Among Kenya's most climate-vulnerable regions"},
    "DEFAULT": {"risks": ["Erratic rainfall", "Pests and diseases", "Market access challenges"], "severity": "Moderate", "type": "General", "details": "General agricultural challenges across Kenya"}
}
risk_color_map = {
    "Critical": "red",
    "High": "orange", 
    "Moderate": "green",
    "Low": "blue"
}

# ======================
# TABS
# ======================
tab1, tab2, tab3 = st.tabs(["Introduction", "Interactive Map", "Summary"])

with tab1:
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

with tab2:
    st.title("Interactive Agricultural Risk Map")
    city_df = load_city_data()
    county_geojson = load_county_geojson()
    view_mode = st.radio("Map View", ["City Markers", "County Choropleth", "Combined View"], horizontal=True)
    selected_type = st.selectbox("Filter by Risk Type", options=["All"] + sorted(set(v['type'] for v in region_agricultural_risks.values())))

    county_counts = city_df['admin_name'].value_counts().reset_index()
    county_counts.columns = ['admin_name', 'city_count']

    m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')

    if view_mode in ["County Choropleth", "Combined View"]:
        possible_keys = ["shapeName", "name", "NAME_1", "admin", "ADM1_EN"]
        geo_key = None
        for key in possible_keys:
            if "features" in county_geojson and len(county_geojson["features"]) > 0:
                if key in county_geojson["features"][0]["properties"]:
                    geo_key = key
                    break
        if geo_key:
            folium.Choropleth(
                geo_data=county_geojson,
                data=county_counts,
                columns=['admin_name', 'city_count'],
                key_on=f'feature.properties.{geo_key}',
                fill_color='YlGnBu',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name='Number of Major Cities'
            ).add_to(m)
            for feature in county_geojson['features']:
                county = feature['properties'][geo_key]
                risk_info = region_agricultural_risks.get(county, region_agricultural_risks["DEFAULT"])
                if selected_type == "All" or risk_info['type'] == selected_type:
                    tooltip_text = f"<b>{county} County</b><br>Severity: <b>{risk_info['severity']}</b><br>Type: {risk_info['type']}<br>Details: {risk_info['details']}"
                    folium.GeoJson(
                        feature,
                        tooltip=tooltip_text,
                        style_function=lambda x, severity=risk_info['severity']: {
                            'fillOpacity': 0.1,
                            'color': risk_color_map[severity],
                            'weight': 1
                        }
                    ).add_to(m)

    if view_mode in ["City Markers", "Combined View"]:
        marker_cluster = MarkerCluster().add_to(m)
        for _, city in city_df.iterrows():
            county = city['admin_name'] if pd.notnull(city['admin_name']) else "Unknown"
            risk_info = region_agricultural_risks.get(county, region_agricultural_risks["DEFAULT"])
            if selected_type == "All" or risk_info['type'] == selected_type:
                risk_list = "<br>".join([f"• {risk}" for risk in risk_info["risks"]])
                popup_html = f"""
                <div style="width: 200px; font-family: Arial;">
                    <h3 style="text-align: center; margin: 8px 0;">{city['city']}</h3>
                    <p><b>County:</b> {county}</p>
                    <p><b>Population:</b> {int(city['population']) if pd.notnull(city['population']) else 'Unknown'}</p>
                    <hr style="margin: 5px 0;">
                    <p><b>Risk:</b> <span style=\"color:{risk_color_map[risk_info['severity']]}; font-weight:bold;\">{risk_info['severity']}</span> ({risk_info['type']})</p>
                    <p><b>Key Risks:</b></p>
                    <div style="margin-left: 10px;">{risk_list}</div>
                    <p style="font-size: 11px; font-style: italic; margin-top: 5px;">{risk_info['details']}</p>
                </div>
                """
                folium.Marker(
                    location=[city['lat'], city['lng']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{city['city']} ({risk_info['severity']} risk)",
                    icon=folium.Icon(color=risk_color_map[risk_info['severity']], icon='leaf', prefix='fa')
                ).add_to(marker_cluster)

    st_folium(m, width=1000, height=650)

with tab3:
    st.title("Agricultural Risk Summary")
    city_df = load_city_data()
    county_counts = city_df['admin_name'].value_counts().reset_index()
    county_counts.columns = ['County', 'Number of Cities']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cities", len(city_df))
    with col2:
        st.metric("Counties Covered", len(county_counts))
    with col3:
        st.metric("Total Population", f"{city_df['population'].sum():,}")
    st.subheader("County Distribution")
    st.dataframe(county_counts, height=300)
    st.subheader("Sample City Data")
    st.dataframe(city_df.head(10), height=300)
