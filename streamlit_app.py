import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(layout="wide", page_title="Marine Pollution Dashboard")

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Marine Pollution data.xlsx", sheet_name="ENV_Marine_Pollution_Obs_data_v")
        df['inc_date'] = pd.to_datetime(df['inc_date'], errors='coerce')
        df['pollution_qty'] = pd.to_numeric(df['pollution_qty'], errors='coerce')
        note_cols = [col for col in df.columns if col.startswith("Note")]
        df.drop(columns=note_cols, inplace=True)
        df = df.dropna(subset=['LAT_1', 'LONG'])
        return df
    except FileNotFoundError:
        st.error("Error: File 'Marine Pollution data.xlsx' tidak ditemukan.")
        st.stop()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
        st.stop()

df = load_data()

st.title("🌍 Marine Pollution Dashboard")
st.markdown("Dashboard ini menampilkan visualisasi interaktif mengenai insiden polusi laut.")

st.sidebar.header("Filter Data")
countries = sorted(df['Country'].dropna().unique())
pollution_types = sorted(df['pollution_type'].dropna().unique())

if not df['inc_date'].empty and pd.notna(df['inc_date'].min()) and pd.notna(df['inc_date'].max()):
    min_date_for_picker = df['inc_date'].min().date()
    max_date_for_picker = df['inc_date'].max().date()
else:
    min_date_for_picker = datetime.date(1900, 1, 1)
    max_date_for_picker = datetime.date.today()

selected_country = st.sidebar.selectbox("Pilih Negara", options=[None] + countries, format_func=lambda x: "Semua Negara" if x is None else x, index=0)
selected_pollution_type = st.sidebar.selectbox("Pilih Jenis Polusi", options=[None] + pollution_types, format_func=lambda x: "Semua Jenis Polusi" if x is None else x, index=0)
selected_dates = st.sidebar.date_input("Rentang Tanggal", value=(min_date_for_picker, max_date_for_picker), min_value=min_date_for_picker, max_value=max_date_for_picker)

if len(selected_dates) == 2:
    start_date_filter = pd.Timestamp(selected_dates[0])
    end_date_filter = pd.Timestamp(selected_dates[1])
elif len(selected_dates) == 1:
    start_date_filter = pd.Timestamp(selected_dates[0])
    end_date_filter = pd.Timestamp(selected_dates[0])
else:
    start_date_filter = None
    end_date_filter = None

def filter_dataframe(data_frame, country, ptype, start_date, end_date):
    dff = data_frame.copy()
    if country:
        dff = dff[dff['Country'] == country]
    if ptype:
        dff = dff[dff['pollution_type'] == ptype]
    if start_date and end_date:
        dff = dff[(dff['inc_date'] >= start_date) & (dff['inc_date'] <= end_date)]
    return dff

filtered_df = filter_dataframe(df, selected_country, selected_pollution_type, start_date_filter, end_date_filter)

if not df.empty:
    total = len(filtered_df)
    total_countries = filtered_df['Country'].nunique()
    total_types = filtered_df['pollution_type'].nunique()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Insiden", total)
    col2.metric("Negara Unik", total_countries)
    col3.metric("Jenis Polusi Unik", total_types)

col1, col2 = st.columns(2)

with col1:
    st.header("\U0001F5FA\ufe0f Sebaran Lokasi Insiden Polusi Laut")
    st.caption("Visualisasi ini menunjukkan lokasi geografis insiden polusi laut berdasarkan koordinat yang tercatat. Warna pada titik menunjukkan jenis polusi yang terjadi.")
    if not filtered_df.empty:
        fig_map = px.scatter_geo(filtered_df, lat='LAT_1', lon='LONG', color='pollution_type', hover_name='Country', title="Peta Lokasi Insiden Polusi Laut", projection="natural earth", height=500)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Peta tidak dapat ditampilkan karena tidak ada data yang difilter.")

with col2:
    st.header("\U0001F4CA Jenis Polusi Paling Umum")
    st.caption("Grafik batang ini menampilkan 10 jenis polusi laut yang paling sering terjadi dalam data yang difilter. Ini membantu mengidentifikasi polusi yang paling dominan.")
    if not filtered_df.empty:
        top_pollution = filtered_df['pollution_type'].value_counts().nlargest(10)
        title_bar = "Top 10 Jenis Polusi (Data Difilter)"
    elif not df.empty: # This is your fallback
        st.warning("Tidak ada data yang sesuai dengan filter. Menampilkan data dari semua negara dan jenis polusi.")
        top_pollution = df['pollution_type'].value_counts().nlargest(10)
        title_bar = "Top 10 Jenis Polusi (Semua Data)"
    else: # This block is reached if both filtered_df and df are empty
        top_pollution = None

    if top_pollution is not None and not top_pollution.empty:
        fig_bar = px.bar(
            x=top_pollution.index,
            y=top_pollution.values,
            labels={'x': 'Jenis Polusi', 'y': 'Jumlah Kejadian'},
            title=title_bar,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else: # This block is reached if top_pollution is None or empty
        st.info("Tidak ada data yang bisa ditampilkan untuk jenis polusi.")

if not filtered_df.empty:
    dff_trend = filtered_df.dropna(subset=['inc_date'])
    if not dff_trend.empty:
        trend = dff_trend.groupby(dff_trend['inc_date'].dt.to_period('M')).size().sort_index()
        trend.index = trend.index.to_timestamp()
        fig_time_trend = px.line(x=trend.index, y=trend.values, labels={'x': 'Bulan', 'y': 'Jumlah Insiden'}, title='Tren Waktu Insiden Polusi Laut (Per Bulan)', markers=True)
        st.plotly_chart(fig_time_trend, use_container_width=True)
    else:
        st.info("Tidak ada data tanggal yang valid untuk menampilkan tren waktu dengan filter yang dipilih.")
else:
    st.info("Grafik tren waktu tidak dapat ditampilkan karena tidak ada data yang difiltered.")

st.header("\U0001F4A1 Kesadaran dan Edukasi Publik")
st.caption("Diagram donat ini menggambarkan distribusi status kesadaran masyarakat ('aware') terhadap insiden polusi laut, berdasarkan kolom `aware_ans`.")
if not filtered_df.empty:
    if 'aware_ans' in filtered_df.columns:
        aware_count = filtered_df['aware_ans'].dropna().value_counts()
        if not aware_count.empty:
            fig_awareness = px.pie(names=aware_count.index, values=aware_count.values, title="Status 'Aware' Masyarakat", hole=0.3)
            st.plotly_chart(fig_awareness, use_container_width=True)
        else:
            st.info("Tidak ada data 'aware_ans' yang tersedia untuk filter yang dipilih.")
    else:
        st.info("Kolom 'aware_ans' tidak tersedia dalam dataset ini.")
else:
    st.info("Grafik kesadaran tidak dapat ditampilkan karena tidak ada data yang difilter.")

st.markdown("---")
st.header("\U0001F4CB Detail Data Insiden")
st.caption("Tabel ini menyajikan data mentah dari insiden yang ditampilkan, termasuk negara, tanggal kejadian, jenis polusi, dan lokasi geografisnya.")
if not filtered_df.empty:
    st.dataframe(filtered_df[['Country', 'inc_date', 'pollution_type', 'material', 'LAT_1', 'LONG']], use_container_width=True, height=300)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("\U0001F4E5 Download Data yang Difilter (.csv)", data=csv, file_name='filtered_marine_pollution.csv', mime='text/csv')
else:
    st.info("Tabel data tidak dapat ditampilkan karena tidak ada data yang difilter.")

st.sidebar.markdown("---")
st.sidebar.markdown("Jalankan aplikasi ini dengan perintah:")
st.sidebar.code("streamlit run your_script_name.py")
