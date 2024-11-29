from sqlalchemy import create_engine, MetaData

DATABASE_URL = "sqlite:///data/series.db"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
