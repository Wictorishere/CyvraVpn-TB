from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Config(Base):
    __tablename__ = 'configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_configs = Column(String)

engine = create_engine('sqlite:///configs.db', echo=True)

Base.metadata.create_all(engine)

print("✅ جدول configs با موفقیت در SQLite ساخته شد!")
