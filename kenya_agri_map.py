import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import pandas as pd
import requests
import io
from urllib.parse import urlparse

# Set page configuration
st.set_page_config(layout="wide", page_title="Kenya Analysis Map", page_icon="🌍")

# --- LOAD DATA ---
@st.cache_data
def load_city_data():
    try:
        # Load directly from GitHub raw content URL
        csv_url = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/ke.csv"
        response = requests.get(csv_url)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        else:
            st.error(f"Failed to load CSV: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- CLEAN DATA ---
def clean_data(df):
    # Drop rows with missing lat/lng
    df = df.dropna(subset=['lat', 'lng'])
    
    # Clean up admin names (fix truncated names)
    admin_name_fixes = {
        'Uasin': 'Uasin Gishu',
        'Trans': 'Trans-Nzoia',
        'Murangâ€™a': "Murang'a",
        'Elgeyo/Marakwet': 'Elgeyo-Marakwet',
        'Taita/Taveta': 'Taita-Taveta',
        'Tana': 'Tana River',
        'West': 'West Pokot',
    }
    
    df['admin_name'] = df['admin_name'].replace(admin_name_fixes)
    
    # Fill missing values
    df['population'] = df['population'].fillna(0)
    df['capital'] = df['capital'].fillna('')
    
    return df

# --- CYBER RISK DATA BY REGION ---
region_risks = {
    "Nairobi": {
        "risk_level": "Critical", 
        "top_risks": ["Ransomware (LockBit)", "Financial Fraud", "Data Breaches"],
        "incident_count": 457
    },
    "Mombasa": {
        "risk_level": "High", 
        "top_risks": ["DDoS Attacks", "Maritime System Hacks", "Tourism Sector Phishing"],
        "incident_count": 329
    },
    "Kisumu": {
        "risk_level": "Moderate", 
        "top_risks": ["Mobile Money Fraud", "SIM Swapping", "Business Email Compromise"],
        "incident_count": 187
    },
    "Uasin Gishu": {
        "risk_level": "Moderate", 
        "top_risks": ["Agritech Supply Chain", "IoT Device Compromises", "Fake Loan Apps"],
        "incident_count": 156
    },
    "Nakuru": {
        "risk_level": "High", 
        "top_risks": ["Ransomware", "Supply Chain Attacks", "Credential Theft"],
        "incident_count": 203
    },
    # Default risk profile for regions without specific data
    "DEFAULT": {
        "risk_level": "Unknown", 
        "top_risks": ["General Malware", "Phishing Campaigns", "Data Theft"],
        "incident_count": 50
    }
}

# --- SIMPLIFIED GEOJSON FOR KENYA REGIONS ---
kenya_geojson = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"REGION": "Coast"}, "geometry": {"type": "Polygon", "coordinates": [[[39.7, -4.2], [40.2, -3.8], [40.5, -1.5], [39.5, -1.0], [39.0, -2.0], [39.0, -4.4], [39.7, -4.2]]]}},
        {"type": "Feature", "properties": {"REGION": "North Eastern"}, "geometry": {"type": "Polygon", "coordinates": [[[39.5, 0.4], [41.2, 2.5], [41.9, 3.9], [41.5, 0.5], [40.5, -0.5], [39.5, 0.4]]]}},
        {"type": "Feature", "properties": {"REGION": "Eastern"}, "geometry": {"type": "Polygon", "coordinates": [[[38.0, -2.0], [38.5, -0.5], [37.5, 0.5], [37.0, 2.0], [38.0, 2.5], [39.5, 0.4], [40.5, -0.5], [39.5, -1.0], [38.5, -1.5], [38.0, -2.0]]]}},
        {"type": "Feature", "properties": {"REGION": "Central"}, "geometry": {"type": "Polygon", "coordinates": [[[36.5, -1.5], [37.0, -1.0], [37.5, 0.0], [37.0, 0.5], [36.5, -0.5], [36.5, -1.5]]]}},
        {"type": "Feature", "properties": {"REGION": "Rift Valley"}, "geometry": {"type": "Polygon", "coordinates": [[[34.5, 4.0], [35.5, 4.0], [36.0, 3.0], [36.5, 1.5], [36.5, -0.5], [36.0, -1.0], [36.5, -1.5], [36.0, -2.0], [35.0, -1.5], [34.5, 0.0], [34.5, 4.0]]]}},
        {"type": "Feature", "properties": {"REGION": "Western"}, "geometry": {"type": "Polygon", "coordinates": [[[34.0, 1.5], [34.0, -0.5], [34.5, 0.0], [35.0, -1.5], [34.5, -1.5], [34.3, -0.5], [34.0, 1.5]]]}},
        {"type": "Feature", "properties": {"REGION": "Nyanza"}, "geometry": {"type": "Polygon", "coordinates": [[[33.5, -1.0], [34.0, -0.5], [34.3, -0.5], [34.5, -1.5], [33.8, -1.5], [33.5, -1.0]]]}}
    ]
}

# --- LOAD AND CLEAN DATA ---
raw_data = load_city_data()
if raw_data is not None:
    city_data = clean_data(raw_data)
else:
    st.error("Failed to load city data. Please check your internet connection.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("Kenya Cyber Intelligence Map")
view_mode = st.sidebar.radio("View Mode:", ["Regional Risk Overview", "City-Level Details"])
risk_filter = st.sidebar.multiselect("Filter by Risk Level:", 
                                   ["Critical", "High", "Moderate", "Unknown"],
                                   default=["Critical", "High"])

st.sidebar.markdown("---")
st.sidebar.subheader("Map Legend")
st.sidebar.markdown(
    """
    **Risk Levels:**
    - 🔴 **Critical**: High volume of sophisticated attacks
    - 🟠 **High**: Significant incidents reported 
    - 🟡 **Moderate**: Limited incidents, lower impact
    - ⚪ **Unknown**: Insufficient data
    
    **Marker Types:**
    - 🛡️ Shield: Admin capital
    - 📍 Pin: Major city
    """
)

# --- MAIN APP ---
st.title("Kenya Cyber Threat Intelligence Map")
st.markdown("Interactive visualization of cyber threats across Kenya's major cities and regions.")

# --- DATA PREP FOR CHOROPLETH ---
# Map admin_name to region for consistent regional aggregation
admin_to_region = {
    "Nairobi": "Central",
    "Mombasa": "Coast",
    "Kisumu": "Nyanza",
    "Uasin Gishu": "Rift Valley",
    "Nakuru": "Rift Valley",
    "Kiambu": "Central",
    "Kilifi": "Coast",
    "Kisii": "Nyanza",
    "Kakamega": "Western",
    "Machakos": "Eastern",
    "Nyeri": "Central",
    "Garissa": "North Eastern",
    # Add mappings for other admin areas
}

# --- MAP CREATION ---
m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles="CartoDB positron")

if view_mode == "Regional Risk Overview":
    # Create region risk data
    region_risk_scores = {}
    for region in ["Central", "Coast", "North Eastern", "Eastern", "Rift Valley", "Western", "Nyanza"]:
        # Calculate risk score based on cities in the region
        cities_in_region = [city for city in city_data['admin_name'] if admin_to_region.get(city, city) == region]
        risk_score = sum([region_risks.get(city, region_risks["DEFAULT"])["incident_count"] for city in cities_in_region])
        region_risk_scores[region] = max(50, risk_score) # Ensure minimum visibility
    
    region_risk_df = pd.DataFrame([
        {"REGION": region, "risk_score": score} 
        for region, score in region_risk_scores.items()
    ])

    # Add choropleth layer
    folium.Choropleth(
        geo_data=kenya_geojson,
        name='Cyber Risk Level',
        data=region_risk_df,
        columns=['REGION', 'risk_score'],
        key_on='feature.properties.REGION',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Cyber Risk Score'
    ).add_to(m)
    
    # Add region tooltips with risk information
    for feature in kenya_geojson['features']:
        region_name = feature['properties']['REGION']
        coords = feature['geometry']['coordinates'][0]
        center_lat = sum(point[1] for point in coords) / len(coords)
        center_lon = sum(point[0] for point in coords) / len(coords)
        
        # Get sample city from region to show risks
        sample_city = next((city for city in city_data['city'] if admin_to_region.get(
            city_data[city_data['city'] == city]['admin_name'].values[0], "") == region_name), None)
        
        if sample_city:
            risk_info = region_risks.get(sample_city, region_risks["DEFAULT"])
        else:
            risk_info = region_risks["DEFAULT"]
        
        # Create tooltip
        tooltip = f"<b>{region_name} Region</b><br>Risk Level: {risk_info['risk_level']}"
        
        # Create detailed popup
        risk_list = "<br>".join([f"• {risk}" for risk in risk_info['top_risks']])
        popup_html = f"""
        <div style="width:200px">
            <h4 style="margin-top:0">{region_name} Region</h4>
            <p><b>Risk Level:</b> {risk_info['risk_level']}</p>
            <p><b>Incidents:</b> {risk_info['incident_count']}</p>
            <p><b>Top Threats:</b><br>{risk_list}</p>
        </div>
        """
        
        folium.Marker(
            location=[center_lat, center_lon],
            tooltip=tooltip,
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.DivIcon(
                icon_size=(150, 36),
                icon_anchor=(75, 18),
                html=f'<div style="font-size: 12pt; color: black; font-weight: bold;">{region_name}</div>'
            )
        ).add_to(m)
        
else:  # City-Level Details
    # Create marker clusters
    marker_cluster = MarkerCluster().add_to(m)
    
    # Risk level to color mapping
    risk_colors = {
        "Critical": "red", "High": "orange", "Moderate": "yellow", "Low": "green", "Unknown": "lightgray"
    }
    
    # Process each city
    for _, city in city_data.iterrows():
        # Skip cities without proper coordinates
        if pd.isnull(city['lat']) or pd.isnull(city['lng']):
            continue
            
        admin = city['admin_name'] if pd.notnull(city['admin_name']) else "Unknown"
        risk_info = region_risks.get(admin, region_risks["DEFAULT"])
        
        # Skip if filtered out by risk level
        if risk_info['risk_level'] not in risk_filter:
            continue
        
        # Choose icon
        icon = 'shield' if city['capital'] == 'admin' else 'map-marker'
        
        # Create popup content
        risk_list = "<br>".join([f"• {risk}" for risk in risk_info['top_risks']])
        popup_html = f"""
        <div style="width:200px">
            <h4 style="margin-top:0">{city['city']}</h4>
            <p><b>County:</b> {admin}</p>
            <p><b>Population:</b> {int(city['population']) if pd.notnull(city['population']) else 'Unknown'}</p>
            <p><b>Risk Level:</b> <span style="color:{risk_colors[risk_info['risk_level']]}; font-weight:bold;">
                {risk_info['risk_level']}</span></p>
            <p><b>Incidents:</b> {risk_info['incident_count']}</p>
            <p><b>Top Threats:</b><br>{risk_list}</p>
        </div>
        """
        
        folium.Marker(
            location=[city['lat'], city['lng']],
            tooltip=f"{city['city']} ({risk_info['risk_level']})",
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(
                color=risk_colors[risk_info['risk_level']].lower(),
                icon=icon,
                prefix='fa'
            )
        ).add_to(marker_cluster)

# --- DISPLAY MAP ---
st_folium(m, width=800, height=600)

# --- ANALYTICS ---
st.subheader("Cyber Threat Analysis")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Cities Monitored", len(city_data))
with col2:
    critical_count = sum(1 for _, city in city_data.iterrows() 
                      if region_risks.get(city['admin_name'], region_risks["DEFAULT"])["risk_level"] == "Critical")
    st.metric("Critical Risk Areas", critical_count)
with col3:
    incident_total = sum(region_risks.get(city['admin_name'], region_risks["DEFAULT"])["incident_count"] 
                      for _, city in city_data.iterrows())
    st.metric("Total Recorded Incidents", f"{incident_total:,}")

# Risk level distribution chart
st.write("### Risk Level Distribution")
risk_counts = {}
for _, city in city_data.iterrows():
    risk_level = region_risks.get(city['admin_name'], region_risks["DEFAULT"])["risk_level"]
    risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

risk_df = pd.DataFrame({
    "Risk Level": list(risk_counts.keys()),
    "City Count": list(risk_counts.values())
}).sort_values(by="Risk Level", key=lambda x: pd.Categorical(x, categories=["Critical", "High", "Moderate", "Low", "Unknown"]))

st.bar_chart(risk_df, x="Risk Level")

st.markdown("""
---
**Data Sources**: This map combines city geographic data with simulated cyber threat intelligence.  
**Note**: For a production deployment, integrate with real-time threat feeds and intelligence platforms.
""")
