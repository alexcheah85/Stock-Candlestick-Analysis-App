import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objs as go
import streamlit as st

# Function to detect basic candlestick patterns
def detect_candlestick_patterns(df):
    if not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        st.write('Missing necessary columns in the data.')
        return df

    # Ensure the columns are of numeric type
    df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].apply(pd.to_numeric, errors='coerce')
    df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)

    df = df.copy()
    df['Body'] = abs(df['Close'] - df['Open'])
    df['Upper_Shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['Lower_Shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    df['Pattern'] = 'None'

    # Doji
    doji_condition = (df['Body'] <= 0.1 * (df['High'] - df['Low'])) & (df['Upper_Shadow'] > 0) & (df['Lower_Shadow'] > 0)
    df.loc[doji_condition, 'Pattern'] = 'Doji'

    # Hammer
    hammer_condition = (df['Body'] <= 0.3 * (df['High'] - df['Low'])) & (df['Lower_Shadow'] > 2 * df['Body']) & (df['Upper_Shadow'] < df['Body'])
    df.loc[hammer_condition, 'Pattern'] = 'Hammer'

    # Bullish Engulfing
    bullish_engulfing_condition = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'].shift(1)) & (df['Open'] < df['Close'].shift(1))
    df.loc[bullish_engulfing_condition, 'Pattern'] = 'Bullish_Engulfing'

    # Bearish Engulfing
    bearish_engulfing_condition = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open'].shift(1)) & (df['Open'] > df['Close'].shift(1))
    df.loc[bearish_engulfing_condition, 'Pattern'] = 'Bearish_Engulfing'

    return df


def predict_movement(df):
    pattern_counts = df['Pattern'].value_counts()
    total_patterns = pattern_counts.sum()

    if total_patterns == 0:
        return {'Up': 0, 'Down': 0, 'Neutral': 0}

    # Calculate probabilities
    probabilities = {
        'Up': (pattern_counts.get('Bullish_Engulfing', 0) + pattern_counts.get('Hammer', 0)) / total_patterns * 100,
        'Down': pattern_counts.get('Bearish_Engulfing', 0) / total_patterns * 100,
        'Neutral': pattern_counts.get('Doji', 0) / total_patterns * 100
    }

    return probabilities


st.title('Stock Candlestick Analysis App')

# User Input
stock_symbol = st.text_input('Enter Stock Symbol (e.g., AAPL, TSLA):', 'AAPL')
start_date = st.date_input('Start Date', pd.to_datetime('2023-01-01'))
end_date = st.date_input('End Date', pd.to_datetime('2025-03-22'))

if st.button('Analyze Stock'):
    # Fetch stock data
    df = yf.download(stock_symbol, start=start_date, end=end_date)

    if not df.empty:
        df = detect_candlestick_patterns(df)
        probabilities = predict_movement(df)

        # Display Probability Results
        st.write(f"### Prediction Probabilities for {stock_symbol}")
        st.write(f"Up: {probabilities['Up']:.2f}%")
        st.write(f"Down: {probabilities['Down']:.2f}%")
        st.write(f"Neutral: {probabilities['Neutral']:.2f}%")

        # Plot Candlestick Chart
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                                             open=df['Open'], high=df['High'],
                                             low=df['Low'], close=df['Close'])])
        fig.update_layout(title=f'{stock_symbol} Candlestick Chart', xaxis_title='Date', yaxis_title='Price')
        st.plotly_chart(fig)

        # Download Process
        csv = df.to_csv(index=True)
        st.download_button(label="Download Analyzed Data as CSV", data=csv, file_name=f'{stock_symbol}_analyzed_data.csv', mime='text/csv')
    else:
        st.write('No data found. Please try a different stock symbol or date range.')
