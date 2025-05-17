import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from folium.plugins import MarkerCluster
import json
import time

# Configure page
st.set_page_config(layout="wide", page_title="Kenya Counties & Cities Map", page_icon="🇰🇪")

# --- LOAD DATA FUNCTIONS ---
@st.cache_data
def load_city_data():
    """Load Kenya cities data"""
    try:
        url = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/ke.csv"
        df = pd.read_csv(url)
        # Clean up data
        df['admin_name'] = df['admin_name'].fillna('Unknown')
        df['population'] = pd.to_numeric(df['population'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Error loading city data: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_county_geojson():
    """Load Kenya counties GeoJSON with multiple fallback options"""
    
    # List of URLs to try in order
    urls = [
        "https://ckan.africadatahub.org/dataset/32b18687-6e88-43b3-94ec-34846b89575f/resource/108ca393-d26d-450d-ac5d-4474ac04212a/download/kenya-counties-simplified.geojson",
        "https://data.humdata.org/dataset/e66dbc70-17fe-4230-b9d6-855d192fc05c/resource/51939d78-35aa-4591-9831-11e61e555130/download/kenya.geojson",
        "https://www.geoboundaries.org/api/current/gbOpen/KEN/ADM1/geojson"
    ]
    
    error_messages = []
    
    # Try each URL
    for url in urls:
        try:
            st.write(f"Trying to load GeoJSON from: {url}")
            response = requests.get(url, timeout=10)
            
            # Check if status code is successful
            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    geojson_data = response.json()
                    st.success(f"Successfully loaded GeoJSON from {url}")
                    return geojson_data
                except json.JSONDecodeError as e:
                    error_messages.append(f"Invalid JSON from {url}: {str(e)}")
                    continue
            else:
                error_messages.append(f"HTTP Error {response.status_code} from {url}")
                continue
                
        except Exception as e:
            error_messages.append(f"Error accessing {url}: {str(e)}")
            continue
    
    # If all URLs fail, use basic fallback GeoJSON
    st.warning(f"Failed to load GeoJSON from all sources. Using simplified fallback version.")
    for error in error_messages:
        st.error(error)
    
    # Return simplified Kenya regions as fallback
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"shapeName": "Nairobi"}, "geometry": {"type": "Polygon", "coordinates": [[[36.7, -1.35], [37.05, -1.35], [37.05, -1.15], [36.7, -1.15], [36.7, -1.35]]]}},
            {"type": "Feature", "properties": {"shapeName": "Mombasa"}, "geometry": {"type": "Polygon", "coordinates": [[[39.5, -4.1], [39.8, -4.1], [39.8, -3.9], [39.5, -3.9], [39.5, -4.1]]]}},
            {"type": "Feature", "properties": {"shapeName": "Kisumu"}, "geometry": {"type": "Polygon", "coordinates": [[[34.6, -0.2], [34.9, -0.2], [34.9, 0.1], [34.6, 0.1], [34.6, -0.2]]]}},
            {"type": "Feature", "properties": {"shapeName": "Nakuru"}, "geometry": {"type": "Polygon", "coordinates": [[[35.8, -0.4], [36.2, -0.4], [36.2, -0.1], [35.8, -0.1], [35.8, -0.4]]]}},
            {"type": "Feature", "properties": {"shapeName": "Kiambu"}, "geometry": {"type": "Polygon", "coordinates": [[[36.7, -1.15], [37.0, -1.15], [37.0, -0.9], [36.7, -0.9], [36.7, -1.15]]]}},
            {"type": "Feature", "properties": {"shapeName": "Uasin Gishu"}, "geometry": {"type": "Polygon", "coordinates": [[[35.0, 0.3], [35.5, 0.3], [35.5, 0.7], [35.0, 0.7], [35.0, 0.3]]]}},
            {"type": "Feature", "properties": {"shapeName": "Kakamega"}, "geometry": {"type": "Polygon", "coordinates": [[[34.5, 0.1], [34.9, 0.1], [34.9, 0.5], [34.5, 0.5], [34.5, 0.1]]]}},
            {"type": "Feature", "properties": {"shapeName": "Kilifi"}, "geometry": {"type": "Polygon", "coordinates": [[[39.5, -3.9], [40.0, -3.9], [40.0, -3.1], [39.5, -3.1], [39.5, -3.9]]]}}
        ]
    }

# --- COUNTY RISK DATA ---
def get_county_risks():
    """Define agricultural risks per county"""
    return {
        "Nairobi": ["Urban sprawl", "Water scarcity", "Food distribution"],
        "Mombasa": ["Coastal erosion", "Marine ecosystem", "Tourism impact"],
        "Kisumu": ["Lake pollution", "Fisheries decline", "Flooding"],
        "Nakuru": ["Land degradation", "Water pollution", "Maize diseases"],
        "Uasin Gishu": ["Erratic rainfall", "Wheat rust", "Market access"],
        "Kiambu": ["Coffee diseases", "Land fragmentation", "Dairy challenges"],
        "Kilifi": ["Drought risk", "Cashew diseases", "Coastal erosion"],
        "Kakamega": ["Deforestation", "Maize diseases", "Land subdivision"],
        # Add more counties as needed
        "DEFAULT": ["Climate risk", "Market access", "Water resources"]
    }

# --- MAIN APP ---
st.title("Kenya Counties and Agricultural Risks Map")
st.write("Interactive visualization of major cities and agricultural risks across Kenya counties.")

# Progress indicator while loading data
with st.spinner("Loading data..."):
    # Load data
    city_df = load_city_data()
    
    # Only proceed if we have city data
    if not city_df.empty:
        county_geojson = load_county_geojson()
        county_risks = get_county_risks()
        
        # Create county summary
        county_counts = city_df['admin_name'].value_counts().reset_index()
        county_counts.columns = ['admin_name', 'city_count']
        
        # --- SIDEBAR ---
        st.sidebar.title("Map Options")
        view_mode = st.sidebar.radio("Select View", ["County Choropleth", "City Markers", "Combined View"])
        
        # --- CREATE MAP ---
        m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles="CartoDB positron")
        
        # ADD CHOROPLETH LAYER
        if view_mode in ["County Choropleth", "Combined View"]:
            # Try different property keys based on what might be in the GeoJSON
            possible_keys = ["shapeName", "name", "NAME_1", "admin", "ADM1_EN"]
            key_used = None
            
            for key in possible_keys:
                # Check if this key exists in the first feature
                if "features" in county_geojson and len(county_geojson["features"]) > 0:
                    if key in county_geojson["features"][0]["properties"]:
                        key_used = key
                        break
            
            if key_used:
                try:
                    folium.Choropleth(
                        geo_data=county_geojson,
                        name='Counties',
                        data=county_counts,
                        columns=['admin_name', 'city_count'],
                        key_on=f'feature.properties.{key_used}',
                        fill_color='YlGn',
                        fill_opacity=0.7,
                        line_opacity=0.2,
                        legend_name='Number of Cities'
                    ).add_to(m)
                    
                    # Add tooltips to counties
                    folium.GeoJson(
                        county_geojson,
                        name="County Info",
                        style_function=lambda x: {"fillOpacity": 0, "color": "transparent"},
                        tooltip=folium.GeoJsonTooltip(
                            fields=[key_used],
                            aliases=["County:"],
                            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
                        )
                    ).add_to(m)
                except Exception as e:
                    st.error(f"Error adding choropleth: {str(e)}")
            else:
                st.warning("Could not determine the correct property key in GeoJSON. Choropleth may not display correctly.")
        
        # ADD CITY MARKERS
        if view_mode in ["City Markers", "Combined View"]:
            marker_cluster = MarkerCluster().add_to(m)
            
            for _, city in city_df.iterrows():
                # Skip cities with invalid coordinates
                if pd.isnull(city['lat']) or pd.isnull(city['lng']):
                    continue
                
                # Get risk info
                county = city['admin_name']
                risks = county_risks.get(county, county_risks["DEFAULT"])
                
                # Format risks as HTML
                risk_html = "<br>".join([f"• {risk}" for risk in risks])
                
                # Create popup content
                popup_html = f"""
                <div style="width: 200px; font-family: Arial;">
                    <h3 style="text-align: center; margin: 8px 0;">{city['city']}</h3>
                    <p><b>County:</b> {county}</p>
                    <p><b>Population:</b> {int(city['population']):,}</p>
                    <hr style="margin: 5px 0;">
                    <p><b>Agricultural Risks:</b></p>
                    <div style="margin-left: 10px;">{risk_html}</div>
                </div>
                """
                
                # Add marker
                icon_color = 'red' if city['capital'] == 'admin' else 'blue'
                icon_type = 'globe' if city['capital'] == 'admin' else 'map-marker'
                
                folium.Marker(
                    location=[city['lat'], city['lng']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{city['city']} ({county})",
                    icon=folium.Icon(color=icon_color, icon=icon_type, prefix='fa')
                ).add_to(marker_cluster)
        
        # Add layer control and display map
        folium.LayerControl().add_to(m)
        st_folium(m, width=950, height=600)
        
        # --- STATISTICS ---
        st.subheader("County Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Counties", len(county_counts))
        with col2:
            st.metric("Total Cities", len(city_df))
        with col3:
            admin_cities = len(city_df[city_df['capital'] == 'admin'])
            st.metric("Administrative Centers", admin_cities)
        
        # Show county table
        st.write("### Cities per County")
        st.dataframe(county_counts.rename(columns={"admin_name": "County", "city_count": "Number of Cities"}).sort_values("Number of Cities", ascending=False))
    else:
        st.error("Failed to load city data. Please try again later.")
