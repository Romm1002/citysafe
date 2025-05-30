from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import DOUBLE, INTEGER, VARCHAR, TEXT, TIMESTAMP
import os
from dotenv import load_dotenv
import json
from config import Config

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

class Neighborhood(db.Model):
    __tablename__ = 'neighborhoods'
    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    name = db.Column(VARCHAR(100), nullable=False)
    boro = db.Column(VARCHAR(100), nullable=False)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    cmplnt_num = db.Column(TEXT)
    addr_pct_cd = db.Column(INTEGER)
    boro_nm = db.Column(TEXT)
    cmplnt_fr_dt = db.Column(TIMESTAMP(fsp=6))
    cmplnt_fr_tm = db.Column(TEXT)
    cmplnt_to_dt = db.Column(TIMESTAMP(fsp=6))
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

    # Relation vers Neighborhood
    neighborhood_id = db.Column(INTEGER(unsigned=True), db.ForeignKey('neighborhoods.id'))
    neighborhood = db.relationship('Neighborhood', backref=db.backref('complaints', lazy=True))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Base de données et tables créées.")
