import serial
import pandas as pd
import joblib
import time
from collections import deque
import numpy as np

# ========== CONFIG ========== #
PORT = 'COM10'  # Replace with your actual ESP32 COM port
BAUD = 115200
MODEL_PATH = 'sustained_tremor_model.pkl'
WINDOW_SIZE = 50
MOTION_THRESHOLD = 100
TREMOR_THRESHOLD = 3
# ============================ #

model = joblib.load(MODEL_PATH)
ser = serial.Serial(PORT, BAUD, timeout=2)
time.sleep(2)
print(f" Connected to {PORT}")

buffer = deque(maxlen=WINDOW_SIZE)
tremor_streak = 0
previous_output = -1

def extract_features(window_df):
    features = {}
    for col in ['aX', 'aY', 'aZ', 'gX', 'gY', 'gZ']:
        data = window_df[col].astype(float)
        features[f'{col}_std'] = data.std()
        features[f'{col}_zcr'] = ((data * data.shift(1)) < 0).sum()
        features[f'{col}_ptp'] = data.max() - data.min()
        features[f'{col}_rms'] = np.sqrt(np.mean(data ** 2))
    return pd.DataFrame([features])

while True:
    try:
        line = ser.readline().decode().strip()
        if not line or ',' not in line:
            continue

        values = list(map(int, line.split(',')))
        if len(values) != 6:
            continue

        buffer.append(values)

        if len(buffer) == WINDOW_SIZE:
            df_window = pd.DataFrame(buffer, columns=['aX', 'aY', 'aZ', 'gX', 'gY', 'gZ'])
            gyro_mag = np.sqrt((df_window[['gX', 'gY', 'gZ']]**2).sum(axis=1)).mean()

            if gyro_mag < MOTION_THRESHOLD:
                tremor_streak = 0
                output = 0
                print(" Low motion — skipping.")
            else:
                feature_df = extract_features(df_window)
                prediction = model.predict(feature_df)[0]

                if prediction == 1:
                    tremor_streak += 1
                else:
                    tremor_streak = 0

                output = 1 if tremor_streak >= TREMOR_THRESHOLD else 0
                print(f" Prediction: {prediction} | Streak: {tremor_streak} → Output: {output}")

            if output != previous_output:
                ser.write(f"{output}".encode())  # Send clean single digit
                previous_output = output

            buffer.clear()

    except Exception as e:
        print(" Error:", e)