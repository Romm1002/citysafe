from flask import Blueprint, request, jsonify
from models.neighborhoods import db, Neighborhood
from models.complaints    import Complaint

neighborhood_bp = Blueprint('neighborhood_bp', __name__)

@neighborhood_bp.route('/neighborhoods', methods=['GET'])
def get_neighborhoods():
    neighborhoods = Neighborhood.query.all()
    return jsonify([{"id": u.id, "name": u.name} for u in neighborhoods])

@neighborhood_bp.route('/neighborhoods/<int:neighborhood_id>', methods=['GET'])
def get_neighborhood(neighborhood_id):
    neighborhood = Neighborhood.query.get(neighborhood_id)
    return jsonify({
        "id":   neighborhood.id,
        "name": neighborhood.name,
        "boro": neighborhood.boro
    })

@neighborhood_bp.route('/neighborhoods/<int:neighborhood_id>/crime_count', methods=['GET'])
def get_crime_count(neighborhood_id):
    n = Neighborhood.query.get(neighborhood_id)
    if not n:
        abort(404, "Neighborhood not found")
    count = Complaint.query.filter_by(neighborhood_id=neighborhood_id).count()
    return jsonify({"neighborhood_id": neighborhood_id, "count": count}), 200

@neighborhood_bp.route('/neighborhoods', methods=['POST'])
def create_neighborhood():
    data = request.json
    neighborhood = Neighborhood(name=data['name'])
    db.session.add(neighborhood)
    db.session.commit()
    return jsonify({"message": "Neighborhood created", "id": neighborhood.id}), 201
