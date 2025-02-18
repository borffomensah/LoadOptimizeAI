# Data manipulation and visualization
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import joblib

# Load the trained Prophet model
model = joblib.load("cr_model.pkl")

# Streamlit app header
st.image("crod.png")
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
    try:
        # Calculate periods based on the selected forecast period
        if forecast_period == "Weekly":
            periods = (end_date - start_date).days // 7
            freq = 'W'
        elif forecast_period == "Monthly":
            periods = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            freq = 'M'
        elif forecast_period == "Quarterly":
            periods = (end_date.year - start_date.year) * 4 + (end_date.month - start_date.month) // 3
            freq = 'Q'
        elif forecast_period == "Yearly":
            periods = end_date.year - start_date.year
            freq = 'Y'

        # Handle cases where periods are zero or negative
        if periods <= 0:
            st.error("The selected date range does not allow for a valid forecast. Please adjust the dates.")
            st.stop()

        # Generate future dataframe
        future = make_future_dataframe(periods, freq)

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
        forecast_filtered = forecast_renamed[
            (forecast_renamed['DATE'] >= pd.to_datetime(start_date)) &
            (forecast_renamed['DATE'] <= pd.to_datetime(end_date))
        ]

        # Display forecast plot
        st.subheader(f"{forecast_period} Forecast")
        
        # Create custom Plotly figure instead of using plot_plotly
        fig = go.Figure()
        
        # Add predicted line
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat'],
            name='Predicted',
            line=dict(color='blue')
        ))
        
        # Add uncertainty interval
        fig.add_trace(go.Scatter(
            x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
            y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(0,0,255,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Uncertainty Interval'
        ))

        # Update layout
        fig.update_layout(
            title=f"{forecast_period} Forecast",
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode='x unified',
            showlegend=True
        )

        # Display the plot
        st.plotly_chart(fig)

        # Display forecast data as a table for the selected date range
        st.subheader(f"{forecast_period} Forecast Data")
        st.write(forecast_filtered[['DATE', 'PREDICTED', 'LOWER VALUE', 'UPPER VALUE']])

    except Exception as e:
        st.error(f"An error occurred while generating the forecast: {e}")
        
        # Fallback to matplotlib if Plotly fails
        st.subheader("Fallback Visualization")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(forecast['ds'], forecast['yhat'], label='Predicted', color='blue')
        ax.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='blue', alpha=0.2)
        ax.set_title(f"{forecast_period} Forecast")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.legend()
        st.pyplot(fig)
else:
    st.write("Please select forecast parameters and click on 'Forecast' to generate the predictions.")