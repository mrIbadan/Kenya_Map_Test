import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from folium.plugins import MarkerCluster
import base64

# ---- STATIC LOGOS AND FLAG ----
def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

UBUNTU_LOGO_PATH = "image.jpg"  # Your logo file must be in the same directory

try:
    ubuntu_logo_base64 = get_image_base64(UBUNTU_LOGO_PATH)
except Exception as e:
    st.warning("Could not load Ubuntu Impact Labs logo. Please check image.jpg is present.")
    ubuntu_logo_base64 = ""

custom_header = f"""
<style>
    .logo-container {{
        position: fixed;
        top: 0.5rem;
        left: 1rem;
        z-index: 1000;
        width: 80px;
        height: 80px;
    }}
    .flag-container {{
        position: fixed;
        top: 0.5rem;
        right: 1rem;
        z-index: 1000;
        width: 80px;
        height: 50px;
    }}
    .logo-img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        background: #fff;
    }}
    .flag-img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        border-radius: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        background: #fff;
    }}
</style>
<div class="logo-container">
    <img class="logo-img" src="data:image/jpeg;base64,{ubuntu_logo_base64}" alt="Ubuntu Impact Labs Logo">
</div>
<div class="flag-container">
    <img class="flag-img" src="https://flagcdn.com/w320/ke.png" alt="Kenya Flag">
</div>
"""
st.components.v1.html(custom_header, height=0)

# ---- DATA LOADING ----
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
    r = requests.get(url)
    return r.json()

# ---- AGRICULTURAL RISKS ----
region_agricultural_risks = {
    "Nairobi": {
        "risks": ["Urban agriculture water scarcity", "Food supply chain disruptions", "Land pressure"],
        "severity": "Moderate",
        "details": "Urban farming faces water constraints and pollution risks"
    },
    "Mombasa": {
        "risks": ["Coastal erosion", "Saltwater intrusion", "Marine ecosystem threats"],
        "severity": "High",
        "details": "Coastal farming affected by rising sea levels and saltwater"
    },
    "Nakuru": {
        "risks": ["Soil erosion", "Maize diseases (MLND)", "Water pollution"],
        "severity": "High",
        "details": "MLND can cause losses of over 80% in maize crops"
    },
    "Uasin Gishu": {
        "risks": ["Maize disease", "Erratic rainfall", "Market access issues"],
        "severity": "Critical",
        "details": "Kenya's breadbasket facing increased disease pressure"
    },
    "Kisumu": {
        "risks": ["Lake pollution", "Flooding", "Fish stock decline"],
        "severity": "High",
        "details": "Lake ecosystem degradation affects fishing livelihoods"
    },
    "Kakamega": {
        "risks": ["Deforestation", "Maize diseases", "Land fragmentation"],
        "severity": "Moderate",
        "details": "High population density straining agricultural land"
    },
    "Kiambu": {
        "risks": ["Coffee Berry Disease", "Coffee Leaf Rust", "Urban encroachment"],
        "severity": "High",
        "details": "Coffee diseases can reduce yields by up to 50%"
    },
    "Machakos": {
        "risks": ["Drought frequency", "Soil erosion", "Limited irrigation"],
        "severity": "Critical",
        "details": "Semi-arid region dependent on water conservation"
    },
    "Kitui": {
        "risks": ["Severe drought cycles", "Crop failure", "Charcoal dependence"],
        "severity": "Critical",
        "details": "Drought-resistant crops needed for food security"
    },
    "Garissa": {
        "risks": ["Severe drought", "Livestock diseases", "Security issues"],
        "severity": "Critical",
        "details": "Pastoralist communities vulnerable to climate shocks"
    },
    "Turkana": {
        "risks": ["Severe drought", "Livestock mortality", "Resource conflicts"],
        "severity": "Critical",
        "details": "Among Kenya's most climate-vulnerable regions"
    },
    "DEFAULT": {
        "risks": ["Erratic rainfall", "Pests and diseases", "Market access challenges"],
        "severity": "Moderate",
        "details": "General agricultural challenges across Kenya"
    }
}
risk_color_map = {
    "Critical": "red",
    "High": "orange", 
    "Moderate": "green",
    "Low": "blue"
}

# ---- MAIN APP ----
st.title("Kenya Cities, Counties, and Key Agricultural Risks Map")
st.write("Interactive visualization of major cities and agricultural risks across Kenya counties.")

city_df = load_city_data()
county_geojson = load_county_geojson()

view_mode = st.sidebar.radio("Map View", ["City Markers", "County Choropleth", "Combined View"])

# --- AGGREGATE CITY DATA BY COUNTY ---
county_counts = city_df['admin_name'].value_counts().reset_index()
county_counts.columns = ['admin_name', 'city_count']

# --- FOLIUM MAP ---
m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')

# --- CHOROPLETH ---
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
            tooltip_text = f"{county} County: {risk_info['severity']} Risk<br>" + "<br>".join(risk_info["risks"])
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
        risk_list = "<br>".join([f"• {risk}" for risk in risk_info["risks"]])
        popup_html = f"""
        <div style="width: 200px; font-family: Arial;">
            <h3 style="text-align: center; margin: 8px 0;">{city['city']}</h3>
            <p><b>County:</b> {county}</p>
            <p><b>Population:</b> {int(city['population']) if pd.notnull(city['population']) else 'Unknown'}</p>
            <hr style="margin: 5px 0;">
            <p><b>Agricultural Risk Level:</b> <span style="color:{risk_color_map[risk_info['severity']]}; font-weight:bold;">{risk_info['severity']}</span></p>
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

st.write("### County Coverage")
st.dataframe(county_counts.rename(columns={"admin_name": "County", "city_count": "Number of Cities"}))
st.write("### Example of City Data")
st.dataframe(city_df.head(20))
