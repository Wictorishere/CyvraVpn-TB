from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Config(Base):
    __tablename__ = 'configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_configs = Column(String)

engine = create_engine('sqlite:///configs.db')
Session = sessionmaker(bind=engine)
session = Session()

new_config = Config(test_configs="test 1")

session.add(new_config)

session.commit()

