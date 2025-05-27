from flask import Flask
from config import Config
from models.neighborhoods import db
from routes.neighborhoods_routes import neighborhood_bp
from models.complaints import db
from routes.complaints_routes import complaint_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(complaint_bp, url_prefix='/api')
app.register_blueprint(neighborhood_bp, url_prefix='/api')

if __name__ == "__main__":
    app.run(debug=True)
