
import requests
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

BASE_URL = "https://aave-api-v2.aave.com"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Save the model to file
import os

# Save the model to file
def save_model(model, filename):
    try:
        joblib.dump(model, filename)
        print(f"Model saved as {filename} at {os.path.abspath(filename)}")
    except Exception as e:
        print(f"Error saving model: {e}")

# Flatten nested dictionary for easier CSV storage
def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# Preprocess Aave daily volume data for ML model
def preprocess_data(data):
    processed_data = []
    for item in data.get('reserves', {}).get('v2', []):
        flat_item = flatten_dict(item)
        try:
            deposit = float(flat_item.get('deposit', 0))
            borrow = float(flat_item.get('borrow', 0))
            estimated_apy = ((borrow - deposit) / deposit) * 100 if deposit != 0 else 0
            flat_item['estimated_apy'] = estimated_apy
        except:
            flat_item['estimated_apy'] = 0
        processed_data.append(flat_item)
    df = pd.DataFrame(processed_data)
    columns = ['priceInEth', 'borrow', 'deposit', 'repay', 'withdrawal', 'symbol', 'estimated_apy']
    df = df[columns].dropna()
    encoder = OneHotEncoder()
    encoded_symbols = encoder.fit_transform(df[['symbol']]).toarray()
    encoded_df = pd.DataFrame(encoded_symbols, columns=encoder.get_feature_names_out(['symbol']))
    df = pd.concat([df.drop(columns=['symbol']), encoded_df], axis=1)
    return df

# Train the model to predict APY
def train_apy_model(df):
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    X = numeric_df.drop(columns=['estimated_apy'])
    y = numeric_df['estimated_apy']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    model = RandomForestRegressor(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Mean Squared Error: {mse}")
    save_model(model, "apy_model.pkl")

# Get Aave Daily Volume Data and preprocess it
def get_daily_volume_data():
    url = f"{BASE_URL}/data/daily-volume-24-hours"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            print("Aave Daily Volume Data fetched successfully.")
            df = preprocess_data(data)
            train_apy_model(df)
        else:
            print(f"Error fetching Daily Volume Data: {response.status_code}")
            print(f"Details: {response.text}")
    except Exception as e:
        print(f"Failed to fetch Daily Volume Data: {e}")

# Run the training process
get_daily_volume_data()
