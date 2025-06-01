from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db
from routes.neighborhoods_routes import neighborhood_bp
from routes.complaints_routes import complaint_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": "*"}})

db.init_app(app)

app.register_blueprint(complaint_bp, url_prefix='/api')
app.register_blueprint(neighborhood_bp, url_prefix='/api')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
 