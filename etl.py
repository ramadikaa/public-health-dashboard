# === SECTION 1: DATA ACQUISITION & ETL (COMPLETE VERSION) ===
# Modul 2: Data Standards & Interoperability
# Modul 3: Database Management

import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime

# ===========================
# 1. KONEKSI DATABASE
# ===========================

def create_mysql_connection():
    """Create connection to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='ifteruts',
            user='root',
            password=''
        )
        if connection.is_connected():
            print("✅ Successfully connected to MySQL database")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

# ===========================
# 2. LOAD SEMUA DATA CSV
# ===========================

print("\n📂 Loading CSV files...")

# File 1: covid_19_clean_complete.csv
cleaned_data = pd.read_csv('forecasting/covid_19_clean_complete.csv', parse_dates=['Date'])
cleaned_data['Active'] = cleaned_data['Confirmed'] - cleaned_data['Deaths'] - cleaned_data['Recovered']
cleaned_data[['Province/State']] = cleaned_data[['Province/State']].fillna('')
cleaned_data[['Confirmed', 'Deaths', 'Recovered', 'Active']] = cleaned_data[['Confirmed', 'Deaths', 'Recovered', 'Active']].fillna(0)
print(f"✅ Loaded covid_19_clean_complete.csv: {len(cleaned_data)} rows")

# File 2: time_series_covid_19_confirmed.csv
ts_confirmed = pd.read_csv('forecasting/time_series_covid_19_confirmed.csv')
print(f"✅ Loaded time_series_covid_19_confirmed.csv: {len(ts_confirmed)} rows")

# File 3: time_series_covid_19_deaths.csv
ts_deaths = pd.read_csv('forecasting/time_series_covid_19_deaths.csv')
print(f"✅ Loaded time_series_covid_19_deaths.csv: {len(ts_deaths)} rows")

# File 4: time_series_covid_19_recovered.csv
ts_recovered = pd.read_csv('forecasting/time_series_covid_19_recovered.csv')
print(f"✅ Loaded time_series_covid_19_recovered.csv: {len(ts_recovered)} rows")

# File 5: train.csv (forecasting data)
train_data = pd.read_csv('forecasting/covid19-global-forecasting-week-1/train.csv', parse_dates=['Date'])
train_data[['Province/State']] = train_data[['Province/State']].fillna('')
train_data[['ConfirmedCases', 'Fatalities']] = train_data[['ConfirmedCases', 'Fatalities']].fillna(0)
print(f"✅ Loaded train.csv: {len(train_data)} rows")

# ===========================
# 3. FUNGSI INSERT (OPTIMIZED)
# ===========================

def insert_daily_cases_batch(connection, df, batch_size=1000):
    """
    Insert data ke tabel daily_cases menggunakan batch insert untuk performance
    Menggunakan executemany() yang lebih efisien daripada loop biasa
    """
    cursor = connection.cursor()
    
    query = """
    INSERT INTO daily_cases (province_state, country_region, latitude, longitude, 
                            date, confirmed, deaths, recovered, active, who_region)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Prepare data dalam bentuk list of tuples
    data_to_insert = []
    for _, row in df.iterrows():
        values = (
            row['Province/State'], 
            row['Country/Region'], 
            float(row['Lat']) if pd.notna(row['Lat']) else None,
            float(row['Long']) if pd.notna(row['Long']) else None,
            row['Date'], 
            int(row['Confirmed']), 
            int(row['Deaths']), 
            int(row['Recovered']), 
            int(row['Active']), 
            row['WHO Region']
        )
        data_to_insert.append(values)
    
    # Batch insert untuk performance lebih baik
    total_rows = len(data_to_insert)
    for i in range(0, total_rows, batch_size):
        batch = data_to_insert[i:i+batch_size]
        cursor.executemany(query, batch)
        connection.commit()
        print(f"   Inserted batch {i//batch_size + 1}: {len(batch)} rows")
    
    cursor.close()
    print(f"✅ Total inserted into daily_cases: {total_rows} rows")


def transform_and_insert_time_series(connection, df, table_name, value_column_name, batch_size=1000):
    """
    Transform time series data dari wide format ke long format,
    kemudian insert ke database
    """
    cursor = connection.cursor()
    
    # Get date columns (semua kolom kecuali Province/State, Country/Region, Lat, Long)
    date_columns = [col for col in df.columns if col not in ['Province/State', 'Country/Region', 'Lat', 'Long']]
    
    print(f"\n📊 Transforming {table_name} from wide to long format...")
    print(f"   Date columns found: {len(date_columns)}")
    
    # Melt dataframe dari wide ke long format
    df_long = df.melt(
        id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
        value_vars=date_columns,
        var_name='date_string',
        value_name=value_column_name
    )
    
    # Parse date string ke datetime
    df_long['date_column'] = pd.to_datetime(df_long['date_string'], format='%m/%d/%y')
    
    # Fill NA values
    df_long[['Province/State']] = df_long[['Province/State']].fillna('')
    df_long[[value_column_name]] = df_long[[value_column_name]].fillna(0)
    
    # Query insert
    if table_name == 'time_series_confirmed':
        query = """
        INSERT INTO time_series_confirmed (province_state, country_region, latitude, longitude, 
                                          date_column, confirmed_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
    elif table_name == 'time_series_deaths':
        query = """
        INSERT INTO time_series_deaths (province_state, country_region, latitude, longitude, 
                                       date_column, deaths_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
    elif table_name == 'time_series_recovered':
        query = """
        INSERT INTO time_series_recovered (province_state, country_region, latitude, longitude, 
                                          date_column, recovered_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
    
    # Prepare data
    data_to_insert = []
    for _, row in df_long.iterrows():
        values = (
            row['Province/State'],
            row['Country/Region'],
            float(row['Lat']) if pd.notna(row['Lat']) else None,
            float(row['Long']) if pd.notna(row['Long']) else None,
            row['date_column'],
            int(row[value_column_name])
        )
        data_to_insert.append(values)
    
    # Batch insert
    total_rows = len(data_to_insert)
    for i in range(0, total_rows, batch_size):
        batch = data_to_insert[i:i+batch_size]
        cursor.executemany(query, batch)
        connection.commit()
        print(f"   Inserted batch {i//batch_size + 1}: {len(batch)} rows")
    
    cursor.close()
    print(f"✅ Total inserted into {table_name}: {total_rows} rows")


def insert_training_data_batch(connection, df, batch_size=1000):
    """Insert data dari train.csv ke tabel training_data"""
    cursor = connection.cursor()
    
    query = """
    INSERT INTO training_data (id, province_state, country_region, latitude, longitude, 
                              date, confirmed_cases, fatalities)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Prepare data
    data_to_insert = []
    for _, row in df.iterrows():
        values = (
            int(row['Id']),
            row['Province/State'],
            row['Country/Region'],
            float(row['Lat']) if pd.notna(row['Lat']) else None,
            float(row['Long']) if pd.notna(row['Long']) else None,
            row['Date'],
            int(row['ConfirmedCases']),
            int(row['Fatalities'])
        )
        data_to_insert.append(values)
    
    # Batch insert
    total_rows = len(data_to_insert)
    for i in range(0, total_rows, batch_size):
        batch = data_to_insert[i:i+batch_size]
        cursor.executemany(query, batch)
        connection.commit()
        print(f"   Inserted batch {i//batch_size + 1}: {len(batch)} rows")
    
    cursor.close()
    print(f"✅ Total inserted into training_data: {total_rows} rows")


def create_dashboard_metrics(connection):
    """
    Create aggregated metrics untuk dashboard dari tabel daily_cases
    """
    cursor = connection.cursor()
    
    print("\n📊 Creating dashboard metrics...")
    
    # Query untuk aggregate data per tanggal
    query = """
    INSERT INTO dashboard_metrics 
        (date, total_confirmed, total_deaths, total_recovered, total_active, 
         daily_new_cases, daily_new_deaths, global_mortality_rate, global_recovery_rate)
    SELECT 
        date,
        SUM(confirmed) AS total_confirmed,
        SUM(deaths) AS total_deaths,
        SUM(recovered) AS total_recovered,
        SUM(active) AS total_active,
        SUM(confirmed) - LAG(SUM(confirmed)) OVER (ORDER BY date) AS daily_new_cases,
        SUM(deaths) - LAG(SUM(deaths)) OVER (ORDER BY date) AS daily_new_deaths,
        ROUND((SUM(deaths) / SUM(confirmed)) * 100, 2) AS global_mortality_rate,
        ROUND((SUM(recovered) / SUM(confirmed)) * 100, 2) AS global_recovery_rate
    FROM daily_cases
    GROUP BY date
    ORDER BY date
    ON DUPLICATE KEY UPDATE
        total_confirmed = VALUES(total_confirmed),
        total_deaths = VALUES(total_deaths),
        total_recovered = VALUES(total_recovered),
        total_active = VALUES(total_active),
        daily_new_cases = VALUES(daily_new_cases),
        daily_new_deaths = VALUES(daily_new_deaths),
        global_mortality_rate = VALUES(global_mortality_rate),
        global_recovery_rate = VALUES(global_recovery_rate)
    """
    
    cursor.execute(query)
    connection.commit()
    
    # Get row count
    cursor.execute("SELECT COUNT(*) FROM dashboard_metrics")
    count = cursor.fetchone()[0]
    
    cursor.close()
    print(f"✅ Dashboard metrics created: {count} date entries")


# ===========================
# 4. EXECUTE ETL PIPELINE
# ===========================

def run_complete_etl():
    """Main ETL pipeline untuk semua 5 file CSV"""
    
    print("\n" + "="*60)
    print("🚀 STARTING COMPLETE ETL PIPELINE")
    print("="*60)
    
    connection = create_mysql_connection()
    
    if not connection:
        print("❌ Failed to connect to database. Exiting...")
        return
    
    try:
        # 1. Insert daily_cases (dari covid_19_clean_complete.csv)
        print("\n[1/6] Inserting daily_cases...")
        insert_daily_cases_batch(connection, cleaned_data, batch_size=1000)
        
        # 2. Insert time_series_confirmed
        print("\n[2/6] Inserting time_series_confirmed...")
        transform_and_insert_time_series(connection, ts_confirmed, 
                                        'time_series_confirmed', 
                                        'confirmed_count', 
                                        batch_size=1000)
        
        # 3. Insert time_series_deaths
        print("\n[3/6] Inserting time_series_deaths...")
        transform_and_insert_time_series(connection, ts_deaths, 
                                        'time_series_deaths', 
                                        'deaths_count', 
                                        batch_size=1000)
        
        # 4. Insert time_series_recovered
        print("\n[4/6] Inserting time_series_recovered...")
        transform_and_insert_time_series(connection, ts_recovered, 
                                        'time_series_recovered', 
                                        'recovered_count', 
                                        batch_size=1000)
        
        # 5. Insert training_data
        print("\n[5/6] Inserting training_data...")
        insert_training_data_batch(connection, train_data, batch_size=1000)
        
        # 6. Create dashboard metrics
        print("\n[6/6] Creating dashboard metrics...")
        create_dashboard_metrics(connection)
        
        print("\n" + "="*60)
        print("✅ ETL PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Summary statistics
        cursor = connection.cursor()
        
        print("\n📊 DATABASE SUMMARY:")
        
        tables = ['daily_cases', 'time_series_confirmed', 'time_series_deaths', 
                 'time_series_recovered', 'training_data', 'dashboard_metrics']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count:,} rows")
        
        cursor.close()
        
    except Error as e:
        print(f"\n❌ Error during ETL: {e}")
        connection.rollback()
        
    finally:
        if connection.is_connected():
            connection.close()
            print("\n🔒 Database connection closed")


# ===========================
# 5. JALANKAN ETL
# ===========================

if __name__ == "__main__":
    run_complete_etl()
