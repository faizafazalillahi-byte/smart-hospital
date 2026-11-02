from app.database import engine, Base
from app import models  # zaroori: isse tables register hoti hain

Base.metadata.create_all(bind=engine)
print("Tables create ho gayi!")
