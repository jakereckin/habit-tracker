def ensure_user():
    sql = """
    INSERT INTO users (EMAIL, PASSWORD)
    SELECT ?, ''
     WHERE NOT EXISTS (
           SELECT 1
             FROM users
            WHERE LOWER(EMAIL) = LOWER(?)
     )
    """
    return sql


def clear_legacy_password():
    sql = """
    UPDATE users
       SET PASSWORD = ''
     WHERE LOWER(EMAIL) = LOWER(?)
    """
    return sql


def get_habits():
    sql = """
    SELECT EMAIL,
           HABIT_NAME,
           HABIT_DESCRIPTION,
           START_DATE,
           ACTIVE,
           GOAL_TYPE,
           DIFFICULTY
      FROM habit_list
     WHERE LOWER(EMAIL) = LOWER(?)
     ORDER BY HABIT_NAME
    """
    return sql


def insert_habits():
    sql = """
    INSERT INTO habit_list (EMAIL, HABIT_NAME, HABIT_DESCRIPTION, START_DATE, ACTIVE, GOAL_TYPE, DIFFICULTY)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    return sql


def set_habit_active():
    sql = """
    UPDATE habit_list
       SET ACTIVE = ?
     WHERE LOWER(EMAIL) = LOWER(?)
       AND HABIT_NAME = ?
    """
    return sql


def add_daily_habits():
    sql = """
    INSERT INTO daily_tracking (EMAIL, HABIT_NAME, DATE, TIME, COUNT_COMPLETED)
    SELECT ?, ?, ?, ?, ?
     WHERE NOT EXISTS (
           SELECT 1
             FROM daily_tracking
            WHERE LOWER(EMAIL) = LOWER(?)
              AND HABIT_NAME = ?
              AND DATE = ?
     )
    """
    return sql


def remove_daily_habit():
    sql = """
    DELETE FROM daily_tracking
     WHERE LOWER(EMAIL) = LOWER(?)
       AND HABIT_NAME = ?
       AND DATE = ?
    """
    return sql


def get_tracking():
    sql = """
    SELECT EMAIL,
           HABIT_NAME,
           DATE,
           TIME,
           COUNT_COMPLETED
      FROM daily_tracking
     WHERE LOWER(EMAIL) = LOWER(?)
     ORDER BY DATE
    """
    return sql