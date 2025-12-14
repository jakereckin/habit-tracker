def select_users():
    sql = """
    SELECT EMAIL,
           PASSWORD
      FROM users
    """
    return sql

def insert_user():
    sql = """
    INSERT INTO users (EMAIL, PASSWORD)
    VALUES (?, ?)
    """
    return sql