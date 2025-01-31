from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_NAME = "grocery_list.db"
DATABASE_URL = f"sqlite:///{DB_NAME}"

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)  # Set echo=True for SQL logs
SessionLocal = sessionmaker(bind=engine)

# GroceryList model
class GroceryList(Base):
    __tablename__ = "grocery_list"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item = Column(String, nullable=False)

# Initialize database
def init_db():
    """Initialize the database and create the table if it doesn't exist."""
    Base.metadata.create_all(engine)

# CRUD Operations
def add_item(item):
    """Add an item to the grocery list."""
    session = SessionLocal()
    try:
        grocery_item = GroceryList(item=item)
        session.add(grocery_item)
        session.commit()
    finally:
        session.close()

def remove_item(item):
    """Remove an item from the grocery list."""
    session = SessionLocal()
    try:
        session.query(GroceryList).filter(GroceryList.item == item).delete()
        session.commit()
    finally:
        session.close()

def get_list():
    """Retrieve all items from the grocery list."""
    session = SessionLocal()
    try:
        items = session.query(GroceryList.item).all()
        return [item[0] for item in items]
    finally:
        session.close()

def clear_list():
    """Clear the grocery list."""
    session = SessionLocal()
    try:
        session.query(GroceryList).delete()
        session.commit()
    finally:
        session.close()

# Initialize the database when the script is run
init_db()
