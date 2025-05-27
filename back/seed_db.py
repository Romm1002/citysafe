# back/seed_db.py

import os, sys, csv
from flask import Flask
from extensions import db
from models.neighborhoods import Neighborhood
from models.complaints    import Complaint
from config import Config

# 1) Init Flask + SQLAlchemy
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 2) Chemin vers le CSV
HERE     = os.path.dirname(__file__)
CSV_PATH = os.path.abspath(os.path.join(
    HERE, '..', 'webapp', 'citysafe', 'public',
    'NYPD_with_NTAName_from_latlon.csv'
))
if not os.path.exists(CSV_PATH):
    print("❌ CSV introuvable :", CSV_PATH)
    sys.exit(1)

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

def main():
    with app.app_context():
        # — 3) Extraire tous les quartiers uniques + leur boro
        nta_to_boro = {}
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('NTAName', '').strip()
                boro = row.get('BORO_NM', '').strip() or 'Unknown'
                if name and name not in nta_to_boro:
                    nta_to_boro[name] = boro
        print(f"⚙️  {len(nta_to_boro)} quartiers uniques détectés")

        # — 4) Insérer ou récupérer ces quartiers en base
        for name, boro in nta_to_boro.items():
            q = Neighborhood.query.filter_by(name=name).first()
            if not q:
                q = Neighborhood(name=name, boro=boro)
                db.session.add(q)
        db.session.commit()
        print("  → Quartiers synchronisés en base")

        # — 5) Construire le mapping name → id
        mapping = {q.name: q.id for q in Neighborhood.query.all()}

        # — 6) Insertion des plaintes (bulk streaming)
        print("⚙️  Insertion des plaintes…")
        count = 0
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                count += 1
                try:
                    comp = Complaint(
                        cmplnt_num          = row.get('CMPLNT_NUM'),
                        addr_pct_cd         = safe_int(row.get('ADDR_PCT_CD')),
                        boro_nm             = row.get('BORO_NM'),
                        cmplnt_fr_dt        = row.get('CMPLNT_FR_DT'),
                        cmplnt_fr_tm        = row.get('CMPLNT_FR_TM'),
                        cmplnt_to_dt        = row.get('CMPLNT_TO_DT'),
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
                        rpt_dt              = row.get('RPT_DT'),
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
                except Exception as e:
                    print(f"⚠️ Ligne {count} ignorée: {e}")

                # flush par paquets de 500
                if count % 500 == 0:
                    db.session.flush()
                    print(f"    flush à {count}")

        db.session.commit()
        print(f"✅ Import terminé : {count} plaintes ajoutées.")

if __name__ == '__main__':
    main()
