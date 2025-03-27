import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from collections import Counter

# Page configuration
st.set_page_config(
    page_title="UNIQ Inventory Dashboard",
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
st.title("📊 UNIQ Inventory Dashboard")
st.markdown(
    "Interactive visualization of inventory data across product categories")

# API endpoints
API_ENDPOINTS = {
    "Jeans": "https://unforus.net/UNIQ/reporting-apis/api_jeans_inventory_count.php",
    "Jackets": "https://unforus.net/UNIQ/reporting-apis/api_jackets_inventory_count.php",
    "Kimono & Gilet": "https://unforus.net/UNIQ/reporting-apis/api_kimono_gilet_inventory_count.php"
}

# Function to fetch data from API


@st.cache_data(ttl=600)  # Cache data for 10 minutes
def fetch_inventory_data(api_url):
    """Fetch inventory data from the API"""
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


# Product category selector
st.sidebar.header("Product Category")
selected_category = st.sidebar.radio(
    "Select Product", list(API_ENDPOINTS.keys()))

# Load and process data for the selected category
with st.spinner(f"Fetching {selected_category} inventory data..."):
    df = fetch_inventory_data(API_ENDPOINTS[selected_category])

# Check if data was loaded successfully
if df.empty:
    st.error("No data available. Please check the API connection.")
    st.stop()

# Convert unique_ean_count to numeric
df["unique_ean_count"] = pd.to_numeric(df["unique_ean_count"])

# Create sidebar filters based on the selected product category
st.sidebar.header("Filters")

# Common filters for all product types
# Collection filter
if "collection" in df.columns:
    all_collections = ["All"] + sorted(df["collection"].unique().tolist())
    selected_collection = st.sidebar.selectbox(
        "Select Collection", all_collections)
    if selected_collection != "All":
        df = df[df["collection"] == selected_collection]

# Fit filter
if "fit" in df.columns:
    all_fits = ["All"] + sorted(df["fit"].unique().tolist())
    selected_fit = st.sidebar.selectbox("Select Fit", all_fits)
    if selected_fit != "All":
        df = df[df["fit"] == selected_fit]

# Product-specific filters
if selected_category == "Jeans":
    # Gender filter for jeans
    if "gender" in df.columns:
        all_genders = ["All"] + sorted(df["gender"].unique().tolist())
        selected_gender = st.sidebar.selectbox("Select Gender", all_genders)
        if selected_gender != "All":
            df = df[df["gender"] == selected_gender]

    # Waist size filter for jeans
    if "un_waist" in df.columns:
        all_waists = [
            "All"] + sorted([str(w) for w in df["un_waist"].unique() if pd.notna(w)])
        selected_waist = st.sidebar.selectbox("Select Waist Size", all_waists)
        if selected_waist != "All":
            df = df[df["un_waist"].astype(str) == selected_waist]

elif selected_category == "Jackets":
    # Gender filter for jackets
    if "gender" in df.columns:
        all_genders = ["All"] + sorted(df["gender"].unique().tolist())
        selected_gender = st.sidebar.selectbox("Select Gender", all_genders)
        if selected_gender != "All":
            df = df[df["gender"] == selected_gender]

    # Size filter for jackets
    if "un_size" in df.columns:
        all_sizes = ["All"] + sorted([str(s)
                                     for s in df["un_size"].unique() if pd.notna(s)])
        selected_size = st.sidebar.selectbox("Select Size", all_sizes)
        if selected_size != "All":
            df = df[df["un_size"].astype(str) == selected_size]

    # Color filter for jackets
    if "color" in df.columns:
        all_colors = ["All"] + sorted(df["color"].unique().tolist())
        selected_color = st.sidebar.selectbox("Select Color", all_colors)
        if selected_color != "All":
            df = df[df["color"] == selected_color]

elif selected_category == "Kimono & Gilet":
    # Size filter for kimono/gilet
    if "un_size" in df.columns:
        all_sizes = ["All"] + sorted([str(s)
                                     for s in df["un_size"].unique() if pd.notna(s)])
        selected_size = st.sidebar.selectbox("Select Size", all_sizes)
        if selected_size != "All":
            df = df[df["un_size"].astype(str) == selected_size]

# Store filtered dataframe for use in tabs
filtered_df = df.copy()

# Create dashboard tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Overview", "🧵 Detailed Analysis", "📋 Raw Data", "⚠️ Low Stock"])

# Overview Tab
with tab1:
    # Top metrics row
    col1, col2, col3 = st.columns(3)

    with col1:
        total_ean = filtered_df["unique_ean_count"].sum()
        st.metric("Total Unique Items", f"{total_ean:,}")

    with col2:
        if "fit" in filtered_df.columns:
            total_fits = filtered_df["fit"].nunique()
            st.metric("Fit Styles", total_fits)
        elif "collection" in filtered_df.columns:
            total_collections = filtered_df["collection"].nunique()
            st.metric("Collections", total_collections)
        else:
            st.metric("Product Variations", len(filtered_df))

    with col3:
        if "collection" in filtered_df.columns:
            total_collections = filtered_df["collection"].nunique()
            st.metric("Collections", total_collections)
        elif "color" in filtered_df.columns:
            total_colors = filtered_df["color"].nunique()
            st.metric("Colors", total_colors)
        else:
            avg_count = filtered_df["unique_ean_count"].mean()
            st.metric("Average Stock Per Item", f"{avg_count:.1f}")

    st.markdown("---")

    # Main charts - adapt based on product category
    col1, col2 = st.columns(2)

    # First chart - product specific
    with col1:
        if selected_category == "Jeans":
            if "gender" in filtered_df.columns and "fit" in filtered_df.columns:
                st.subheader("Inventory by Gender and Fit")
                gender_fit_df = filtered_df.groupby(["gender", "fit"])[
                    "unique_ean_count"].sum().reset_index()
                fig = px.bar(
                    gender_fit_df,
                    x="gender",
                    y="unique_ean_count",
                    color="fit",
                    title="Inventory Count by Gender and Fit",
                    labels={"unique_ean_count": "Item Count",
                            "gender": "Gender", "fit": "Fit Style"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.subheader("Inventory by Fit")
                fit_df = filtered_df.groupby(
                    "fit")["unique_ean_count"].sum().reset_index()
                fig = px.bar(
                    fit_df,
                    x="fit",
                    y="unique_ean_count",
                    color="fit",
                    title="Inventory Count by Fit",
                    labels={"unique_ean_count": "Item Count",
                            "fit": "Fit Style"}
                )
                st.plotly_chart(fig, use_container_width=True)

        elif selected_category == "Jackets":
            if "color" in filtered_df.columns:
                st.subheader("Inventory by Color")
                color_df = filtered_df.groupby(
                    "color")["unique_ean_count"].sum().reset_index()
                color_df = color_df.sort_values(
                    by="unique_ean_count", ascending=False)
                fig = px.bar(
                    color_df,
                    x="color",
                    y="unique_ean_count",
                    color="color",
                    title="Inventory by Color",
                    labels={"unique_ean_count": "Item Count", "color": "Color"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.subheader("Inventory by Fit")
                fit_df = filtered_df.groupby(
                    "fit")["unique_ean_count"].sum().reset_index()
                fig = px.bar(
                    fit_df,
                    x="fit",
                    y="unique_ean_count",
                    color="fit",
                    title="Inventory Count by Fit",
                    labels={"unique_ean_count": "Item Count",
                            "fit": "Fit Style"}
                )
                st.plotly_chart(fig, use_container_width=True)

        elif selected_category == "Kimono & Gilet":
            st.subheader("Inventory by Fit")
            fit_df = filtered_df.groupby(
                "fit")["unique_ean_count"].sum().reset_index()
            fig = px.bar(
                fit_df,
                x="fit",
                y="unique_ean_count",
                color="fit",
                title="Inventory Count by Fit",
                labels={"unique_ean_count": "Item Count", "fit": "Fit Style"}
            )
            st.plotly_chart(fig, use_container_width=True)

    # Second chart - Collection distribution for all products
    with col2:
        if "collection" in filtered_df.columns:
            st.subheader("Inventory by Collection")
            collection_df = filtered_df.groupby(
                "collection")["unique_ean_count"].sum().reset_index()
            fig = px.pie(
                collection_df,
                values="unique_ean_count",
                names="collection",
                title="Inventory Distribution by Collection",
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        elif "un_size" in filtered_df.columns:
            st.subheader("Inventory by Size")
            size_df = filtered_df.groupby(
                "un_size")["unique_ean_count"].sum().reset_index()
            fig = px.pie(
                size_df,
                values="unique_ean_count",
                names="un_size",
                title="Inventory Distribution by Size",
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("Overall Inventory")
            inventory_sum = filtered_df["unique_ean_count"].sum()
            fig = go.Figure(go.Indicator(
                mode="number",
                value=inventory_sum,
                title={"text": "Total Inventory Items"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            st.plotly_chart(fig, use_container_width=True)

# Detailed Analysis Tab
with tab2:
    col1, col2 = st.columns(2)

    # First detailed chart - Size distribution (waist for jeans, size for others)
    with col1:
        if "un_waist" in filtered_df.columns:
            st.subheader("Waist Size Distribution")
            waist_df = filtered_df.groupby(
                "un_waist")["unique_ean_count"].sum().reset_index()
            waist_df = waist_df.sort_values(by="un_waist")
            fig = px.bar(
                waist_df,
                x="un_waist",
                y="unique_ean_count",
                title="Inventory by Waist Size",
                labels={"unique_ean_count": "Item Count",
                        "un_waist": "Waist Size"}
            )
            st.plotly_chart(fig, use_container_width=True)
        elif "un_size" in filtered_df.columns:
            st.subheader("Size Distribution")
            size_df = filtered_df.groupby(
                "un_size")["unique_ean_count"].sum().reset_index()
            size_df = size_df.sort_values(by="un_size")
            fig = px.bar(
                size_df,
                x="un_size",
                y="unique_ean_count",
                title="Inventory by Size",
                labels={"unique_ean_count": "Item Count", "un_size": "Size"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("Inventory Distribution")
            total_items = filtered_df["unique_ean_count"].sum()
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=total_items,
                gauge={'axis': {'range': [0, total_items * 1.5]},
                       'bar': {'color': "darkblue"}},
                title={"text": "Total Inventory"}
            ))
            st.plotly_chart(fig, use_container_width=True)

    # Second detailed chart - Fit style or color popularity
    with col2:
        if "fit" in filtered_df.columns:
            st.subheader("Fit Style Popularity")
            fit_df = filtered_df.groupby(
                "fit")["unique_ean_count"].sum().reset_index()
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
        elif "color" in filtered_df.columns:
            st.subheader("Color Popularity")
            color_df = filtered_df.groupby(
                "color")["unique_ean_count"].sum().reset_index()
            color_df = color_df.sort_values(
                by="unique_ean_count", ascending=False)
            fig = px.bar(
                color_df,
                x="color",
                y="unique_ean_count",
                title="Inventory by Color",
                labels={"unique_ean_count": "Item Count", "color": "Color"},
                color="color"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("Stock Distribution")
            fig = px.histogram(
                filtered_df,
                x="unique_ean_count",
                nbins=20,
                title="Distribution of Stock Counts",
                labels={"unique_ean_count": "Stock Count",
                        "count": "Number of Items"}
            )
            st.plotly_chart(fig, use_container_width=True)

    # Heatmap for combinations - adapt based on product category
    if selected_category == "Jeans" and "gender" in filtered_df.columns and "collection" in filtered_df.columns and "fit" in filtered_df.columns:
        st.subheader("Inventory Heatmap: Gender × Collection × Fit")
        try:
            heatmap_df = filtered_df.pivot_table(
                index=["gender", "collection"],
                columns="fit",
                values="unique_ean_count",
                aggfunc="sum",
                fill_value=0
            )

            fig = px.imshow(
                heatmap_df,
                labels=dict(x="Fit Style", y="Gender & Collection",
                            color="Item Count"),
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Viridis"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not create heatmap: {e}")

    elif selected_category == "Jackets" and "color" in filtered_df.columns and "fit" in filtered_df.columns:
        st.subheader("Inventory Heatmap: Color × Fit")
        try:
            heatmap_df = filtered_df.pivot_table(
                index="color",
                columns="fit",
                values="unique_ean_count",
                aggfunc="sum",
                fill_value=0
            )

            fig = px.imshow(
                heatmap_df,
                labels=dict(x="Fit Style", y="Color", color="Item Count"),
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Viridis"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not create heatmap: {e}")

    elif selected_category == "Kimono & Gilet" and "un_size" in filtered_df.columns and "fit" in filtered_df.columns:
        st.subheader("Inventory Heatmap: Size × Fit")
        try:
            heatmap_df = filtered_df.pivot_table(
                index="un_size",
                columns="fit",
                values="unique_ean_count",
                aggfunc="sum",
                fill_value=0
            )

            fig = px.imshow(
                heatmap_df,
                labels=dict(x="Fit Style", y="Size", color="Item Count"),
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Viridis"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not create heatmap: {e}")

# Raw Data Tab
with tab3:
    st.subheader(f"Raw {selected_category} Inventory Data")

    # Download button for CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name=f"{selected_category.lower().replace(' & ', '_')}_inventory.csv",
        mime="text/csv",
    )

    # Show dataframe
    st.dataframe(filtered_df, use_container_width=True)

    # Summary statistics
    if st.checkbox("Show Summary Statistics"):
        st.write(filtered_df.describe())

# Low Stock Tab
with tab4:
    st.subheader(f"Low Stock {selected_category} Analysis")

    # Let user define what "low stock" means
    low_stock_threshold = st.slider("Low Stock Threshold", 1, 30, 10)

    # Filter for low stock items
    low_stock_df = filtered_df[filtered_df["unique_ean_count"]
                               <= low_stock_threshold].copy()

    if low_stock_df.empty:
        st.info(
            f"No {selected_category} items below the threshold of {low_stock_threshold} units.")
    else:
        st.write(
            f"Found {len(low_stock_df)} items with stock at or below {low_stock_threshold} units.")

        # Create visualizations based on product category
        col1, col2 = st.columns(2)

        with col1:
            # Low stock distribution chart
            if "fit" in low_stock_df.columns:
                st.subheader("Low Stock by Fit Style")
                low_fit_df = low_stock_df.groupby(
                    "fit")["unique_ean_count"].count().reset_index()
                low_fit_df = low_fit_df.sort_values(
                    by="unique_ean_count", ascending=False)
                fig = px.bar(
                    low_fit_df,
                    x="fit",
                    y="unique_ean_count",
                    color="fit",
                    title=f"Low Stock Items by Fit Style (≤ {low_stock_threshold} units)",
                    labels={
                        "unique_ean_count": "Number of Low Stock Items", "fit": "Fit Style"}
                )
                st.plotly_chart(fig, use_container_width=True)
            elif "color" in low_stock_df.columns:
                st.subheader("Low Stock by Color")
                low_color_df = low_stock_df.groupby(
                    "color")["unique_ean_count"].count().reset_index()
                low_color_df = low_color_df.sort_values(
                    by="unique_ean_count", ascending=False)
                fig = px.bar(
                    low_color_df,
                    x="color",
                    y="unique_ean_count",
                    color="color",
                    title=f"Low Stock Items by Color (≤ {low_stock_threshold} units)",
                    labels={
                        "unique_ean_count": "Number of Low Stock Items", "color": "Color"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.subheader("Low Stock Distribution")
                fig = px.histogram(
                    low_stock_df,
                    x="unique_ean_count",
                    nbins=low_stock_threshold,
                    title=f"Distribution of Low Stock Counts (≤ {low_stock_threshold} units)",
                    labels={"unique_ean_count": "Stock Count",
                            "count": "Number of Items"}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Second low stock chart
            if "collection" in low_stock_df.columns:
                st.subheader("Low Stock by Collection")
                low_collection_df = low_stock_df.groupby(
                    "collection")["unique_ean_count"].count().reset_index()
                fig = px.pie(
                    low_collection_df,
                    values="unique_ean_count",
                    names="collection",
                    title=f"Low Stock Items by Collection (≤ {low_stock_threshold} units)",
                    hole=0.4
                )
                fig.update_traces(textposition='inside',
                                  textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            elif "un_size" in low_stock_df.columns or "un_waist" in low_stock_df.columns:
                size_col = "un_size" if "un_size" in low_stock_df.columns else "un_waist"
                size_label = "Size" if size_col == "un_size" else "Waist Size"
                st.subheader(f"Low Stock by {size_label}")
                low_size_df = low_stock_df.groupby(
                    size_col)["unique_ean_count"].count().reset_index()
                fig = px.pie(
                    low_size_df,
                    values="unique_ean_count",
                    names=size_col,
                    title=f"Low Stock Items by {size_label} (≤ {low_stock_threshold} units)",
                    hole=0.4
                )
                fig.update_traces(textposition='inside',
                                  textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.subheader("Low Stock Summary")
                avg_low_stock = low_stock_df["unique_ean_count"].mean()
                fig = go.Figure(go.Indicator(
                    mode="number+gauge",
                    value=avg_low_stock,
                    number={"suffix": " units"},
                    gauge={
                        'axis': {'range': [0, low_stock_threshold]},
                        'bar': {'color': "red"},
                        'steps': [
                            {'range': [0, low_stock_threshold/3],
                                'color': "darkred"},
                            {'range': [low_stock_threshold/3, 2 *
                                       low_stock_threshold/3], 'color': "orange"},
                            {'range': [2*low_stock_threshold/3,
                                       low_stock_threshold], 'color': "yellow"}
                        ]
                    },
                    title={"text": "Average Stock Level of Low Stock Items"}
                ))
                st.plotly_chart(fig, use_container_width=True)

        # Create a treemap for low stock distribution
        st.subheader("Low Stock Distribution Treemap")

        # Define hierarchical path based on available columns
        treemap_path = []
        if "gender" in low_stock_df.columns:
            treemap_path.append("gender")
        if "collection" in low_stock_df.columns:
            treemap_path.append("collection")
        if "fit" in low_stock_df.columns:
            treemap_path.append("fit")
        if "color" in low_stock_df.columns:
            treemap_path.append("color")
        if "un_size" in low_stock_df.columns:
            treemap_path.append("un_size")
        elif "un_waist" in low_stock_df.columns:
            treemap_path.append("un_waist")

        # Only proceed if we have columns to create hierarchy
        if treemap_path:
            # Group data according to the path
            treemap_data = low_stock_df.groupby(
                treemap_path)['unique_ean_count'].sum().reset_index()

            fig = px.treemap(
                treemap_data,
                path=treemap_path,
                values='unique_ean_count',
                color='unique_ean_count',
                color_continuous_scale='Reds',
                title=f'Low Stock Distribution Across Categories (≤ {low_stock_threshold} units)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough categorical data to create a treemap visualization.")

        # Create a sunburst chart for hierarchical view
        st.subheader("Low Stock Hierarchy (Sunburst)")

        # Use the same path as treemap
        if treemap_path:
            sunburst_data = low_stock_df.groupby(
                treemap_path)['unique_ean_count'].sum().reset_index()
            fig = px.sunburst(
                sunburst_data,
                path=treemap_path,
                values='unique_ean_count',
                color='unique_ean_count',
                color_continuous_scale='Reds',
                title=f'Hierarchical View of Low Stock (≤ {low_stock_threshold} units)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough categorical data to create a sunburst visualization.")

        # Create a parallel coordinates plot
        st.subheader("Low Stock Patterns (Parallel Coordinates)")

        # Only create the parallel coordinates if we have enough dimensions
        if len(low_stock_df.columns) >= 3:
            # Select columns for parallel coordinates
            parcoords_cols = []

            # Add categorical dimensions
            for col in ['gender', 'collection', 'fit', 'color', 'un_size', 'un_waist']:
                if col in low_stock_df.columns:
                    parcoords_cols.append(col)

            # Always include stock count
            parcoords_cols.append('unique_ean_count')

            # Only proceed if we have at least 3 dimensions (2 categorical + stock count)
            if len(parcoords_cols) >= 3:
                # Prepare data for parallel coordinates
                parallel_data = low_stock_df[parcoords_cols].copy()

                # Create dimensions list for the plot
                dimensions = []

                # Add categorical dimensions
                for col in parcoords_cols:
                    if col != 'unique_ean_count':
                        # Map categorical values to numeric indices
                        unique_vals = parallel_data[col].unique()
                        val_map = {val: idx for idx, val in enumerate(unique_vals)}

                        dimensions.append(
                            dict(
                                range=[0, len(unique_vals)],
                                tickvals=list(range(len(unique_vals))),
                                ticktext=unique_vals,
                                label=col,
                                values=parallel_data[col].map(val_map)
                            )
                        )

                # Add stock count dimension
                dimensions.append(
                    dict(
                        range=[0, low_stock_threshold],
                        label='Stock Count',
                        values=parallel_data['unique_ean_count']
                    )
                )

                # Create the parallel coordinates plot
                fig = go.Figure(data=go.Parcoords(
                    line=dict(
                        color=parallel_data['unique_ean_count'],
                        colorscale='Reds',
                        showscale=True
                    ),
                    dimensions=dimensions
                )
                )

                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    title=f'Low Stock Patterns Across Categories (≤ {low_stock_threshold} units)',
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(
                    "Not enough dimensions available to create a parallel coordinates plot.")
        else:
            st.info("Not enough data dimensions to create a parallel coordinates visualization.")

        # Detailed low stock table
        st.subheader("Detailed Low Stock Items")
        st.dataframe(low_stock_df.sort_values(
            "unique_ean_count"), use_container_width=True)

        # Download low stock data
        csv = low_stock_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download low stock data as CSV",
            data=csv,
            file_name=f"low_stock_{selected_category.lower().replace(' & ', '_')}_inventory.csv",
            mime="text/csv",
        )

# Footer
st.markdown("---")
st.markdown("*Data provided by UNIQ Inventory API*")
