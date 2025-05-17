import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# --- LOAD CITY DATA ---
@st.cache_data
def load_city_data():
    url = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/ke.csv"
    df = pd.read_csv(url)
    df['admin_name'] = df['admin_name'].fillna('Unknown')
    df['population'] = pd.to_numeric(df['population'], errors='coerce').fillna(0).astype(int)
    return df

# --- LOAD COUNTY GEOJSON ---
@st.cache_data
def load_county_geojson():
    url = "https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM1/geojson"
    r = requests.get(url)
    return r.json()

# --- RISK DATA EXAMPLE ---
county_risks = {
    "Nairobi": ["Urbanization pressure", "Water scarcity", "Cyber risk"],
    "Mombasa": ["Coastal flooding", "Port security", "Tourism volatility"],
    "Nakuru": ["Soil erosion", "Agri-market shocks", "Urban sprawl"],
    "Uasin Gishu": ["Maize disease", "Land tenure", "Market access"],
    "Kiambu": ["Urban encroachment", "Water stress", "Land fragmentation"],
    "Kakamega": ["Deforestation", "Soil fertility", "Agro-processing"],
    "Turkana": ["Drought", "Livestock loss", "Resource conflict"],
    "Garissa": ["Pastoralist risk", "Drought", "Insecurity"],
    # ...add more as needed, or use a default
}

# --- STREAMLIT UI ---
st.set_page_config(layout="wide", page_title="Kenya City & County Map", page_icon="🌍")
st.title("Kenya Cities, Counties, and Key Risks Map")

city_df = load_city_data()
county_geojson = load_county_geojson()

view_mode = st.sidebar.radio("Map View", ["City Markers", "County Choropleth"])

# --- AGGREGATE CITY DATA BY COUNTY ---
county_counts = city_df['admin_name'].value_counts().reset_index()
county_counts.columns = ['admin_name', 'city_count']

# --- FOLIUM MAP ---
m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='CartoDB positron')

if view_mode == "County Choropleth":
    # Choropleth: all counties colored by number of cities in your CSV
    folium.Choropleth(
        geo_data=county_geojson,
        data=county_counts,
        columns=['admin_name', 'city_count'],
        key_on='feature.properties.shapeName',
        fill_color='YlGnBu',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Number of Major Cities'
    ).add_to(m)

    # Add tooltips with risk info and city count for each county
    for feature in county_geojson['features']:
        county = feature['properties']['shapeName']
        n_cities = county_counts[county_counts['admin_name'] == county]['city_count'].values
        n_cities = int(n_cities[0]) if len(n_cities) else 0
        risks = county_risks.get(county, ["General agri risk", "Market access", "Climate"])
        risk_html = "<br>".join(f"- {r}" for r in risks)
        tooltip = f"<b>{county}</b><br>Cities: {n_cities}<br>Top Risks:<br>{risk_html}"
        folium.GeoJson(
            feature,
            tooltip=tooltip,
            style_function=lambda x: {'fillOpacity': 0, 'color': 'none'}
        ).add_to(m)

else:
    # City markers
    from folium.plugins import MarkerCluster
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in city_df.iterrows():
        county = row['admin_name']
        risks = county_risks.get(county, ["General agri risk", "Market access", "Climate"])
        popup = folium.Popup(
            f"<b>{row['city']}</b><br>County: {county}<br>Population: {row['population']}<br>"
            f"Top Risks:<br>" + "<br>".join(f"- {r}" for r in risks),
            max_width=300
        )
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=popup,
            tooltip=f"{row['city']} ({county})",
            icon=folium.Icon(color='blue' if row['capital'] == 'admin' else 'green')
        ).add_to(marker_cluster)

st_folium(m, width=1000, height=650)

# --- SUMMARY ---
st.write("### County Coverage")
st.dataframe(county_counts.rename(columns={"admin_name": "County", "city_count": "Number of Cities"}))

st.write("### Example of City Data")
st.dataframe(city_df.head(20))
