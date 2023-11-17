import re
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection


conn = st.connection("gsheets", type=GSheetsConnection)


@st.cache_data(persist="disk")
def read_data():
    st.cache_data.clear()
    df = conn.read(worksheet="Aktual")
    df = df[['timestamp', 'ketinggian', 'status_siaga', 'cuaca', 'name_pintu_air']]
    df = df.dropna(how='all')
    return df


@st.cache_data(persist="disk")
def update_data(new_df):
    st.cache_data.clear()
    df = read_data()
    df = df.dropna(subset=['timestamp'])
    new_df = new_df.dropna(subset=['timestamp'])
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], format="%d/%m/%Y %H:%M:%S")
    new_df["timestamp"] = pd.to_datetime(
        new_df["timestamp"], format="%Y/%m/%d %H:%M:%S")
    update_df = pd.concat([df, new_df], ignore_index=True)
    update_df = process_and_filter_data(update_df)
    update_df = conn.update(worksheet="Aktual", data=update_df)
    return update_df


def process_and_filter_data(data_df):
    data_df = data_df.drop_duplicates(subset='timestamp', keep='first')
    # data_df["timestamp"] = pd.to_datetime(data_df["timestamp"], format="%Y/%m/%d %H:%M:%S")
    data_df = data_df.sort_values(by='timestamp')
    data_df["timestamp"] = data_df["timestamp"].dt.strftime(
        "%d/%m/%Y %H:%M")
    return data_df


def get_last_timestamp(df):
    last_timestamp = pd.to_datetime(
        df['timestamp'], format="%d/%m/%Y %H:%M:%S").iloc[-1]
    return last_timestamp


def get_first_timestamp(df):
    first_timestamp = df['timestamp'].iloc[0]
    return first_timestamp


def scrape_data_realtime(url, token, df):
    last_timestamp = get_last_timestamp(df)
    last_timestamp = last_timestamp.strftime("%d/%m/%Y %H:%M")
    last_timestamp = re.sub(
        r'(\d{2})/(\d{2})/(\d{4}) (\d{2}:\d{2})', r'\1-\2-\3 \4', last_timestamp)
    start_date = datetime.strptime(
        last_timestamp, "%d-%m-%Y %H:%M") + timedelta(hours=1)

    end_date = start_date + timedelta(hours=6)

    json_data_list = []

    while start_date <= end_date:
        formatted_date = start_date.strftime("%Y-%m-%d")
        formatted_url = f"{url}/{formatted_date}?format=json"

        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36 Edg/117.0.2045.43",
            "token": token,
            "Referer": "https://pantaubanjir.jakarta.go.id/"
        }

        response = requests.get(formatted_url, headers=headers)

        if response.status_code == 200:
            print(f"Berhasil mengambil data untuk tanggal {formatted_date}")
            json_data_list.append(response.json())
        else:
            print(
                f"Gagal mengambil data untuk tanggal {formatted_date}. Kode status:", response.status_code)

        start_date += timedelta(days=1)

    combined_json_data = {"data": []}
    for json_data in json_data_list:
        combined_json_data["data"].extend(json_data["data"])

    return combined_json_data


def create_dataframe_from_json(data_json):
    data_df = pd.DataFrame(data_json['data'])
    return data_df


def process_data(df):
    df['cuaca'] = df['cuaca'].apply(lambda x: x['nama'])
    df['id_pintu_air'] = df['pintu_air'].apply(lambda x: x['id'])
    df['name_pintu_air'] = df['pintu_air'].apply(lambda x: x['name'])

    data_df = df[['tanggal', 'jam', 'ketinggian',
                  'status_siaga', 'cuaca', 'name_pintu_air']]

    return data_df


def filter(data_df, pintu_air_name):
    data_df = data_df[data_df['name_pintu_air'] == pintu_air_name]
    return data_df


def transform_data(data_df):
    data_df["timestamp"] = pd.to_datetime(
        data_df["tanggal"] + " " + data_df["jam"])
    data_df["timestamp"] = pd.to_datetime(
        data_df["timestamp"], format="%d/%m/%Y %H:%M")
    # data_df["timestamp"] = data_df["timestamp"].dt.strftime("%d/%m/%Y %H:%M")
    data_df = data_df[['timestamp', 'ketinggian',
                       'status_siaga', 'cuaca', 'name_pintu_air']]
    return data_df


def sort_data(data_df):
    data_df["timestamp"] = pd.to_datetime(
        data_df["timestamp"], format="%d/%m/%Y %H:%M")
    data_df = data_df.sort_values(by='timestamp')
    return data_df


def fix_timestamp_order(data_df):
    data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])
    data_df['timestamp'] = data_df['timestamp'].dt.strftime(
        "%d/%m/%Y %H:%M")
    correct_order = pd.DataFrame(pd.date_range(start=data_df['timestamp'].min(
    ), end=data_df['timestamp'].max(), freq='H'), columns=['timestamp'])
    correct_order['timestamp'] = correct_order['timestamp'].dt.strftime(
        "%d/%m/%Y %H:%M")
    data_df = pd.merge(correct_order, data_df, on='timestamp', how='left')
    data_df = data_df.fillna(method='ffill')
    data_df["timestamp"] = pd.to_datetime(
        data_df["timestamp"], format="%d/%m/%Y %H:%M")
    return data_df


def get_current_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return current_time
