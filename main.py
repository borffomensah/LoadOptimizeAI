# Data manipulation and visualization
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import joblib
from prophet import Prophet

# Load the trained Prophet model
model = joblib.load("cr_model.pkl")

# Streamlit app header
st.image("crod.png")
st.title("Workload Forecasting App")

# Sidebar for forecast settings
st.sidebar.header("Forecast Settings")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime('2024-11-05'))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime('2024-12-31'))
forecast_period = st.sidebar.selectbox("Select Forecast Period:", ["Weekly", "Monthly", "Quarterly", "Yearly"])
forecast_button = st.sidebar.button("Forecast")

# Frequency mapping with proper offset aliases
freq_map = {
    "Weekly": "W",
    "Monthly": "MS",  # Month start
    "Quarterly": "QS-JAN",  # Quarter start aligned with January
    "Yearly": "YS"  # Year start
}

if forecast_button:
    try:
        # Get the last training date from the model's history
        last_training_date = pd.to_datetime(model.history['ds'].iloc[-1])
        st.write(f"Last training date in model: {last_training_date.date()}")
        
        # Convert start_date and end_date to Timestamps for comparison
        start_date_ts = pd.Timestamp(start_date)
        end_date_ts = pd.Timestamp(end_date)

        # Validate dates
        if start_date_ts >= end_date_ts:
            st.error("End date must be after Start date")
            st.stop()
            
        if end_date_ts <= last_training_date:
            st.error(f"End date must be after last training date ({last_training_date.date()})")
            st.stop()

        # Calculate required periods
        freq = freq_map[forecast_period]
        date_range = pd.date_range(start=last_training_date, end=end_date_ts, freq=freq)
        periods = len(date_range)
        
        if periods <= 0:
            st.error("No periods to forecast. Adjust dates or select a different frequency.")
            st.stop()

        # Generate future dataframe
        future = model.make_future_dataframe(periods=periods, freq=freq, include_history=False)
        forecast = model.predict(future)

        # Filter to selected date range
        forecast_filtered = forecast[
            (forecast['ds'] >= start_date_ts) &
            (forecast['ds'] <= end_date_ts)
        ].rename(columns={
            'ds': 'DATE',
            'yhat': 'PREDICTED',
            'yhat_lower': 'LOWER VALUE',
            'yhat_upper': 'UPPER VALUE'
        })

        # Check if filtered forecast is empty
        if forecast_filtered.empty:
            st.error("No data in selected date range. Adjust dates or check frequency.")
            st.stop()

        # Display results
        st.subheader(f"{forecast_period} Forecast")
        
        # Plotting
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=forecast['ds'], 
            y=forecast['yhat'], 
            name='Predicted',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
            y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(0,0,255,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Uncertainty'
        ))
        fig.update_layout(
            title=f"{forecast_period} Forecast",
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode='x unified'
        )
        st.plotly_chart(fig)

        st.subheader("Forecast Data")
        st.dataframe(forecast_filtered[['DATE', 'PREDICTED', 'LOWER VALUE', 'UPPER VALUE']])

    except Exception as e:
        st.error(f"Critical error: {str(e)}")
        st.write("Troubleshooting Checklist:")
        st.write("1. Ensure model file (cr_model.pkl) exists and is a valid Prophet model")
        st.write("2. Verify selected dates are after the last training date")
        st.write("3. Check frequency alignment (monthly forecasts need month-start dates)")
        st.write("4. Confirm the date range contains forecastable periods")
        st.write(f"Last training date: {last_training_date if 'last_training_date' in locals() else 'Unknown'}")