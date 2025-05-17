import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html
import shap
import numpy as np
import plotly.express as px
import xgboost as xgb
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
from sklearn.metrics import classification_report, accuracy_score
from skopt import BayesSearchCV
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt

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
section[data-testid="stSidebar"] > div:first-child {{
    background-color: #f0f4f8;
    padding-top: 2rem;
    border-right: 2px solid #ddd;
    font-family: Arial, sans-serif;
    color: #333;
}}
</style>
<img src="{LOGO_LEFT_URL}" class="fixed-logo-left" alt="Ubuntu Impact Labs Logo">
<img src="{LOGO_RIGHT_URL}" class="fixed-logo-right" alt="Kenya Flag">
""", height=0)

st.markdown("<div style='height: 130px;'></div>", unsafe_allow_html=True)

# ======================
# SIDEBAR NAVIGATION
# ======================
page = st.sidebar.radio("Navigation", [
    "Home", "Interactive Map", "Model Results", "Visuals", "Benchmark Models", "Summary", "About", "Contact"
])

# ======================
# DATA LOADING
# ======================
@st.cache_data
def load_city_data():
    url = "https://raw.githubusercontent.com/mrIbadan/Kenya_Map_Test/main/ke.csv"
    df = pd.read_csv(url)
    df['admin_name'] = df['admin_name'].fillna('Unknown')
    df['population'] = pd.to_numeric(df['population'], errors='coerce').fillna(0).astype(int)
    # Add more variation for demo
    df['risk_index'] = np.random.randint(1, 100, len(df))
    df['yield_tons'] = np.random.normal(1000, 300, len(df)).astype(int)
    df['rainfall_mm'] = np.random.normal(800, 200, len(df)).astype(int)
    return df

@st.cache_data
def load_county_geojson():
    url = "https://ckan.africadatahub.org/dataset/32b18687-6e88-43b3-94ec-34846b89575f/resource/108ca393-d26d-450d-ac5d-4474ac04212a/download/kenya-counties-simplified.geojson"
    return requests.get(url).json()

# ======================
# AGRICULTURAL RISKS
# ======================
region_agricultural_risks = {
    "Nairobi": {"risks": ["Urban agriculture water scarcity", "Food supply chain disruptions", "Land pressure"], "severity": "Moderate", "type": "Urban", "details": "Urban farming faces water constraints"},
    "Uasin Gishu": {"risks": ["Maize disease", "Erratic rainfall", "Market access issues"], "severity": "Critical", "type": "Maize", "details": "Breadbasket disease pressure"},
    "Kitui": {"risks": ["Severe drought", "Crop failure", "Charcoal dependence"], "severity": "Critical", "type": "Weather", "details": "Food security risks"},
    "Kisumu": {"risks": ["Lake pollution", "Flooding", "Fish stock decline"], "severity": "High", "type": "Lake", "details": "Lake ecosystem degradation"},
    "Mombasa": {"risks": ["Coastal erosion", "Saltwater intrusion", "Marine threats"], "severity": "High", "type": "Coastal", "details": "Coastal farming affected by rising sea levels"},
    "DEFAULT": {"risks": ["Generic risks"], "severity": "Low", "type": "General", "details": "General challenges"}
}
risk_color_map = {
    "Critical": "#ff4d4d",
    "High": "#ffa07a",
    "Moderate": "#add8e6",
    "Low": "#90ee90",
    "None": "#d3d3d3"
}

# ======================
# PAGE ROUTING
# ======================
if page == "Home":
    st.title("Kenya Agricultural Monitoring System")
    st.markdown("""
    ## Welcome
    Explore Kenya's agricultural risks via interactive tools, models, and data visualizations.
    """)

elif page == "Interactive Map":
    st.title("Agricultural Risk Map")
    city_df = load_city_data()
    geojson = load_county_geojson()
    selected_type = st.selectbox("Risk Type", ["All"] + sorted(set(v['type'] for k, v in region_agricultural_risks.items() if k != 'DEFAULT')))
    m = folium.Map(location=[0.2, 37.0], zoom_start=6, tiles='cartodb positron')
    geo_key = next((k for k in ["shapeName", "name"] if k in geojson['features'][0]['properties']), None)

    # County polygons with tooltips
    for feature in geojson['features']:
        county = feature['properties'][geo_key]
        risk_info = region_agricultural_risks.get(county, region_agricultural_risks['DEFAULT'])
        if selected_type == "All" or risk_info['type'] == selected_type:
            popup_content = (
                f"<b>{county}</b><br>"
                f"Risk Type: {risk_info['type']}<br>"
                f"Severity: {risk_info['severity']}<br>"
                f"Details: {risk_info['details']}"
            )
            folium.GeoJson(
                feature,
                tooltip=folium.Tooltip(popup_content, sticky=True),
                style_function=lambda x, s=risk_info['severity']: {
                    'fillColor': risk_color_map.get(s, '#d3d3d3'),
                    'color': risk_color_map.get(s, '#d3d3d3'),
                    'fillOpacity': 0.6,
                    'weight': 1
                }
            ).add_to(m)

    # City markers with more variation
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in city_df.iterrows():
        county = row['admin_name']
        risk_info = region_agricultural_risks.get(county, region_agricultural_risks['DEFAULT'])
        if selected_type == "All" or risk_info['type'] == selected_type:
            popup = (
                f"<b>{row['city']}</b><br>"
                f"County: {county}<br>"
                f"Population: {row['population']}<br>"
                f"Yield (tons): {row['yield_tons']}<br>"
                f"Rainfall (mm): {row['rainfall_mm']}<br>"
                f"Risk Index: {row['risk_index']}<br>"
                f"Risks: {', '.join(risk_info['risks'])}<br>"
                f"Severity: {risk_info['severity']}<br>"
                f"Type: {risk_info['type']}<br>"
                f"Details: {risk_info['details']}"
            )
            folium.Marker(
                location=[row['lat'], row['lng']],
                popup=popup,
                tooltip=f"{row['city']} ({risk_info['severity']} risk)",
                icon=folium.Icon(color='blue' if risk_info['severity'] in ['Low', 'Moderate'] else 'red')
            ).add_to(marker_cluster)

    st_folium(m, width=1000, height=650)

elif page == "Model Results":
    st.title("Risk Model - GBM")
    X, y = make_classification(n_samples=1000, n_features=10, n_informative=5, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y)
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    st.subheader("Classification Report")
    st.text(classification_report(y_test, y_pred))
    explainer = shap.Explainer(model)
    shap_values = explainer(X_test)
    st.subheader("SHAP Summary Plot")
    shap.summary_plot(shap_values, X_test, show=False)
    st.pyplot(bbox_inches='tight')

elif page == "Visuals":
    st.title("Model Visuals")
    chart_data = pd.DataFrame({
        'Year': range(2015, 2025),
        'Risk Index': np.random.rand(10) * 100
    })
    fig = px.line(chart_data, x='Year', y='Risk Index', title='Risk Index Over Time', markers=True)
    fig.update_layout(template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)

elif page == "Benchmark Models":
    st.title("Model Benchmark: GBM vs GLM / XGBoost vs LightGBM")
    X, y = make_classification(n_samples=1000, n_features=10, n_informative=6, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)
    glm = LogisticRegression()
    glm.fit(X_train, y_train)
    glm_score = accuracy_score(y_test, glm.predict(X_test))
    gbm_search = BayesSearchCV(xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'), {
        'max_depth': (3, 10),
        'learning_rate': (0.01, 0.3, 'log-uniform')
    }, n_iter=10, cv=3)
    gbm_search.fit(X_train, y_train)
    gbm_score = accuracy_score(y_test, gbm_search.predict(X_test))
    lgbm_search = BayesSearchCV(lgb.LGBMClassifier(), {
        'max_depth': (3, 10),
        'learning_rate': (0.01, 0.3, 'log-uniform')
    }, n_iter=10, cv=3)
    lgbm_search.fit(X_train, y_train)
    lgbm_score = accuracy_score(y_test, lgbm_search.predict(X_test))
    st.metric("GLM Accuracy", f"{glm_score:.3f}")
    st.metric("XGBoost (Bayesian Opt) Accuracy", f"{gbm_score:.3f}")
    st.metric("LightGBM (Bayesian Opt) Accuracy", f"{lgbm_score:.3f}")

elif page == "Summary":
    st.title("Summary")
    df = load_city_data()
    st.metric("Total Cities", len(df))
    st.metric("Total Population", f"{df['population'].sum():,}")
    st.dataframe(df.head())

elif page == "About":
    st.title("About")
    st.markdown("""
    This project uses geospatial and statistical tools to monitor agricultural risk in Kenya.

    Built by Ubuntu Impact Labs using Python, Streamlit, Folium, Plotly and open datasets.
    """)

elif page == "Contact":
    st.title("Contact")
    st.markdown("""
    Email: [info@kenyarisksystem.org](mailto:info@kenyarisksystem.org)
    Phone: +254 700 123 456  
    LinkedIn: Kenya Risk Monitoring  
    Twitter: @KenyaAgriRisk
    """)
