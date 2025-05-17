import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json

# --- EXPANDED DATA ---
data = pd.DataFrame({
    'Location': ['Nairobi', 'Eldoret', 'Kisumu', 'Mombasa', 'Garissa', 'Nakuru', 
                'Thika', 'Kitale', 'Malindi', 'Naivasha', 'Machakos', 'Embu', 
                'Meru', 'Kakamega', 'Busia', 'Lodwar', 'Isiolo', 'Lamu', 'Voi', 
                'Nyeri', 'Narok', 'Kitui', 'Bungoma', 'Homa Bay', 'Kilifi'],
    'Latitude': [-1.2864, 0.5143, -0.0917, -4.0435, 0.4562, -0.3031, -1.0333, 
                1.0167, -3.2167, -0.7167, -1.5167, -0.5333, 0.05, 0.2833, 0.45,
                3.1194, 0.3556, -2.2694, -3.3964, -0.4207, -1.0833, -1.3667, 
                0.5667, -0.5167, -3.6333],
    'Longitude': [36.8172, 35.2698, 34.7680, 39.6682, 39.6583, 36.0800, 37.0694,
                35.0000, 40.1167, 36.4333, 37.2667, 37.45, 37.65, 34.75, 34.1,
                35.5972, 37.5822, 40.9022, 38.5631, 36.9475, 35.8667, 38.0167,
                34.5667, 34.4667, 39.8500],
    'Project': ['Soil Survey', 'Irrigation Pilot', 'Crop Monitoring', 'Coastal Farming',
               'Drought Response', 'Water Mgmt', 'Agroforestry', 'Pest Control', 
               'Marine Farming', 'Horticulture', 'Livestock Health', 'Soil Fertility',
               'Crop Diversification', 'Market Access', 'Food Security', 'Arid Farming',
               'Nomad Support', 'Marine Conservation', 'Wildlife Protection', 
               'Tea Cultivation', 'Maize Production', 'Drought Resistant Crops',
               'Sugar Production', 'Fishing Support', 'Coral Protection'],
    'Status': ['Active', 'Active', 'Planned', 'Active', 'Emergency', 'Active',
              'Planned', 'Active', 'Planned', 'Active', 'Active', 'Planned',
              'Active', 'Active', 'Emergency', 'Active', 'Planned', 'Active',
              'Emergency', 'Active', 'Active', 'Planned', 'Active', 'Active', 'Emergency'],
    'Region': ['Central', 'Rift Valley', 'Western', 'Coast', 'North Eastern',
              'Rift Valley', 'Central', 'Rift Valley', 'Coast', 'Rift Valley',
              'Eastern', 'Eastern', 'Eastern', 'Western', 'Western', 'Rift Valley',
              'Eastern', 'Coast', 'Coast', 'Central', 'Rift Valley', 'Eastern',
              'Western', 'Western', 'Coast']
})

# --- GEOJSON FOR KENYA REGIONS ---
kenya_geojson = {
  "type": "FeatureCollection",
  "features": [
    {"type":"Feature","properties":{"REGION":"Coast"},"geometry":{"type":"Polygon","coordinates":[[[39.7,-4.2],[39.2,-3.8],[39.8,-3.0],[39.7,-4.2]]]}},
    {"type":"Feature","properties":{"REGION":"North Eastern"},"geometry":{"type":"Polygon","coordinates":[[[39.5,0.4],[40.5,1.5],[41.0,0.0],[39.5,0.4]]]}},
    # Add other regions' coordinates...
  ]
}

# --- SIDEBAR ---
st.sidebar.title("Kenya Agriculture Dashboard")
view_mode = st.sidebar.radio("View Mode:", ["Regional Overview", "Project Details"])
show_emergency = st.sidebar.checkbox("Highlight Emergency Projects", True)

# --- MAIN APP ---
st.title("Kenya Agricultural Initiatives Monitoring")

if view_mode == "Regional Overview":
    # Choropleth map
    region_counts = data.groupby('Region').size().reset_index(name='counts')
    
    m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')
    
    folium.Choropleth(
        geo_data=kenya_geojson,
        name='choropleth',
        data=region_counts,
        columns=['Region', 'counts'],
        key_on='feature.properties.REGION',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Number of Projects'
    ).add_to(m)
    
    # Add region labels
    for feature in kenya_geojson['features']:
        folium.Marker(
            location=[feature['geometry']['coordinates'][0][0][1]-0.5, 
                     feature['geometry']['coordinates'][0][0][0]-0.5],
            icon=folium.DivIcon(
                html=f"<div style='font-weight:bold;color:black'>{feature['properties']['REGION']}</div>"
            )
        ).add_to(m)
    
    st_folium(m, width=700, height=500)
    
else:
    # Detailed project map
    m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')
    
    marker_cluster = folium.plugins.MarkerCluster().add_to(m)
    
    for _, row in data.iterrows():
        color = 'red' if (row['Status'] == 'Emergency' and show_emergency) else \
               'green' if row['Status'] == 'Active' else 'blue'
        
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(
                f"<b>{row['Project']}</b><br>"
                f"Location: {row['Location']}<br>"
                f"Status: {row['Status']}<br>"
                f"Region: {row['Region']}",
                max_width=300
            ),
            icon=folium.Icon(color=color, icon='leaf', prefix='fa')
        ).add_to(marker_cluster)
    
    st_folium(m, width=700, height=500)

# --- PROJECT SUMMARY ---
st.subheader("Regional Project Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Projects", len(data))
with col2:
    st.metric("Emergency Projects", len(data[data['Status'] == 'Emergency']))
with col3:
    st.metric("Active Projects", len(data[data['Status'] == 'Active']))

st.write("### Regional Distribution")
st.bar_chart(data['Region'].value_counts())
