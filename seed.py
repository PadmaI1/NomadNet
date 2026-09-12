from app import app
from models import db, Country, Location


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


    locations = [
        Location(
            name="Pune",
            type="city",
            country="India",
            city="Pune",
            latitude=18.5204,
            longitude=73.8567
        ),

        Location(
            name="Mumbai",
            type="city",
            country="India",
            city="Mumbai",
            latitude=19.0760,
            longitude=72.8777
        ),

        Location(
            name="Bangkok",
            type="city",
            country="Thailand",
            city="Bangkok",
            latitude=13.7563,
            longitude=100.5018
        ),

        Location(
            name="Phuket",
            type="city",
            country="Thailand",
            city="Phuket",
            latitude=7.8804,
            longitude=98.3923
        ),

        Location(
            name="Tokyo",
            type="city",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503
        ),

        Location(
            name="Rome",
            type="city",
            country="Italy",
            city="Rome",
            latitude=41.9028,
            longitude=12.4964
        ),
    ]

    db.session.add_all(locations)
    db.session.commit()

    print("Countries and locations added successfully!")