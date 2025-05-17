import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# Sample data for Kenya agriculture projects
data = pd.DataFrame({
    'Location': ['Nairobi', 'Eldoret', 'Kisumu', 'Mombasa', 'Garissa'],
    'Latitude': [-1.286389, 0.5143, -0.0917, -4.0435, 0.4562],
    'Longitude': [36.817223, 35.2698, 34.7680, 39.6682, 39.6583],
    'Project': ['Soil Survey', 'Irrigation Pilot', 'Crop Yield Monitoring', 'Coastal Farming', 'Drought Response'],
    'Status': ['Active', 'Active', 'Planned', 'Active', 'Emergency']
})

# Create the folium map centered on Kenya
m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')

# Add markers
for _, row in data.iterrows():
    color = 'green' if row['Status'] == 'Active' else 'red' if row['Status'] == 'Emergency' else 'blue'
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(f"<b>{row['Project']}</b><br>{row['Location']} ({row['Status']})", max_width=300),
        tooltip=row['Location'],
        icon=folium.Icon(color=color, icon='leaf', prefix='fa')
    ).add_to(m)

# Use streamlit_folium to render the map in Streamlit
st.title('Kenya Agriculture Projects Map')
st_folium(m, width=700, height=500)
