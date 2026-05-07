from sqlalchemy import Column, Integer, String, JSON
from app.database import Base

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cooking_time = Column(Integer, nullable=False)  # минуты
    ingredients = Column(JSON, nullable=False)      # список строк
    description = Column(String, nullable=False)
    views = Column(Integer, default=0)