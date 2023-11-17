from sklearn.metrics import mean_squared_error
import os
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from streamlit_gsheets import GSheetsConnection
from sklearn.model_selection import train_test_split
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.models import Sequential, load_model, save_model


st.set_page_config(page_title="Model Forecasting", page_icon="🤖")
st.sidebar.header("Model Forecasting")
st.title("Model Forecasting")
st.write(
    """"""
)

conn = st.connection("gsheets", type=GSheetsConnection)
scaler = MinMaxScaler()


def read_data():
    st.cache_data.clear()
    df = conn.read(worksheet="AfterPreprocessing")
    df = df[['timestamp', 'ketinggian']]
    df = df.dropna(how='all')
    return df


df = read_data()
st.dataframe(df)


def get_last_timestamp(df):
    last_timestamp = df['timestamp'].iloc[-1]
    return last_timestamp


def get_first_timestamp(df):
    first_timestamp = df['timestamp'].iloc[0]
    return first_timestamp


def normalize_column(df, column_name='ketinggian'):
    df[column_name] = scaler.fit_transform(df[[column_name]])
    return df


def prepare_data_model(df, test_size, sequence_length):
    df.set_index('timestamp', inplace=True)
    train_data, test_data = train_test_split(
        df, test_size=test_size, shuffle=False)

    X_train, y_train = [], []
    X_test, y_test = [], []

    for i in range(len(train_data) - sequence_length):
        X_train.append(train_data.iloc[i:i+sequence_length].values)
        y_train.append(train_data.iloc[i+sequence_length].values)

    for i in range(len(test_data) - sequence_length):
        X_test.append(test_data.iloc[i:i+sequence_length].values)
        y_test.append(test_data.iloc[i+sequence_length].values)

    X_train, y_train = np.array(X_train), np.array(y_train)
    X_test, y_test = np.array(X_test), np.array(y_test)

    return X_train, y_train, X_test, y_test, test_data


def build_lstm_model(sequence_length=24):
    model = Sequential()
    model.add(LSTM(64, activation='relu', return_sequences=True,
              input_shape=(sequence_length, 1)))
    model.add(LSTM(64, activation='relu'))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model


def train_lstm_model(model, X_train, y_train, X_test, y_test, epochs=10, batch_size=32):
    history = model.fit(X_train, y_train, epochs=epochs,
                        batch_size=batch_size, verbose=2, validation_data=(X_test, y_test))
    return model, history


def evaluate_model(model, X_test, y_test):
    mse = model.evaluate(X_test, y_test, verbose=0)
    return mse


def prepare_data_model_data(df, test_size, sequence_length):

    # Pemisahan data menjadi train dan test
    train_data, test_data = train_test_split(
        df, test_size=test_size, shuffle=False)

    X_train, y_train = [], []
    X_test, y_test = [], []

    for i in range(len(train_data) - sequence_length):
        X_train.append(train_data.iloc[i:i+sequence_length+1].values)
        y_train.append(train_data.iloc[i+sequence_length].values)

    for i in range(len(test_data) - sequence_length):
        X_test.append(test_data.iloc[i:i+sequence_length+1].values)
        y_test.append(test_data.iloc[i+sequence_length].values)

    X_train, y_train = np.array(X_train), np.array(y_train)
    X_test, y_test = np.array(X_test), np.array(y_test)

    return X_train, y_train, X_test, y_test, test_data


df_norm = normalize_column(df, 'ketinggian')
X_train, y_train, X_test, y_test, test_data = prepare_data_model(
    df_norm, test_size=0.1, sequence_length=24)

df_data = read_data()
X_train_data, y_train_data, X_test_data, y_test_data, test_data_data = prepare_data_model_data(
    df_data, test_size=0.1, sequence_length=24)
# Menampilkan data train dan test pada Streamlit
st.title("Data Train")
train = pd.DataFrame(
    X_train_data.reshape(-1, X_train_data.shape[-1]), columns=df_data.columns)
first_timestamp = get_first_timestamp(train)
last_timestamp = get_last_timestamp(train)
st.markdown(
    f"Data Train ini mencakup periode waktu dari **{first_timestamp}** hingga **{last_timestamp}**.")
st.write("Jumlah data train:", len(train))
st.title("Data Test")
test = pd.DataFrame(
    X_test_data.reshape(-1, X_test_data.shape[-1]), columns=df_data.columns)
first_timestamp = get_first_timestamp(test)
last_timestamp = get_last_timestamp(test)
st.markdown(
    f"Data Test ini mencakup periode waktu dari **{first_timestamp}** hingga **{last_timestamp}**.")
st.write("Jumlah data test:", len(test))


# Bangun model LSTM
lstm_model = build_lstm_model(sequence_length=24)

# Latih model LSTM
model, history = train_lstm_model(
    lstm_model, X_train, y_train, X_test, y_test, epochs=100, batch_size=32)

st.title("Plot Loss")
fig_loss = px.line(history.history, x=history.epoch, y=[
                   'loss', 'val_loss'], labels={'index': 'Epoch', 'value': 'Loss'})
st.plotly_chart(fig_loss)

# val_loss = history.history['val_loss'][-1]
# st.write(f'Nilai evaluasi menggunakan MSE yaitu: {val_loss}')

forecast = model.predict(X_test)
forecast = scaler.inverse_transform(forecast)
y_test_ori = scaler.inverse_transform(y_test)

mse = mean_squared_error(y_test_ori, forecast)
st.write(f'Mean Squared Error on Test Data: {mse}')
rmse = np.sqrt(mse)
st.write(f'Root Mean Squared Error on Test Data: {rmse}')

# Plot hasil prediksi dan data asli
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(test_data.index[24:], y_test_ori, label='Actual Data', color='blue')
ax.plot(test_data.index[24:], forecast, label='Predicted Data', color='red')
ax.set_xlabel('Timestamp')
ax.set_ylabel('Ketinggian')
ax.set_title('Actual vs. Predicted Data')
ax.legend()

# Tampilkan grafik di Streamlit
st.pyplot(fig)


if st.button('Simpan Model'):
    save_model(model, 'model.h5')

num_predictions = 6
current_data = X_test[-1].tolist()


def make_predictions(model, current_data, num_predictions, scaler):
    predictions = []

    for _ in range(num_predictions):
        current_data_reshaped = np.array(current_data).reshape((1, 24, 1))
        next_prediction = model.predict(current_data_reshaped)
        next_prediction_original_scale = scaler.inverse_transform(
            next_prediction)
        predictions.append(next_prediction_original_scale[0, 0])
        current_data = np.roll(current_data, -1)
        current_data[-1] = next_prediction[0, 0]

    return predictions


def plot_predictions(predictions_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=predictions_df['timestamp'], y=predictions_df['ketinggian'],
                             mode='lines', name='Predicted Data', line=dict(color='red')))
    fig.update_layout(title='Predicted Data',
                      xaxis_title='Timestamp', yaxis_title='Ketinggian')
    st.plotly_chart(fig)


st.markdown('### **Forecasting TMA Manggarai 6 Jam Kedepan**')
# Lakukan prediksi
predictions = make_predictions(
    model, current_data, num_predictions=num_predictions, scaler=scaler)

# Buat DataFrame untuk menampilkan hasil prediksi
pred_df = pd.DataFrame({
    'timestamp': pd.date_range(start=test_data.index[-1], periods=num_predictions + 1, freq='H')[1:],
    'ketinggian': predictions
})

pred_df['ketinggian'] = pred_df['ketinggian'].astype(int)
pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
pred_df['timestamp'] = pred_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')

# Tampilkan hasil prediksi
plot_predictions(pred_df)

# PrediksiOnly
update_df = conn.update(worksheet="PrediksiOnly", data=pred_df)
st.success("Berhasil Update Data Hasil Prediksi")

# TotalPrediksi
df = conn.read(worksheet="AfterPreprocessing")
df = df[['timestamp', 'ketinggian']]
df = df.dropna(how='all')
update_df = pd.concat([df, pred_df], ignore_index=True)
update_df = conn.update(worksheet="TotalPrediksi", data=update_df)
st.success("Berhasil Update Data Total + Hasil Prediksi")

if st.button('Generate Predictions'):
    # Lakukan prediksi
    predictions = make_predictions(
        model, current_data, num_predictions=num_predictions, scaler=scaler)

    # Buat DataFrame untuk menampilkan hasil prediksi
    pred_df = pd.DataFrame({
        'timestamp': pd.date_range(start=test_data.index[-1], periods=num_predictions + 1, freq='H')[1:],
        'ketinggian': predictions
    })

    pred_df['ketinggian'] = pred_df['ketinggian'].astype(int)
    pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
    pred_df['timestamp'] = pred_df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')

    # Tampilkan hasil prediksi
    plot_predictions(pred_df)

    # PrediksiOnly
    update_df = conn.update(worksheet="PrediksiOnly", data=pred_df)
    st.success("Berhasil Update Data Hasil Prediksi")

    # TotalPrediksi
    df = conn.read(worksheet="AfterPreprocessing")
    df = df[['timestamp', 'ketinggian']]
    df = df.dropna(how='all')
    update_df = pd.concat([df, pred_df], ignore_index=True)
    update_df = conn.update(worksheet="TotalPrediksi", data=update_df)
    st.success("Berhasil Update Data Total + Hasil Prediksi")

    if st.button('Simpan Data Hasil Prediksi'):
        update_df = conn.update(worksheet="PrediksiOnly", data=pred_df)
        st.success("Berhasil Update Data Hasil Prediksi")

    if st.button('Simpan Data Total + Hasil Prediksi'):
        df = conn.read(worksheet="AfterPreprocessing")
        df = df[['timestamp', 'ketinggian']]
        df = df.dropna(how='all')
        update_df = pd.concat([df, pred_df], ignore_index=True)
        update_df = conn.update(worksheet="TotalPrediksi", data=update_df)
        st.success("Berhasil Update Data Total + Hasil Prediksi")
