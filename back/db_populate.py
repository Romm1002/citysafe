from flask import Flask
from dotenv import load_dotenv
import pandas as pd
import geopandas as gpd
from config import Config

from models.complaints import Complaint
from models.neighborhoods import Neighborhood
from extensions import db

from sqlalchemy import inspect

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Fichiers
CSV_PATH = "NYPD_Complaint_Data_Current__Year_To_Date__20250526.csv"
GEOJSON_PATH = "neighborhoods.geojson"

def enrich_and_insert_complaints():
    # Lecture des données
    df = pd.read_csv(CSV_PATH)
    gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]), crs="EPSG:4326")
    gdf_neigh = gpd.read_file(GEOJSON_PATH).to_crs("EPSG:4326")

    # Jointure spatiale
    joined = gpd.sjoin(gdf_points, gdf_neigh[["NTAName", "geometry"]], how="left", predicate="within")
    joined = joined.drop(columns=["geometry", "index_right"])

    print(f"Nombre de points sans quartier trouvé : {joined['NTAName'].isna().sum()} sur {len(joined)}")

    with app.app_context():
        # Mise en cache des quartiers
        neighborhoods_cache = Neighborhood.query.all()
 
        complaints = []
        for _, row in joined.iterrows():
            nta_name = row.get("NTAName", "")
            neighborhood_id = neighborhoods_cache.get(nta_name)

            complaint = Complaint(
                cmplnt_num=row.get("CMPLNT_NUM"),
                addr_pct_cd=row.get("ADDR_PCT_CD"),
                boro_nm=row.get("BORO_NM"),
                cmplnt_fr_dt=row.get("CMPLNT_FR_DT"),
                cmplnt_fr_tm=row.get("CMPLNT_FR_TM"),
                cmplnt_to_dt=row.get("CMPLNT_TO_DT"),
                cmplnt_to_tm=row.get("CMPLNT_TO_TM"),
                crm_atpt_cptd_cd=row.get("CRM_ATPT_CPTD_CD"),
                hadevelopt=row.get("HADEVELOPT"),
                housing_psa=row.get("HOUSING_PSA"),
                jurisdiction_code=row.get("JURISDICTION_CODE"),
                juris_desc=row.get("JURIS_DESC"),
                ky_cd=row.get("KY_CD"),
                law_cat_cd=row.get("LAW_CAT_CD"),
                loc_of_occur_desc=row.get("LOC_OF_OCCUR_DESC"),
                ofns_desc=row.get("OFNS_DESC"),
                parks_nm=row.get("PARKS_NM"),
                patrol_boro=row.get("PATROL_BORO"),
                pd_cd=row.get("PD_CD"),
                pd_desc=row.get("PD_DESC"),
                prem_typ_desc=row.get("PREM_TYP_DESC"),
                rpt_dt=row.get("RPT_DT"),
                station_name=row.get("STATION_NAME"),
                susp_age_group=row.get("SUSP_AGE_GROUP"),
                susp_race=row.get("SUSP_RACE"),
                susp_sex=row.get("SUSP_SEX"),
                transit_district=row.get("TRANSIT_DISTRICT"),
                vic_age_group=row.get("VIC_AGE_GROUP"),
                vic_race=row.get("VIC_RACE"),
                vic_sex=row.get("VIC_SEX"),
                x_coord_cd=row.get("X_COORD_CD"),
                y_coord_cd=row.get("Y_COORD_CD"),
                latitude=row.get("Latitude"),
                longitude=row.get("Longitude"),
                lat_lon=f"{row.get('Latitude')}, {row.get('Longitude')}",
                geocoded_column=None,
                neighborhood_id=neighborhood_id
            )
            complaints.append(complaint)

        db.session.bulk_save_objects(complaints)
        db.session.commit()
        print(f"{len(complaints)} plaintes insérées dans la base de données.")

if __name__ == "__main__":
    enrich_and_insert_complaints()
