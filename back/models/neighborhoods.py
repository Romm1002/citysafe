from extensions import db
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

class Neighborhood(db.Model):
    __tablename__ = 'neighborhoods'

    id = db.Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    name = db.Column(VARCHAR(100), nullable=False)
