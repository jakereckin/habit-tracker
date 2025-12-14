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

def get_habits():
    sql = """
    SELECT habit_list.*
      FROM habit_list
      INNER JOIN users
        ON habit_list.EMAIL = users.EMAIL
    """
    return sql

def insert_habits():
    sql = """
    INSERT INTO habit_list (EMAIL, HABIT_NAME, HABIT_DESCRIPTION, START_DATE, ACTIVE, GOAL_TYPE, DIFFICULTY)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    return sql