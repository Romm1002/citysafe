from flask import Blueprint, request, jsonify
from models.neighborhoods import db, Neighborhood

neighborhood_bp = Blueprint('neighborhood_bp', __name__)

@neighborhood_bp.route('/neighborhoods', methods=['GET'])
def get_neighborhoods():
    neighborhoods = Neighborhood.query.all()
    return jsonify([{"id": u.id, "name": u.name} for u in neighborhoods])

@neighborhood_bp.route('/neighborhoods', methods=['POST'])
def create_neighborhood():
    data = request.json
    neighborhood = Neighborhood(name=data['name'])
    db.session.add(neighborhood)
    db.session.commit()
    return jsonify({"message": "Neighborhood created", "id": neighborhood.id}), 201
