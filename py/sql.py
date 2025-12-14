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

def add_daily_habits():
    sql = """
    INSERT INTO daily_tracking (EMAIL, HABIT_NAME, DATE, TIME, COUNT_COMPLETED)
    VALUES (?, ?, ?, ?, ?)
    """
    return sql

def get_current_day():
    sql = """
    SELECT *
      FROM daily_tracking
      INNER JOIN users
        ON daily_tracking.EMAIL = users.EMAIL
     WHERE DATE = DATE('now', 'localtime')
    """
    return sql