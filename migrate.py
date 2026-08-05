import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    item = Column(String)
    status = Column(String, default='pending')
    admin_comment = Column(String, nullable=True)

# Создаём только недостающие таблицы и колонки (не удаляем данные!)
Base.metadata.create_all(engine)
print("✅ Миграция завершена: таблица orders и колонка admin_comment готовы.")
