import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

# Connect to PostgreSQL Database
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="cdii",
        user="postgres",
        password="8300"
    )

# Fetch Data from Database
def run_query(query):
    try:
        # Establish a new connection each time
        conn = psycopg2.connect(
            dbname="cdii",
            user="postgres",
            password="8300",
            host="localhost",
            port="5432"
        )
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            columns = [desc[0] for desc in cur.description]  # Extract column names
        conn.close()  # Close the connection after use
        return [dict(zip(columns, row)) for row in results]  # Return as list of dictionaries
    except Exception as e:
        print(f"Error executing query: {e}")
        return []
    
# Streamlit App Layout
st.title("U.S. Chronic Disease Indicators (CDI) Explorer")
st.sidebar.header("Filter Options")


# Sidebar Filters
# Example for fetching distinct years
year_data = run_query("SELECT DISTINCT Year FROM Year")
# print('-----X--------', year_data)
if not year_data:
    st.sidebar.warning("No year data found.")
    year = st.sidebar.selectbox("Select Year", options=["All"])
else:
    year = st.sidebar.selectbox("Select Year", options=["All"] + [row["year"] for row in year_data])

# Example for fetching distinct locations
location_data = run_query("SELECT DISTINCT LocationDesc FROM Location")
# print('-----X--------', location_data)

if not location_data:
    st.sidebar.warning("No location data found.")
    location = st.sidebar.selectbox("Select Location", options=["All"])
else:
    location = st.sidebar.selectbox("Select Location", options=["All"] + [row["locationdesc"] for row in location_data])


topic_data = run_query("SELECT DISTINCT Topic FROM Topic")  # Fetch topics
# print('-----X--------', topic_data)
topic = st.sidebar.selectbox("Select Topic", options=["All"] + [row["topic"] for row in topic_data])

# Query Filters
filters = []
if year != "All":
    filters.append(f"Year.Year = '{year}'")
if location != "All":
    filters.append(f"Location.LocationDesc = '{location}'")
if topic != "All":
    filters.append(f"Topic.Topic = '{topic}'")
filter_query = " AND ".join(filters)

# Fetch Filtered Data
base_query = """
    SELECT Year.Year, Location.LocationDesc, Topic.Topic, Question.Question, DataValue.DataValue, DataValue.DataValueUnit
    FROM DataValue
    JOIN Year ON DataValue.YearID = Year.YearID
    JOIN Location ON DataValue.LocationID = Location.LocationID
    JOIN Question ON DataValue.QuestionID = Question.QuestionID
    JOIN Topic ON Question.TopicID = Topic.TopicID
"""
if filters:
    base_query += " WHERE " + filter_query

data = run_query(base_query)

if data:  # If data is not empty
    data = pd.DataFrame(data)
else:
    st.warning("No data found for the selected filters.")
    data = pd.DataFrame()  # Create an empty DataFrame
    
# Display Data Table
st.subheader("Filtered Data")
st.dataframe(data)

# Visualization Options
# Visualization Options
st.subheader("Visualizations")
if not data.empty:  # Check if the DataFrame is not empty
    chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Map"])

    if chart_type == "Bar Chart":
        bar_x = st.selectbox("X-Axis", data.columns)
        bar_y = st.selectbox("Y-Axis", data.columns)
        st.plotly_chart(px.bar(data, x=bar_x, y=bar_y, title="Bar Chart"))

    elif chart_type == "Line Chart":
        line_x = st.selectbox("X-Axis", data.columns)
        line_y = st.selectbox("Y-Axis", data.columns)
        st.plotly_chart(px.line(data, x=line_x, y=line_y, title="Line Chart"))

    elif chart_type == "Map":
        if "Latitude" in data.columns and "Longitude" in data.columns:
            st.map(data[["Latitude", "Longitude"]].dropna())
        else:
            st.warning("Latitude and Longitude data are not available.")
else:
    st.warning("No data available for visualization.")
    
# Export Filtered Data
st.sidebar.subheader("Export Options")
if st.sidebar.button("Export Data to CSV"):
    data.to_csv("filtered_data.csv", index=False)
    st.sidebar.success("Data exported successfully!")

# Custom SQL Query
st.sidebar.subheader("Custom SQL Query")
custom_query = st.sidebar.text_area("Enter your SQL query:")
if st.sidebar.button("Run Query"):
    try:
        custom_data = run_query(custom_query)
        st.write(custom_data)
    except Exception as e:
        st.error(f"Error: {e}")
