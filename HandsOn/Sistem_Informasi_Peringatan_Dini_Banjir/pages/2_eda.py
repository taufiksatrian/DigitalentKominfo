import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import re
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Exploratory Data Analysis", page_icon="📊")
st.sidebar.header("Exploratory Data Analysis")
st.title("Exploratory Data Analysis")
st.write(
    """"""
)

conn = st.connection("gsheets", type=GSheetsConnection)


def read_data():
    st.cache_data.clear()
    df = conn.read(worksheet="Aktual")
    df = df[['timestamp', 'ketinggian', 'status_siaga', 'cuaca', 'name_pintu_air']]
    df = df.dropna(how='all')
    return df


def get_last_timestamp(df):
    last_timestamp = df['timestamp'].iloc[-1]
    return last_timestamp


def get_first_timestamp(df):
    first_timestamp = df['timestamp'].iloc[0]
    return first_timestamp


def descriptive_stats(df):
    # Describe
    data_desc = df.describe()
    first_timestamp = get_first_timestamp(df)
    last_timestamp = get_last_timestamp(df)
    st.markdown("**Descriptive Statistics:**")
    st.text(data_desc)
    st.markdown(
        f"Data ini mencakup periode waktu dari **{first_timestamp}** hingga **{last_timestamp}**.")


def check_missing_values(df):
    missing_values = df.isnull().sum()
    missing_values = missing_values[missing_values > 0]

    if not missing_values.empty:
        st.write("Missing Values")
        st.table(missing_values.reset_index().rename(
            columns={0: 'Count', 'index': 'Column'}))
    else:
        st.write("No Missing Values")


def plot_histogram(df):
    fig_hist = px.histogram(df, x='ketinggian', nbins=20,
                            title='Histogram Ketinggian')
    st.plotly_chart(fig_hist)


def plot_box_plot(df):
    fig_box = px.box(df, y='ketinggian', title='Box Plot Ketinggian')
    st.plotly_chart(fig_box)


def plot_line_chart(df):
    fig = px.line(df, x='timestamp', y='ketinggian',
                  title='Line Chart Ketinggian')
    st.plotly_chart(fig)


def adf_test(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df['ketinggian']

    adf_result = adfuller(df)
    adf_statistic = adf_result[0]
    p_value = adf_result[1]
    critical_values = adf_result[4]

    if p_value <= 0.05:
        result = "Data time series stationer (H0 ditolak)"
    else:
        result = "Data time series tidak stationer (H0 Tidak ditolak)"

    st.write("**Augmented Dickey-Fuller (ADF) Test**")
    st.write(f"ADF Statistic: {adf_statistic}")
    st.write(f"P-Value: {p_value}")
    st.write(f"Critical Values: {critical_values}")
    st.write(f"Conclusion: {result}")


def shapiro_wilk_test(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df['ketinggian']
    statistic, p_value = stats.shapiro(df)
    alpha = 0.05

    if p_value > alpha:
        result = "Data time series terdistribusi normal (H0 diterima)"
    else:
        result = "Data time series tidak terdistribusi normal (H0 ditolak)"

    st.write("**Shapiro-Wilk Test**")
    st.write(f"Statistic: {statistic}")
    st.write(f"P-Value: {p_value}")
    st.write(f"Conclusion: {result}")


def process_and_filter_data(data_df):
    data_df = data_df.drop_duplicates(subset='timestamp', keep='first')
    data_df = data_df.sort_values(by='timestamp')
    data_df["timestamp"] = data_df["timestamp"].dt.strftime(
        "%d/%m/%Y %H:%M")
    return data_df


df = read_data()
st.markdown("### **Data TMA Manggarai BKB Sebelum Preprocessing**")
st.dataframe(df)


def main(df):
    descriptive_stats(df)
    check_missing_values(df)
    plot_histogram(df)
    plot_box_plot(df)
    plot_line_chart(df)
    adf_test(df)
    shapiro_wilk_test(df)


def after_preprocessing(df):
    descriptive_stats(df)
    plot_histogram(df)
    plot_box_plot(df)
    plot_line_chart(df)
    adf_test(df)
    shapiro_wilk_test(df)


# def identify_and_replace_outliers_zscore(df, column_name='ketinggian', z_threshold=-3):
#     df.reset_index(drop=True, inplace=True)
#     z_scores = stats.zscore(df[column_name])
#     outliers = (z_scores < z_threshold)
#     outlier_count = outliers.sum()

#     st.write("Outlier Identification")
#     st.write("Number of outliers identified:", outlier_count)

#     for i in range(1, len(df) - 1):
#         if outliers[i]:
#             df.at[i, column_name] = df.at[i - 1, column_name]

#     st.write("Outliers Replaced")
#     st.table(df)


# def identify_and_replace_outliers_zscore_streamlit(df, column_name='ketinggian', z_threshold=-3):
#     z_scores = stats.zscore(df[column_name])
#     outliers = (z_scores < z_threshold)
#     outlier_count = outliers.sum()

#     st.write("### Outlier Identification")
#     st.write("Number of outliers identified:", outlier_count)

#     df_before = df[outliers]

#     df[column_name] = np.where(outliers, np.roll(
#         df[column_name], 1), df[column_name])

#     df_after = df[outliers]

#     st.write("### Outliers Before Replacement")
#     st.table(df_before)

#     st.write("### Outliers After Replacement")
#     st.table(df_after)
#     return df

def detect_sudden_changes(df, column_name='ketinggian', threshold=50):
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], format="%d/%m/%Y %H:%M:%S")
    df_copy = df.copy()
    df_copy['perbedaan'] = df_copy[column_name].diff()
    df_copy['perubahan_tiba_tiba'] = (df_copy['perbedaan'] < 0) & (
        df_copy['perbedaan'].abs() >= threshold)
    df_copy = df_copy.sort_values(by='timestamp')
    st.dataframe(df_copy)
    fig_changes = px.scatter(df_copy, x='timestamp', y='ketinggian',
                             color='perubahan_tiba_tiba', title='Deteksi Perubahan Tiba-tiba')
    st.plotly_chart(fig_changes)

    df_copy[column_name] = df_copy[column_name].where(
        ~df_copy['perubahan_tiba_tiba'], df_copy[column_name].shift(1))
    df_copy = df_copy.sort_values(by='timestamp')
    fig_changes = px.scatter(df_copy, x='timestamp', y='ketinggian',
                             color='perubahan_tiba_tiba', title='Setelah ditangani data Perubahan Tiba-tiba')
    st.plotly_chart(fig_changes)

    return df_copy


def preprocessing(df):
    st.markdown("### **Data TMA Manggarai BKB Setelah Preprocessing**")
    df = read_data()
    df = detect_sudden_changes(df)
    after_preprocessing(df)
    df = process_and_filter_data(df)
    conn.update(worksheet="AfterPreprocessing", data=df)


if __name__ == '__main__':
    main(df)
    preprocessing(df)
