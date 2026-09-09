from app import app
from models import db, Country


with app.app_context():

    countries = [
        Country(name="India", code="IN"),
        Country(name="Thailand", code="TH"),
        Country(name="Japan", code="JP"),
        Country(name="Vietnam", code="VN"),
        Country(name="Italy", code="IT"),
    ]

    db.session.add_all(countries)
    db.session.commit()

    print("Countries added successfully!")