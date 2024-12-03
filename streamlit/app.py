import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

# Connect to PostgreSQL Database
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="pg-cgi-chronic-disease-indicators.e.aivencloud.com",
        database="cdi",
        user="avnadmin",
        password="AVNS_5sy_zeptMJyBrvRiJM9",
        port="15815"
    )

# Fetch Data from Database
def run_query(query):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return []

# Streamlit App Layout
st.title("U.S. Chronic Disease Indicators (CDI) Explorer")
st.sidebar.header("Filter Options")

# Sidebar Filters
location_data = run_query("SELECT DISTINCT LocationDesc FROM Location")
location = st.sidebar.selectbox("Select Location", 
    options=["All"] + [row["locationdesc"] for row in location_data] if location_data else ["All"])

topic_data = run_query("SELECT DISTINCT Topic FROM Topic")
topic = st.sidebar.selectbox("Select Topic", 
    options=["All"] + [row["topic"] for row in topic_data] if topic_data else ["All"])

datasource_data = run_query("SELECT DISTINCT DataSource FROM DataSource")
datasource = st.sidebar.selectbox("Select Data Source", 
    options=["All"] + [row["datasource"] for row in datasource_data] if datasource_data else ["All"])

# Build Query Based on Schema
base_query = """
    SELECT 
        l.LocationDesc,
        t.Topic,
        ds.DataSource,
        q.Question,
        c.DataValueType,
        c.DataValue,
        c.Year,
        c.LowConfidenceLimit,
        c.HighConfidenceLimit,
        l.Latitude,
        l.Longitude
    FROM CDI c
    JOIN Location l ON c.LocationID = l.LocationID
    JOIN DataSource ds ON c.DataSourceID = ds.DataSourceID
    JOIN Topic t ON c.TopicID = t.TopicID
    JOIN Question q ON c.QuestionID = q.QuestionID
"""

# Add Filters
filters = []
if location != "All":
    filters.append(f"l.LocationDesc = '{location}'")
if topic != "All":
    filters.append(f"t.Topic = '{topic}'")
if datasource != "All":
    filters.append(f"ds.DataSource = '{datasource}'")

if filters:
    base_query += " WHERE " + " AND ".join(filters)

# Fetch and Display Data
data = run_query(base_query)
if data:
    df = pd.DataFrame(data)
    
    # Display Data Table
    st.subheader("Filtered Data")
    st.dataframe(df)
    
    # Visualizations
    st.subheader("Visualizations")
    chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Map"])
    
    if chart_type == "Bar Chart":
        x_col = st.selectbox("X-Axis", df.columns)
        y_col = st.selectbox("Y-Axis", df.select_dtypes(include=['float64', 'int64']).columns)
        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        st.plotly_chart(fig)
        
    elif chart_type == "Line Chart":
        x_col = st.selectbox("X-Axis", df.columns)
        y_col = st.selectbox("Y-Axis", df.select_dtypes(include=['float64', 'int64']).columns)
        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} Trend by {x_col}")
        st.plotly_chart(fig)
        
    elif chart_type == "Map":
        fig = px.scatter_mapbox(df, 
            lat='latitude', 
            lon='longitude',
            hover_name='locationdesc',
            hover_data=['datavalue'],
            zoom=3,
            mapbox_style="carto-positron")
        st.plotly_chart(fig)
        
    # Export Option
    if st.sidebar.button("Export to CSV"):
        df.to_csv("cdi_data.csv", index=False)
        st.sidebar.success("Data exported successfully!")
else:
    st.warning("No data found for the selected filters.")

# Custom SQL Query Section
st.sidebar.subheader("Custom SQL Query")
custom_query = st.sidebar.text_area("Enter your SQL query:")
if st.sidebar.button("Run Custom Query"):
    if custom_query:
        custom_data = run_query(custom_query)
        if custom_data:
            st.write(pd.DataFrame(custom_data))
        else:
            st.warning("No results found for the custom query.")