#!/usr/bin/env python3
# geojoin_neighborhoods.py

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# 1. Chemins vers tes fichiers
CSV_PATH      = "NYPD_Complaint_Data_Current__Year_To_Date__20250526.csv"
GEOJSON_PATH  = "neighborhoods.geojson"       # ton GeoJSON de quartiers
OUTPUT_CSV    = "NYPD_with_NTAName_from_latlon.csv"

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
print(f"Nombre de points sans quartier trouvé : {missing} sur {len(df_final)}")

# 8. Sauvegarde du CSV enrichi
df_final.to_csv(OUTPUT_CSV, index=False)
print(f"CSV généré : {OUTPUT_CSV}")
