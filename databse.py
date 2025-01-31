import sqlite3

DB_NAME = "grocery_list.db"

def init_db():
    """Initialize the database and create the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grocery_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_item(item):
    """Add an item to the grocery list."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grocery_list (item) VALUES (?)", (item,))
    conn.commit()
    conn.close()

def remove_item(item):
    """Remove an item from the grocery list."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grocery_list WHERE item = ?", (item,))
    conn.commit()
    conn.close()

def get_list():
    """Retrieve all items from the grocery list."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT item FROM grocery_list")
    items = [row[0] for row in cursor.fetchall()]
    conn.close()
    return items

def clear_list():
    """Clear the grocery list."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grocery_list")
    conn.commit()
    conn.close()

# Initialize database when script runs
init_db()
