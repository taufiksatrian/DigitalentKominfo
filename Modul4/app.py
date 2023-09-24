import joblib
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score


st.title("Aplikasi Prediksi Telco Churn Prevention")

uploaded_file = st.file_uploader(
    "Unggah file CSV dengan data baru:", type=["csv"])

rfc = joblib.load('Modul4/random_forest_model.pkl')


def preprocess_data(data):
    normalisasi = MinMaxScaler()
    normalized_data = normalisasi.fit_transform(data)
    return normalized_data


if uploaded_file is not None:
    new_data = pd.read_csv(uploaded_file)

    st.subheader("Data yang Diunggah:")
    st.write(new_data)

    selected_columns = ['los', 'voice_rev', 'voice_trx', 'voice_mou', 'voice_dou', 'sms_rev',
                        'sms_trx', 'sms_dou', 'voice_package_rev', 'voice_package_trx', 'voice_package_dou']
    input_data = new_data[selected_columns]

    normalized_data = preprocess_data(input_data)
    predicted_values = rfc.predict(normalized_data)

    new_data['prediksi'] = predicted_values

    accuracy = accuracy_score(new_data['churn'], new_data['prediksi'])
    st.subheader("Akurasi Prediksi:")
    st.write(f"{accuracy*100:.2f}%")

    st.subheader("Hasil Prediksi:")
    st.write(new_data)

    st.subheader(
        "Visualisasi Prediksi pelanggan yang punya kecenderungan akan churn:")
    category_counts = new_data['prediksi'].value_counts()
    st.bar_chart(category_counts)
