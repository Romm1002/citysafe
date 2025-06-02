from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import requests
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import time 
import shutil
from sqlalchemy.dialects.mysql import DATE, INTEGER, DOUBLE, TEXT, TIMESTAMP, VARCHAR

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    cmplnt_num = db.Column(TEXT)
    addr_pct_cd = db.Column(INTEGER)
    boro_nm = db.Column(TEXT)
    cmplnt_fr_dt = db.Column(DATE, nullable=True)
    cmplnt_fr_tm = db.Column(TEXT)
    cmplnt_to_dt = db.Column(DATE, nullable=True)
    cmplnt_to_tm = db.Column(TEXT)
    crm_atpt_cptd_cd = db.Column(TEXT)
    hadevelopt = db.Column(TEXT)
    housing_psa = db.Column(INTEGER)
    jurisdiction_code = db.Column(INTEGER)
    juris_desc = db.Column(TEXT)
    ky_cd = db.Column(INTEGER)
    law_cat_cd = db.Column(TEXT)
    loc_of_occur_desc = db.Column(TEXT)
    ofns_desc = db.Column(TEXT)
    parks_nm = db.Column(TEXT)
    patrol_boro = db.Column(TEXT)
    pd_cd = db.Column(INTEGER)
    pd_desc = db.Column(TEXT)
    prem_typ_desc = db.Column(TEXT)
    rpt_dt = db.Column(TIMESTAMP(fsp=6))
    station_name = db.Column(TEXT)
    susp_age_group = db.Column(TEXT)
    susp_race = db.Column(TEXT)
    susp_sex = db.Column(TEXT)
    transit_district = db.Column(INTEGER)
    vic_age_group = db.Column(TEXT)
    vic_race = db.Column(TEXT)
    vic_sex = db.Column(TEXT)
    x_coord_cd = db.Column(INTEGER)
    y_coord_cd = db.Column(INTEGER)
    latitude = db.Column(DOUBLE(10, 6))
    longitude = db.Column(DOUBLE(10, 6))
    lat_lon = db.Column(VARCHAR(100))
    geocoded_column = db.Column(TEXT)

    # Relation avec Neighborhood
    neighborhood_id = db.Column(INTEGER(unsigned=True), db.ForeignKey('neighborhoods.id'))
    neighborhood = db.relationship('Neighborhood', backref=db.backref('complaints', lazy=True))



default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}


class Neighborhood(db.Model):
    __tablename__ = 'neighborhoods'

    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    name = db.Column(VARCHAR(100), nullable=False)
    boro = db.Column(VARCHAR(100), nullable=False)

def safe_int(val):
    try:
        return int(float(val)) if val not in (None, '', 'NaN') else None
    except:
        return None

def safe_float(val):
    try:
        return float(val) if val not in (None, '', 'NaN') else None
    except:
        return None
    
def parse_date(val):
    try:
        return datetime.strptime(val, '%m/%d/%Y')
    except Exception:
        return None



def download_csv():
    url = "https://data.cityofnewyork.us/api/views/5uac-w243/rows.csv?accessType=DOWNLOAD"
    output_path = "/usr/local/airflow/dags/data/nypd_complaint_data.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    response = requests.get(url)
    response.raise_for_status()  

    with open(output_path, 'wb') as f:
        f.write(response.content)

    print("✅ Fichier téléchargé :", output_path)

    # attendre 20 secondes

    time.sleep(15)

    #!/usr/bin/env python3
    # geojoin_neighborhoods.py

    # 1. Chemins vers tes fichiers
    CSV_PATH      = "/usr/local/airflow/dags/data/nypd_complaint_data.csv"
    GEOJSON_PATH  = "/usr/local/airflow/dags/data/neighborhoods.geojson"
    OUTPUT_CSV    = "/usr/local/airflow/dags/data/clean_data.csv"
    OLD_CSV       = "/usr/local/airflow/dags/old_data/clean_data.csv"

    # 2. Lecture du CSV
    df = pd.read_csv(CSV_PATH)

    # 3. Création d’une GeoDataFrame à partir des colonnes Lon/Lat
    gdf_points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326"   # WGS84, même CRS que ton GeoJSON
    )

    # 4. Lecture du GeoJSON des quartiers
    gdf_neigh = gpd.read_file(GEOJSON_PATH).to_crs("EPSG:4326")

    # 5. Spatial join : pour chaque point, on récupère les attributs du polygone contenant le point
    #    on ne garde que NTAName (et éventuellement BoroName si besoin)
    joined = gpd.sjoin(
        gdf_points,
        gdf_neigh[["NTAName", "geometry"]],
        how="left",
        predicate="within"
    )

    # 6. joined contient désormais une colonne 'NTAName'  
    #    on remet au format DataFrame pandas classique et on enlève les colonnes spatiales
    df_final = pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))

    # 7. Rapport sur les points hors quartier
    missing = df_final["NTAName"].isna().sum()

    # 8. Sauvegarde du CSV enrichi
    df_final.to_csv(OUTPUT_CSV, index=False)

    new_df = pd.read_csv(OUTPUT_CSV)
    old_df = pd.read_csv(OLD_CSV) if os.path.exists(OLD_CSV) else pd.DataFrame(columns=new_df.columns)

    new_data_only = pd.concat([new_df, old_df]).drop_duplicates(keep=False)

    if new_data_only.empty:
        print("🟡 Aucun nouveau enregistrement à insérer.")
    else:
        print(f"🟢 {len(new_data_only)} lignes à insérer.")

        # Quartiers
        nta_to_boro = {
            name.strip(): boro.strip() or "Unknown"
            for name, boro in zip(new_data_only['NTAName'], new_data_only['BORO_NM'])
            if name.strip()
        }

        for name, boro in nta_to_boro.items():
            if not Neighborhood.query.filter_by(name=name).first():
                db.session.add(Neighborhood(name=name, boro=boro))
        db.session.commit()

        mapping = {q.name: q.id for q in Neighborhood.query.all()}

        # Insertion plaintes
        count = 0
        for _, row in new_data_only.iterrows():
            try:
                comp = Complaint(
                    cmplnt_num          = row.get('CMPLNT_NUM'),
                    addr_pct_cd         = safe_int(row.get('ADDR_PCT_CD')),
                    boro_nm             = row.get('BORO_NM'),
                    cmplnt_fr_dt        = parse_date(row.get('CMPLNT_FR_DT')),
                    cmplnt_fr_tm        = row.get('CMPLNT_FR_TM'),
                    cmplnt_to_dt        = parse_date(row.get('CMPLNT_TO_DT')),
                    cmplnt_to_tm        = row.get('CMPLNT_TO_TM'),
                    crm_atpt_cptd_cd    = row.get('CRM_ATPT_CPTD_CD'),
                    hadevelopt          = row.get('HADEVELOPT'),
                    housing_psa         = safe_int(row.get('HOUSING_PSA')),
                    jurisdiction_code   = safe_int(row.get('JURISDICTION_CODE')),
                    juris_desc          = row.get('JURIS_DESC'),
                    ky_cd               = safe_int(row.get('KY_CD')),
                    law_cat_cd          = row.get('LAW_CAT_CD'),
                    loc_of_occur_desc   = row.get('LOC_OF_OCCUR_DESC'),
                    ofns_desc           = row.get('OFNS_DESC'),
                    parks_nm            = row.get('PARKS_NM'),
                    patrol_boro         = row.get('PATROL_BORO'),
                    pd_cd               = safe_int(row.get('PD_CD')),
                    pd_desc             = row.get('PD_DESC'),
                    prem_typ_desc       = row.get('PREM_TYP_DESC'),
                    rpt_dt              = parse_date(row.get('RPT_DT')),
                    station_name        = row.get('STATION_NAME'),
                    susp_age_group      = row.get('SUSP_AGE_GROUP'),
                    susp_race           = row.get('SUSP_RACE'),
                    susp_sex            = row.get('SUSP_SEX'),
                    transit_district    = safe_int(row.get('TRANSIT_DISTRICT')),
                    vic_age_group       = row.get('VIC_AGE_GROUP'),
                    vic_race            = row.get('VIC_RACE'),
                    vic_sex             = row.get('VIC_SEX'),
                    x_coord_cd          = safe_int(row.get('X_COORD_CD')),
                    y_coord_cd          = safe_int(row.get('Y_COORD_CD')),
                    latitude            = safe_float(row.get('Latitude')),
                    longitude           = safe_float(row.get('Longitude')),
                    lat_lon             = row.get('Lat_Lon'),
                    geocoded_column     = row.get('New Georeferenced Column'),
                    neighborhood_id     = mapping.get(row.get('NTAName', '').strip())
                )
                db.session.add(comp)
                count += 1
                if count % 500 == 0:
                    db.session.flush()
                    print(f"    flush à {count}")
            except Exception as e:
                print(f"⚠️ Ligne ignorée: {e}")

        db.session.commit()
        print(f"✅ {count} nouvelles plaintes ajoutées.")

    if os.path.exists(OLD_CSV):
        os.remove(OLD_CSV)

    if os.path.exists(CSV_PATH):
        os.remove(CSV_PATH)

    shutil.move(OUTPUT_CSV, OLD_CSV)




with DAG(
    dag_id='download_nypd_data_csv',
    default_args=default_args,
    description='Télécharge les données NYPD sans Selenium via Socrata API',
    schedule_interval="0 0 1 1,4,7,10 *",
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['nypd', 'socrata', 'csv']
) as dag:

    task_download_csv = PythonOperator(
        task_id='download_csv_data',
        python_callable=download_csv
    )
