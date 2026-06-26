import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

from dotenv import load_dotenv
import os

# CONFIG — PASTE YOUR API KEY HERE

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"


# PAGE SETUP

st.set_page_config(
    page_title="🌤️ Real-Time Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f, #2d6a9f);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin: 5px;
    }
    .alert-box {
        background-color: #ff4b4b22;
        border-left: 4px solid #ff4b4b;
        padding: 10px 15px;
        border-radius: 5px;
        color: #ff4b4b;
        margin: 5px 0;
    }
    .success-box {
        background-color: #00c85322;
        border-left: 4px solid #00c853;
        padding: 10px 15px;
        border-radius: 5px;
        color: #00c853;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)


# API FUNCTIONS

def get_current_weather(city):
    """Fetch current weather for a city."""
    url = f"{BASE_URL}/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            return None, f"City '{city}' not found. Check spelling."
        elif response.status_code == 401:
            return None, "Invalid API Key. Check your key in the code."
        else:
            return None, f"API Error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "No internet connection."
    except Exception as e:
        return None, str(e)


def get_forecast(city):
    """Fetch 5-day / 3-hour forecast."""
    url = f"{BASE_URL}/forecast"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Forecast error: {response.status_code}"
    except Exception as e:
        return None, str(e)


def parse_forecast(data):
    """Convert forecast JSON into a clean DataFrame."""
    rows = []
    for item in data["list"]:
        rows.append({
            "DateTime"   : datetime.fromtimestamp(item["dt"]),
            "Temp"       : item["main"]["temp"],
            "Feels Like" : item["main"]["feels_like"],
            "Humidity"   : item["main"]["humidity"],
            "Wind Speed" : item["wind"]["speed"],
            "Description": item["weather"][0]["description"].title(),
            "Icon"       : item["weather"][0]["icon"]
        })
    return pd.DataFrame(rows)


def weather_emoji(description):
    desc = description.lower()
    if "clear" in desc:      return "☀️"
    if "cloud" in desc:      return "☁️"
    if "rain" in desc:       return "🌧️"
    if "storm" in desc:      return "⛈️"
    if "snow" in desc:       return "❄️"
    if "mist" in desc or "fog" in desc: return "🌫️"
    return "🌤️"


# SIDEBAR

st.sidebar.title("⚙️ Dashboard Settings")
st.sidebar.markdown("---")

# City input
city_input = st.sidebar.text_input(
    "🏙️ Enter City Name",
    value="Ahmedabad",
    placeholder="e.g. Delhi, London, New York"
)

# Multiple cities compare
st.sidebar.markdown("### 🌍 Compare Cities")
compare_cities = st.sidebar.text_input(
    "Add cities (comma separated)",
    value="Delhi, Ahmedabad, Mumbai",
    placeholder="Delhi, Bangalore, Chennai"
)

st.sidebar.markdown("---")

# Auto-refresh
st.sidebar.markdown("### 🔄 Auto Refresh")
auto_refresh = st.sidebar.toggle("Enable Auto Refresh", value=False)
refresh_interval = st.sidebar.slider(
    "Refresh every (seconds)", 30, 300, 60, step=30
)

st.sidebar.markdown("---")

# Alerts
st.sidebar.markdown("### 🚨 Weather Alerts")
temp_alert_high = st.sidebar.number_input("🌡️ High Temp Alert (°C)", value=40)
temp_alert_low  = st.sidebar.number_input("🥶 Low Temp Alert (°C)",  value=10)
wind_alert      = st.sidebar.number_input("💨 Wind Alert (m/s)",      value=10)
humidity_alert  = st.sidebar.number_input("💧 Humidity Alert (%)",    value=80)

st.sidebar.markdown("---")
st.sidebar.markdown("Built with using Streamlit")


# MAIN DASHBOARD

st.title("🌤️ Real-Time Weather Analytics Dashboard")
st.markdown(f"*Last updated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}*")
st.markdown("---")

# Fetch current weather
weather_data, error = get_current_weather(city_input)

if error:
    st.error(f"❌ {error}")
    st.stop()

# Extract values
temp        = weather_data["main"]["temp"]
feels_like  = weather_data["main"]["feels_like"]
humidity    = weather_data["main"]["humidity"]
pressure    = weather_data["main"]["pressure"]
wind_speed  = weather_data["wind"]["speed"]
visibility  = weather_data.get("visibility", 0) / 1000
description = weather_data["weather"][0]["description"].title()
city_name   = weather_data["name"]
country     = weather_data["sys"]["country"]
sunrise     = datetime.fromtimestamp(weather_data["sys"]["sunrise"]).strftime("%I:%M %p")
sunset      = datetime.fromtimestamp(weather_data["sys"]["sunset"]).strftime("%I:%M %p")
emoji       = weather_emoji(description)


# ALERTS SECTION

alerts = []
if temp >= temp_alert_high:
    alerts.append(f"🌡️ HIGH TEMP ALERT! Temperature is {temp}°C (threshold: {temp_alert_high}°C)")
if temp <= temp_alert_low:
    alerts.append(f"🥶 LOW TEMP ALERT! Temperature is {temp}°C (threshold: {temp_alert_low}°C)")
if wind_speed >= wind_alert:
    alerts.append(f"💨 HIGH WIND ALERT! Wind speed is {wind_speed} m/s (threshold: {wind_alert} m/s)")
if humidity >= humidity_alert:
    alerts.append(f"💧 HIGH HUMIDITY ALERT! Humidity is {humidity}% (threshold: {humidity_alert}%)")

if alerts:
    for alert in alerts:
        st.markdown(f'<div class="alert-box">⚠️ {alert}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="success-box">✅ All weather conditions are normal!</div>',
                unsafe_allow_html=True)

st.markdown("---")


# CURRENT WEATHER — KPI CARDS

st.subheader(f"{emoji} Current Weather — {city_name}, {country}")
st.markdown(f"**{description}**")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("🌡️ Temperature", f"{temp}°C", f"Feels {feels_like}°C")
with col2:
    st.metric("💧 Humidity", f"{humidity}%")
with col3:
    st.metric("💨 Wind Speed", f"{wind_speed} m/s")
with col4:
    st.metric("🔵 Pressure", f"{pressure} hPa")
with col5:
    st.metric("👁️ Visibility", f"{visibility:.1f} km")
with col6:
    st.metric("🌅 Sunrise / 🌇 Sunset", sunrise, sunset)

st.markdown("---")


# FORECAST CHARTS

forecast_data, forecast_error = get_forecast(city_input)

if forecast_data:
    df = parse_forecast(forecast_data)

    # Row 1: Temperature + Humidity
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🌡️ Temperature Forecast (5 Days)")
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=df["DateTime"], y=df["Temp"],
            mode="lines+markers",
            name="Temperature",
            line=dict(color="#FF6B6B", width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(255,107,107,0.1)",
            hovertemplate="<b>%{x|%d %b %I:%M %p}</b><br>Temp: %{y:.1f}°C<extra></extra>"
        ))
        fig_temp.add_trace(go.Scatter(
            x=df["DateTime"], y=df["Feels Like"],
            mode="lines",
            name="Feels Like",
            line=dict(color="#FFB347", width=1.5, dash="dash"),
            hovertemplate="<b>%{x|%d %b %I:%M %p}</b><br>Feels: %{y:.1f}°C<extra></extra>"
        ))
        # Threshold lines
        fig_temp.add_hline(y=temp_alert_high, line_dash="dot",
                        line_color="red", annotation_text=f"High Alert {temp_alert_high}°C")
        fig_temp.add_hline(y=temp_alert_low, line_dash="dot",
                        line_color="blue", annotation_text=f"Low Alert {temp_alert_low}°C")
        fig_temp.update_layout(
            height=350, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="white"), legend=dict(orientation="h"),
            xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333", title="°C")
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with col_b:
        st.subheader("💧 Humidity Forecast (5 Days)")
        fig_hum = go.Figure()
        fig_hum.add_trace(go.Bar(
            x=df["DateTime"], y=df["Humidity"],
            name="Humidity",
            marker_color=[
                "#FF4B4B" if h >= humidity_alert else "#4ECDC4"
                for h in df["Humidity"]
            ],
            hovertemplate="<b>%{x|%d %b %I:%M %p}</b><br>Humidity: %{y}%<extra></extra>"
        ))
        fig_hum.add_hline(y=humidity_alert, line_dash="dot",
                        line_color="red", annotation_text=f"Alert {humidity_alert}%")
        fig_hum.update_layout(
            height=350, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="white"),
            xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333", title="%")
        )
        st.plotly_chart(fig_hum, use_container_width=True)

    # Row 2: Wind Speed + Weather Distribution
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("💨 Wind Speed Forecast (5 Days)")
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(
            x=df["DateTime"], y=df["Wind Speed"],
            mode="lines+markers",
            name="Wind Speed",
            line=dict(color="#A8EDEA", width=2.5),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(168,237,234,0.1)",
            hovertemplate="<b>%{x|%d %b %I:%M %p}</b><br>Wind: %{y:.1f} m/s<extra></extra>"
        ))
        fig_wind.add_hline(y=wind_alert, line_dash="dot",
                        line_color="orange", annotation_text=f"Alert {wind_alert} m/s")
        fig_wind.update_layout(
            height=350, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="white"),
            xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333", title="m/s")
        )
        st.plotly_chart(fig_wind, use_container_width=True)

    with col_d:
        st.subheader("🌥️ Weather Condition Distribution")
        condition_counts = df["Description"].value_counts().reset_index()
        condition_counts.columns = ["Condition", "Count"]
        fig_pie = px.pie(
            condition_counts, names="Condition", values="Count",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4
        )
        fig_pie.update_layout(
            height=350, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="white"), legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Raw forecast table
    with st.expander("📋 View Raw Forecast Data"):
        st.dataframe(
            df[["DateTime", "Temp", "Feels Like", "Humidity", "Wind Speed", "Description"]]
            .rename(columns={
                "DateTime"  : "Date & Time",
                "Temp"      : "Temp (°C)",
                "Feels Like": "Feels Like (°C)",
                "Humidity"  : "Humidity (%)",
                "Wind Speed": "Wind (m/s)"
            }),
            use_container_width=True, height=300
        )

st.markdown("---")

# MULTI-CITY COMPARISON

st.subheader("🌍 Multi-City Weather Comparison")

cities = [c.strip() for c in compare_cities.split(",") if c.strip()]
city_records = []

for city in cities:
    data, err = get_current_weather(city)
    if data:
        city_records.append({
            "City"      : data["name"],
            "Country"   : data["sys"]["country"],
            "Temp (°C)" : data["main"]["temp"],
            "Humidity %": data["main"]["humidity"],
            "Wind (m/s)": data["wind"]["speed"],
            "Condition" : data["weather"][0]["description"].title()
        })

if city_records:
    df_cities = pd.DataFrame(city_records)
    st.dataframe(df_cities, use_container_width=True)

    col_e, col_f = st.columns(2)
    with col_e:
        fig_cmp_temp = px.bar(
            df_cities, x="City", y="Temp (°C)",
            color="Temp (°C)", color_continuous_scale="RdYlBu_r",
            title="Temperature Comparison",
            text="Temp (°C)"
        )
        fig_cmp_temp.update_traces(texttemplate="%{text:.1f}°C", textposition="outside")
        fig_cmp_temp.update_layout(
            height=350, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="white"), showlegend=False
        )
        st.plotly_chart(fig_cmp_temp, use_container_width=True)

    with col_f:
        fig_cmp_hum = px.bar(
            df_cities, x="City", y="Humidity %",
            color="Humidity %", color_continuous_scale="Blues",
            title="Humidity Comparison",
            text="Humidity %"
        )
        fig_cmp_hum.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_cmp_hum.update_layout(
            height=350, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font=dict(color="white"), showlegend=False
        )
        st.plotly_chart(fig_cmp_hum, use_container_width=True)


# AUTO REFRESH

if auto_refresh:
    st.markdown("---")
    st.info(f"🔄 Dashboard will auto-refresh every {refresh_interval} seconds...")
    countdown = st.empty()
    for i in range(refresh_interval, 0, -1):
        countdown.markdown(f"⏱️ Refreshing in **{i}** seconds...")
        time.sleep(1)
    st.rerun()
