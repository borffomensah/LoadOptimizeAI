import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from prophet import Prophet
from prophet.plot import plot_plotly

# Load the trained Prophet model
model = joblib.load("cr_model.pkl")  # Use relative path

# Streamlit app header
st.image("crod.png")  # Use relative path
st.title("Workload Forecasting App")

# Sidebar for forecast period selection
st.sidebar.header("Forecast Settings")

# Sidebar for date range input
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime('2024-11-05'))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime('2024-12-31'))

# Sidebar for frequency selection
forecast_period = st.sidebar.selectbox("Select Forecast Period:", ["Weekly", "Monthly", "Quarterly", "Yearly"])

# Sidebar button to trigger forecast
forecast_button = st.sidebar.button("Forecast")

# Function to make future dataframe based on selected period
def make_future_dataframe(periods, freq):
    future = model.make_future_dataframe(periods=periods, freq=freq)
    return future

# Map frequency selection to corresponding time frequency
freq_map = {
    "Weekly": "W",
    "Monthly": "M",
    "Quarterly": "Q",
    "Yearly": "Y"
}

# Generate the forecast if the button is clicked
if forecast_button:
    # Calculate periods based on the selected forecast period
    if forecast_period == "Weekly":
        periods = (end_date - start_date).days // 7
        future = make_future_dataframe(periods, 'W')
    elif forecast_period == "Monthly":
        periods = (end_date.month - start_date.month) + (end_date.year - start_date.year) * 12
        future = make_future_dataframe(periods, 'M')
    elif forecast_period == "Quarterly":
        periods = (end_date.month - start_date.month) // 3 + (end_date.year - start_date.year) * 4
        future = make_future_dataframe(periods, 'Q')
    elif forecast_period == "Yearly":
        periods = end_date.year - start_date.year
        future = make_future_dataframe(periods, 'Y')

    # Generate the forecast
    forecast = model.predict(future)

    # Rename columns for better readability
    forecast_renamed = forecast.rename(columns={
        'ds': 'DATE',
        'yhat': 'PREDICTED',
        'yhat_lower': 'LOWER VALUE',
        'yhat_upper': 'UPPER VALUE'
    })

    # Filter the forecast to only include the selected date range
    forecast_filtered = forecast_renamed[(forecast_renamed['DATE'] >= pd.to_datetime(start_date)) &
                                         (forecast_renamed['DATE'] <= pd.to_datetime(end_date))]

    # Display forecast plot
    st.subheader(f"{forecast_period} Forecast")
    fig1 = plot_plotly(model, forecast)
    st.plotly_chart(fig1)

    # Display forecast data as a table for the selected date range
    st.subheader(f"{forecast_period} Forecast Data")
    st.write(forecast_filtered[['DATE', 'PREDICTED', 'LOWER VALUE', 'UPPER VALUE']])

else:
    st.write("Please select forecast parameters and click on 'Forecast' to generate the predictions.")
