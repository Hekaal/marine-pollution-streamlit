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
        
        # --- KODE PEMBERSIHAN DATA 'pollution_type' YANG LEBIH LANJUT ---
        if 'pollution_type' in df.columns:
            # 1. Konversi ke string dan buang spasi di awal/akhir
            df['pollution_type'] = df['pollution_type'].astype(str).str.strip()
            
            # 2. Ubah semua teks menjadi huruf kecil untuk standarisasi (kemudian akan kita kapitalisasi lagi jika perlu)
            df['pollution_type'] = df['pollution_type'].str.lower()

            # 3. Ganti nilai-nilai yang bermasalah dengan 'Tidak Diketahui'
            problematic_values = ['nan', '', ' ', '-', '0', 'null', 'n/a', 'no data'] # Tambahkan jika ada nilai bermasalah lain yang Anda temukan di Excel
            df['pollution_type'] = df['pollution_type'].replace(problematic_values, 'tidak diketahui')
            
            # 4. Standarisasi ejaan (jika ada variasi umum, contoh: "oil spill" vs "oil spills")
            # Anda harus menyesuaikan ini berdasarkan variasi yang Anda temukan di data Anda
            df['pollution_type'] = df['pollution_type'].replace({
                'oil spill': 'tumpahan minyak',
                'oil spills': 'tumpahan minyak',
                'waste dumped overboard': 'limbah dibuang ke laut',
                'plastic waste': 'limbah plastik',
                # ... tambahkan lebih banyak jika ada variasi lain
            })

            # 5. Kapitalisasi huruf pertama setiap kata (opsional, untuk tampilan yang lebih rapi)
            df['pollution_type'] = df['pollution_type'].str.title()
            
            # 6. Pastikan 'Tidak Diketahui' tetap 'Tidak Diketahui' setelah title()
            df.loc[df['pollution_type'] == 'Tidak Diketahui', 'pollution_type'] = 'Tidak Diketahui'

        else:
            print("Peringatan: Kolom 'pollution_type' tidak ditemukan di dataset. Membuat kolom placeholder.")
            df['pollution_type'] = 'Tidak Diketahui (Kolom Hilang)'
        # --- AKHIR KODE PEMBERSIHAN ---

        print(f"DEBUG: Data Loaded Successfully. Total rows: {len(df)}")
        print(f"DEBUG: Unique pollution types after comprehensive cleaning: {df['pollution_type'].nunique()}")
        print("DEBUG: Top 10 pollution types after comprehensive cleaning:")
        print(df['pollution_type'].value_counts(dropna=False).head(10))

        return df
    except FileNotFoundError:
        st.error("Error: File 'Marine Pollution data.xlsx' tidak ditemukan. Pastikan file berada di direktori yang sama dengan aplikasi.")
        st.stop()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}. Mohon periksa format file Excel Anda.")
        st.stop()

# --- Sisa kode aplikasi Anda sama seperti sebelumnya ---
# --- (Anda bisa salin tempel sisa kode dari jawaban saya sebelumnya setelah fungsi load_data) ---
df = load_data()

st.title("🌍 Marine Pollution Dashboard")
st.markdown("Dashboard ini menampilkan visualisasi interaktif mengenai insiden polusi laut.")

st.sidebar.header("Filter Data")
countries = sorted(df['Country'].dropna().unique())
pollution_types = sorted(df['pollution_type'].dropna().unique())

# Set default date values for date input
if not df['inc_date'].empty and pd.notna(df['inc_date'].min()) and pd.notna(df['inc_date'].max()):
    min_date_for_picker = df['inc_date'].min().date()
    max_date_for_picker = df['inc_date'].max().date()
else:
    min_date_for_picker = datetime.date(1900, 1, 1) # Fallback to a very old date
    max_date_for_picker = datetime.date.today() # Fallback to today

# Handle cases where min_date might be after max_date due to data issues
if min_date_for_picker > max_date_for_picker:
    selected_dates = (max_date_for_picker, max_date_for_picker) # Set to a single day
else:
    selected_dates = st.sidebar.date_input("Rentang Tanggal", 
                                          value=(min_date_for_picker, max_date_for_picker), 
                                          min_value=min_date_for_picker, 
                                          max_value=max_date_for_picker)

selected_country = st.sidebar.selectbox("Pilih Negara", options=[None] + countries, format_func=lambda x: "Semua Negara" if x is None else x, index=0)
selected_pollution_type = st.sidebar.selectbox("Pilih Jenis Polusi", options=[None] + pollution_types, format_func=lambda x: "Semua Jenis Polusi" if x is None else x, index=0)


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
    print(f"DEBUG: Initial rows for filtering: {len(dff)}")

    if country:
        dff = dff[dff['Country'] == country]
        print(f"DEBUG: Rows after country filter '{country}': {len(dff)}")
    if ptype:
        dff = dff[dff['pollution_type'] == ptype]
        print(f"DEBUG: Rows after pollution type filter '{ptype}': {len(dff)}")
    if start_date and end_date:
        # Ensure 'inc_date' is datetime and compare only date part
        # Drop rows where 'inc_date' is NaT before comparison to avoid errors
        dff_temp = dff.dropna(subset=['inc_date']) 
        dff = dff_temp[(dff_temp['inc_date'].dt.date >= start_date.date()) & (dff_temp['inc_date'].dt.date <= end_date.date())]
        print(f"DEBUG: Rows after date filter '{start_date.date()} - {end_date.date()}': {len(dff)}")
    return dff

filtered_df = filter_dataframe(df, selected_country, selected_pollution_type, start_date_filter, end_date_filter)

print(f"DEBUG: Final filtered_df rows: {len(filtered_df)}")

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
    st.header("🗺️ Sebaran Lokasi Insiden Polusi Laut")
    st.caption("Visualisasi ini menunjukkan lokasi geografis insiden polusi laut berdasarkan koordinat yang tercatat. Warna pada titik menunjukkan jenis polusi yang terjadi.")
    if not filtered_df.empty:
        fig_map = px.scatter_geo(filtered_df, lat='LAT_1', lon='LONG', color='pollution_type', hover_name='Country', title="Peta Lokasi Insiden Polusi Laut", projection="natural earth", height=500)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Peta tidak dapat ditampilkan karena tidak ada data yang difilter.")

with col2:
    st.header("📊 Jenis Polusi Paling Umum")
    st.caption("Grafik batang ini menampilkan 5 jenis polusi laut yang paling sering terjadi dalam data yang difilter. Ini membantu mengidentifikasi polusi yang paling dominan.")
    
    top_pollution = pd.Series(dtype='int64') # Initialize as an empty Series for robustness

    # Determine which DataFrame to use for the bar chart
    data_for_bar_chart = filtered_df
    title_bar = "Top 5 Jenis Polusi (Data Difilter)"

    if filtered_df.empty:
        if not df.empty:
            st.warning("Tidak ada data yang sesuai dengan filter. Menampilkan data dari semua negara dan jenis polusi.")
            data_for_bar_chart = df
            title_bar = "Top 10 Jenis Polusi (Semua Data)"
        else:
            st.info("Tidak ada data yang tersedia baik dari filter maupun data asli untuk jenis polusi.")
            data_for_bar_chart = pd.DataFrame() # Ensure it's an empty DataFrame

    if not data_for_bar_chart.empty and 'pollution_type' in data_for_bar_chart.columns:
        # Calculate value_counts on the cleaned 'pollution_type' column
        temp_value_counts = data_for_bar_chart['pollution_type'].value_counts()
        
        print(f"DEBUG: Value counts for bar chart ({title_bar}):")
        print(temp_value_counts.head(10)) # Log top 10 counts to console

        if not temp_value_counts.empty:
            top_pollution = temp_value_counts.nlargest(10)
        else:
            print("DEBUG: Value counts result is empty after all cleaning.")
    else:
        print("DEBUG: Data for bar chart is empty or 'pollution_type' column is missing/problematic.")

    # --- Plotting logic ---
    if top_pollution is not None and not top_pollution.empty:
        fig_bar = px.bar(
            x=top_pollution.index,
            y=top_pollution.values,
            labels={'x': 'Jenis Polusi', 'y': 'Jumlah Kejadian'},
            title=title_bar,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Tidak ada data yang bisa ditampilkan untuk jenis polusi pada grafik ini. Mohon periksa data Excel atau filter yang dipilih.")


# Tren Waktu Insiden Polusi Laut
st.header("📈 Tren Waktu Insiden Polusi Laut")
st.caption("Grafik garis ini menampilkan jumlah insiden polusi laut dari waktu ke waktu, dikelompokkan per bulan.")
if not filtered_df.empty:
    dff_trend = filtered_df.dropna(subset=['inc_date'])
    if not dff_trend.empty:
        # Group by month and year
        trend = dff_trend.groupby(dff_trend['inc_date'].dt.to_period('M')).size().sort_index()
        trend.index = trend.index.to_timestamp() # Convert PeriodIndex to Timestamp for plotting
        fig_time_trend = px.line(x=trend.index, y=trend.values, labels={'x': 'Bulan', 'y': 'Jumlah Insiden'}, title='Tren Waktu Insiden Polusi Laut (Per Bulan)', markers=True)
        st.plotly_chart(fig_time_trend, use_container_width=True)
    else:
        st.info("Tidak ada data tanggal yang valid untuk menampilkan tren waktu dengan filter yang dipilih.")
else:
    st.info("Grafik tren waktu tidak dapat ditampilkan karena tidak ada data yang difilter.")

st.header("💡 Kesadaran dan Edukasi Publik")
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
st.header("📋 Detail Data Insiden")
st.caption("Tabel ini menyajikan data mentah dari insiden yang ditampilkan, termasuk negara, tanggal kejadian, jenis polusi, dan lokasi geografisnya.")
if not filtered_df.empty:
    st.dataframe(filtered_df[['Country', 'inc_date', 'pollution_type', 'material', 'LAT_1', 'LONG']], use_container_width=True, height=300)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Data yang Difilter (.csv)", data=csv, file_name='filtered_marine_pollution.csv', mime='text/csv')
else:
    st.info("Tabel data tidak dapat ditampilkan karena tidak ada data yang difilter.")

st.sidebar.markdown("---")
st.sidebar.markdown("Jalankan aplikasi ini dengan perintah:")
st.sidebar.code("streamlit run your_script_name.py")
