import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from collections import Counter

# Page configuration
st.set_page_config(
    page_title="Jeans Inventory Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 1rem 1rem;
    }
    .stMetric {
        background-color: #000000;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }

    [data-testid="stTabContent"] {
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.title("📊 Jeans Inventory Dashboard")
st.markdown("Interactive visualization of jeans inventory data")

# Function to fetch data from API
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def fetch_inventory_data():
    """Fetch jeans inventory data from the API"""
    api_url = "https://unforus.net/UNIQ/reporting-apis/api_jeans_inventory_count.php"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        if data["status"] == "success":
            return pd.DataFrame(data["data"])
        else:
            st.error(f"API returned error status: {data['status']}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Load and process data
with st.spinner("Fetching inventory data..."):
    df = fetch_inventory_data()

# Check if data was loaded successfully
if df.empty:
    st.error("No data available. Please check the API connection.")
    st.stop()

# Convert unique_ean_count to numeric
df["unique_ean_count"] = pd.to_numeric(df["unique_ean_count"])

# Create sidebar filters
st.sidebar.header("Filters")

# Gender filter
all_genders = ["All"] + sorted(df["gender"].unique().tolist())
selected_gender = st.sidebar.selectbox("Select Gender", all_genders)

# Collection filter
all_collections = ["All"] + sorted(df["collection"].unique().tolist())
selected_collection = st.sidebar.selectbox("Select Collection", all_collections)

# Fit filter
all_fits = ["All"] + sorted(df["fit"].unique().tolist())
selected_fit = st.sidebar.selectbox("Select Fit", all_fits)

# Apply filters
filtered_df = df.copy()
if selected_gender != "All":
    filtered_df = filtered_df[filtered_df["gender"] == selected_gender]
if selected_collection != "All":
    filtered_df = filtered_df[filtered_df["collection"] == selected_collection]
if selected_fit != "All":
    filtered_df = filtered_df[filtered_df["fit"] == selected_fit]

# Create dashboard layout
tab1, tab2, tab3 = st.tabs(["📈 Overview", "🧵 Detailed Analysis", "📋 Raw Data"])

with tab1:
    # Top metrics row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_ean = filtered_df["unique_ean_count"].sum()
        st.metric("Total Unique Items", f"{total_ean:,}")
    
    with col2:
        total_fits = filtered_df["fit"].nunique()
        st.metric("Fit Styles", total_fits)
    
    with col3:
        total_collections = filtered_df["collection"].nunique()
        st.metric("Collections", total_collections)
    
    st.markdown("---")
    
    # Main charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Inventory by Gender and Fit")
        gender_fit_df = df.groupby(["gender", "fit"])["unique_ean_count"].sum().reset_index()
        fig = px.bar(
            gender_fit_df,
            x="gender",
            y="unique_ean_count",
            color="fit",
            title="Inventory Count by Gender and Fit",
            labels={"unique_ean_count": "Item Count", "gender": "Gender", "fit": "Fit Style"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Inventory by Collection")
        collection_df = df.groupby("collection")["unique_ean_count"].sum().reset_index()
        fig = px.pie(
            collection_df,
            values="unique_ean_count",
            names="collection",
            title="Inventory Distribution by Collection",
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Waist Size Distribution")
        waist_df = filtered_df.groupby("un_waist")["unique_ean_count"].sum().reset_index()
        waist_df = waist_df.sort_values(by="un_waist")
        fig = px.bar(
            waist_df,
            x="un_waist",
            y="unique_ean_count",
            title="Inventory by Waist Size",
            labels={"unique_ean_count": "Item Count", "un_waist": "Waist Size"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Fit Style Popularity")
        fit_df = filtered_df.groupby("fit")["unique_ean_count"].sum().reset_index()
        fit_df = fit_df.sort_values(by="unique_ean_count", ascending=False)
        fig = px.bar(
            fit_df,
            x="fit",
            y="unique_ean_count",
            title="Inventory by Fit Style",
            labels={"unique_ean_count": "Item Count", "fit": "Fit Style"},
            color="fit"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap for combinations
    st.subheader("Inventory Heatmap: Gender × Collection × Fit")
    heatmap_df = df.pivot_table(
        index=["gender", "collection"],
        columns="fit",
        values="unique_ean_count",
        aggfunc="sum",
        fill_value=0
    )
    
    fig = px.imshow(
        heatmap_df,
        labels=dict(x="Fit Style", y="Gender & Collection", color="Item Count"),
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Raw Inventory Data")
    
    # Download button for CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="jeans_inventory.csv",
        mime="text/csv",
    )
    
    # Show dataframe
    st.dataframe(filtered_df, use_container_width=True)
    
    # Summary statistics
    if st.checkbox("Show Summary Statistics"):
        st.write(filtered_df.describe())

# Footer
st.markdown("---")
st.markdown("*Data provided by UnDenim Jeans Inventory API*")