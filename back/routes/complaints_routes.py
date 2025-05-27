from flask import Blueprint, request, jsonify
from models.complaints import db, Complaint
from models.neighborhoods import Neighborhood

complaint_bp = Blueprint('complaint_bp', __name__)

# Obtenir toutes les plaintes
@complaint_bp.route('/complaints', methods=['GET'])
def get_all_complaints():
    complaints = Complaint.query.all()
    result = []
    for c in complaints:
        result.append({
            "id": c.id,
            "cmplnt_num": c.cmplnt_num,
            "boro_nm": c.boro_nm,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "neighborhood": {
                "id": c.neighborhood.id,
                "name": c.neighborhood.name
            } if c.neighborhood else None
        })
    return jsonify(result), 200

@complaint_bp.route('/complaints', methods=['POST'])
def create_complaint():
    data = request.get_json()

    try:
        new_complaint = Complaint(
            cmplnt_num=data.get("cmplnt_num"),
            addr_pct_cd=data.get("addr_pct_cd"),
            boro_nm=data.get("boro_nm"),
            cmplnt_fr_dt=data.get("cmplnt_fr_dt"),
            cmplnt_fr_tm=data.get("cmplnt_fr_tm"),
            cmplnt_to_dt=data.get("cmplnt_to_dt"),
            cmplnt_to_tm=data.get("cmplnt_to_tm"),
            crm_atpt_cptd_cd=data.get("crm_atpt_cptd_cd"),
            hadevelopt=data.get("hadevelopt"),
            housing_psa=data.get("housing_psa"),
            jurisdiction_code=data.get("jurisdiction_code"),
            juris_desc=data.get("juris_desc"),
            ky_cd=data.get("ky_cd"),
            law_cat_cd=data.get("law_cat_cd"),
            loc_of_occur_desc=data.get("loc_of_occur_desc"),
            ofns_desc=data.get("ofns_desc"),
            parks_nm=data.get("parks_nm"),
            patrol_boro=data.get("patrol_boro"),
            pd_cd=data.get("pd_cd"),
            pd_desc=data.get("pd_desc"),
            prem_typ_desc=data.get("prem_typ_desc"),
            rpt_dt=data.get("rpt_dt"),
            station_name=data.get("station_name"),
            susp_age_group=data.get("susp_age_group"),
            susp_race=data.get("susp_race"),
            susp_sex=data.get("susp_sex"),
            transit_district=data.get("transit_district"),
            vic_age_group=data.get("vic_age_group"),
            vic_race=data.get("vic_race"),
            vic_sex=data.get("vic_sex"),
            x_coord_cd=data.get("x_coord_cd"),
            y_coord_cd=data.get("y_coord_cd"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            lat_lon=data.get("lat_lon"),
            geocoded_column=data.get("geocoded_column"),
            neighborhood_id=data.get("neighborhood_id")
        )

        db.session.add(new_complaint)
        db.session.commit()

        return jsonify({"message": "Complaint created", "id": new_complaint.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
