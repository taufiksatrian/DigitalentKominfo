import time
import utils
import schedule
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="API", page_icon="🚀")
st.sidebar.header("API")
st.title("API")
st.write(
    """"""
)

conn = st.connection("gsheets", type=GSheetsConnection)

# From API Pantau Banjir Jakarta
url = "https://sisteminformasibanjir.jakarta.go.id/api/report/pintuAirReports"
token = "T4EgIr1xIwsy7vr9UiAY64L61HWlDVN4V6qE3cc7OCvGzEg4hqhiagqatihAFgGB"

time_placeholder = st.sidebar.empty()


def display_current_time():
    while True:
        current_time = utils.get_current_time()
        time_placeholder.text(current_time)
        time.sleep(1)


def read_worksheet():
    st.cache_data.clear()
    df = utils.read_data()
    timestamp_column_type = type(df["timestamp"])
    first_timestamp = utils.get_first_timestamp(df)
    last_timestamp = utils.get_last_timestamp(df)
    count_data = df.shape[0]
    st.dataframe(df)
    st.write(f"{timestamp_column_type}")
    st.write(f"Data terawal dari kolom timestamp: {first_timestamp}")
    st.write(f"Data terakhir dari kolom timestamp: {last_timestamp}")
    st.write(f"Total jumlah data: {count_data}")
    return df


st.title("Read Data from Google Sheet")
# read_worksheet()

if st.button("Read Worksheet"):
    read_worksheet()
    st.text("Data refreshed successfully!")


def update_worksheet():
    st.cache_data.clear()
    data_df = utils.read_data()
    data_json = utils.scrape_data_realtime(url, token, data_df)
    data_df_realtime = utils.create_dataframe_from_json(data_json)
    st.success("Data berhasil diubah dari json ke dataframe")
    st.dataframe(data_df_realtime)
    data_df_realtime = utils.process_data(data_df_realtime)
    st.success("Data berhasil diproses.")
    st.dataframe(data_df_realtime)
    data_df_realtime = utils.filter(data_df_realtime, 'Manggarai BKB')
    st.success("Data berhasil difilter.")
    st.dataframe(data_df_realtime)
    data_df_realtime = utils.transform_data(data_df_realtime)
    st.success("Data berhasil diubah.")
    st.dataframe(data_df_realtime)
    data_df_realtime = utils.fix_timestamp_order(data_df_realtime)
    st.success("Data berhasil diperbaiki.")
    st.dataframe(data_df_realtime)
    # data_df_realtime = utils.sort_data(data_df_realtime)
    # st.success("Data berhasil diurutkan.")
    # st.dataframe(data_df_realtime)

    # data_df = data_df.drop_duplicates(subset='timestamp', keep='first')
    # data_df_realtime = data_df_realtime.drop_duplicates(
    #     subset='timestamp', keep='first')
    # duplicates = data_df_realtime[data_df_realtime['timestamp'].isin(
    #     data_df['timestamp'])]
    # st.dataframe(duplicates)

    mask = ~data_df_realtime['timestamp'].isin(data_df['timestamp'])
    data_df_realtime_filtered = data_df_realtime[mask]
    st.success("Data baru yang akan disimpan.")
    st.dataframe(data_df_realtime_filtered)

    utils.update_data(data_df_realtime_filtered)
    st.success("Success update data")
    st.cache_data.clear()
    df = utils.read_data()
    last_timestamp = utils.get_last_timestamp(df)
    st.dataframe(df)
    st.write(
        f"Data terakhir dari kolom timestamp: {last_timestamp}")
    st.write(f"Jumlah data baru: {data_df_realtime_filtered.shape[0]}")
    st.write(f"Total jumlah data: {df.shape[0]}")

    # if not data_df_realtime.empty:
    #     if duplicates.empty:
    #         utils.update_data(data_df_realtime_filtered)
    #         st.success("Success update data")
    #         st.cache_data.clear()
    #         df = utils.read_data()
    #         last_timestamp = utils.get_last_timestamp(df)
    #         st.dataframe(df)
    #         st.write(
    #             f"Data terakhir dari kolom timestamp: {last_timestamp}")
    #         st.write(f"Total jumlah data: {df.shape[0]}")
    #     else:
    #         st.cache_data.clear()
    #         df = utils.read_data()
    #         st.success("data baru")
    #         st.dataframe(data_df_realtime)
    #         last_timestamp = utils.get_last_timestamp(df)
    #         st.write(
    #             f"Data terakhir dari kolom timestamp: {last_timestamp}")
    #         st.success("data update terbaru")
    #         st.dataframe(data_df_realtime)
    #         df = utils.update_data(data_df_realtime_filtered)
    #         st.warning(
    #             'Some data already exists. Updated with new data.', icon="⚠️")
    #         st.cache_data.clear()
    #         last_timestamp = utils.get_last_timestamp(df)
    #         st.dataframe(df)
    #         st.write(
    #             f"Data terakhir dari kolom timestamp: {last_timestamp}")
    #         st.write(f"Total jumlah data: {df.shape[0]}")
    # else:
    #     st.warning('No data available for update.', icon="⚠️")


st.title("Update Data in Google Sheet")
if st.button("Update Worksheet"):
    st.cache_data.clear()
    update_worksheet()
    st.cache_data.clear()

# schedule.every().day.at("00:10").do(update_worksheet)
# schedule.every().day.at("06:10").do(update_worksheet)
# schedule.every().day.at("12:10").do(update_worksheet)
# schedule.every().day.at("18:10").do(update_worksheet)

# while True:
#     schedule.run_pending()
