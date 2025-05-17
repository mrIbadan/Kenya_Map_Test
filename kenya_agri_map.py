import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# --- DATA ---
data = pd.DataFrame({
    'Location': ['Nairobi', 'Eldoret', 'Kisumu', 'Mombasa', 'Garissa'],
    'Latitude': [-1.286389, 0.5143, -0.0917, -4.0435, 0.4562],
    'Longitude': [36.817223, 35.2698, 34.7680, 39.6682, 39.6583],
    'Project': ['Soil Survey', 'Irrigation Pilot', 'Crop Yield Monitoring', 'Coastal Farming', 'Drought Response'],
    'Status': ['Active', 'Active', 'Planned', 'Active', 'Emergency']
})

# --- SIDEBAR LEGEND & SUMMARY ---
st.sidebar.title("Map Legend & Project Summary")

# Legend
st.sidebar.markdown("### Marker Colors")
st.sidebar.markdown(
    """
    <span style='color:green'>●</span> **Active**  
    <span style='color:blue'>●</span> **Planned**  
    <span style='color:red'>●</span> **Emergency**
    """,
    unsafe_allow_html=True,
)

# Status summary
status_counts = data['Status'].value_counts()
st.sidebar.markdown("### Project Status Counts")
for status, count in status_counts.items():
    st.sidebar.write(f"- **{status}**: {count}")

# Brief summary
summary = ""
if 'Emergency' in status_counts:
    summary += "🚨 **Emergency projects are ongoing, with urgent response needed in Garissa.**\n\n"
if 'Planned' in status_counts:
    summary += "📝 **Some projects are still in the planning phase (e.g., Crop Yield Monitoring in Kisumu).**\n\n"
if status_counts.get('Active', 0) > 0:
    summary += "✅ **Most projects are currently active, indicating good operational coverage across Kenya.**"

st.sidebar.markdown("### Brief Risk Summary")
st.sidebar.info(summary)

# --- MAIN PAGE ---
st.title("Kenya Agriculture Projects Map")
st.write(
    "This interactive map shows the locations and statuses of key agriculture projects in Kenya. "
    "Marker color indicates project status. Click a marker for project details."
)

# --- FOLIUM MAP ---
m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')

# Color mapping
status_color = {'Active': 'green', 'Planned': 'blue', 'Emergency': 'red'}

# Add markers
for _, row in data.iterrows():
    color = status_color.get(row['Status'], 'gray')
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(f"<b>{row['Project']}</b><br>{row['Location']} ({row['Status']})", max_width=300),
        tooltip=row['Location'],
        icon=folium.Icon(color=color, icon='leaf', prefix='fa')
    ).add_to(m)

# Display Folium map in Streamlit
st_folium(m, width=700, height=500)
