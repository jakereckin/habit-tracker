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
           DIFFICULTY,
           DEFAULT_DAILY_GOAL,
           GOAL_FREQUENCY,
           SCHEDULED_DAYS,
           PERIOD_TARGET
      FROM habit_list
     WHERE LOWER(EMAIL) = LOWER(?)
     ORDER BY HABIT_NAME
    """
    return sql


def insert_habits():
    sql = """
    INSERT INTO habit_list (
        EMAIL, HABIT_NAME, HABIT_DESCRIPTION, START_DATE, ACTIVE,
        GOAL_TYPE, DIFFICULTY, DEFAULT_DAILY_GOAL,
        GOAL_FREQUENCY, SCHEDULED_DAYS, PERIOD_TARGET
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def update_habit_cadence():
    sql = """
    UPDATE habit_list
       SET GOAL_FREQUENCY = ?,
           SCHEDULED_DAYS = ?,
           PERIOD_TARGET = ?
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


def update_daily_goal():
    sql = """
    UPDATE daily_tracking
       SET DAILY_GOAL = ?
     WHERE LOWER(EMAIL) = LOWER(?)
       AND HABIT_NAME = ?
       AND DATE = ?
    """
    return sql


def insert_daily_goal():
    sql = """
    INSERT INTO daily_tracking (
        EMAIL, HABIT_NAME, DATE, TIME, COUNT_COMPLETED, DAILY_GOAL
    )
    SELECT ?, ?, ?, ?, 0, ?
     WHERE NOT EXISTS (
           SELECT 1
             FROM daily_tracking
            WHERE LOWER(EMAIL) = LOWER(?)
              AND HABIT_NAME = ?
              AND DATE = ?
     )
    """
    return sql


def add_numeric_progress():
    sql = """
    UPDATE daily_tracking
       SET COUNT_COMPLETED = COALESCE(COUNT_COMPLETED, 0) + ?,
           DAILY_GOAL = ?,
           TIME = ?
     WHERE LOWER(EMAIL) = LOWER(?)
       AND HABIT_NAME = ?
       AND DATE = ?
    """
    return sql


def insert_numeric_progress():
    sql = """
    INSERT INTO daily_tracking (
        EMAIL, HABIT_NAME, DATE, TIME, COUNT_COMPLETED, DAILY_GOAL
    )
    SELECT ?, ?, ?, ?, ?, ?
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
    SELECT tracking.EMAIL,
           tracking.HABIT_NAME,
           tracking.DATE,
           tracking.TIME,
           tracking.COUNT_COMPLETED,
           tracking.DAILY_GOAL,
           habits.GOAL_TYPE,
           habits.DEFAULT_DAILY_GOAL,
           habits.GOAL_FREQUENCY,
           habits.SCHEDULED_DAYS,
           habits.PERIOD_TARGET
      FROM daily_tracking AS tracking
      LEFT JOIN habit_list AS habits
        ON LOWER(habits.EMAIL) = LOWER(tracking.EMAIL)
       AND habits.HABIT_NAME = tracking.HABIT_NAME
     WHERE LOWER(tracking.EMAIL) = LOWER(?)
     ORDER BY tracking.DATE
    """
    return sql


def get_skip_days():
    sql = """
    SELECT EMAIL, HABIT_NAME, DATE
      FROM habit_skip_days
     WHERE LOWER(EMAIL) = LOWER(?)
     ORDER BY DATE
    """
    return sql


def insert_skip_day():
    sql = """
    INSERT INTO habit_skip_days (EMAIL, HABIT_NAME, DATE)
    SELECT ?, ?, ?
     WHERE NOT EXISTS (
           SELECT 1
             FROM habit_skip_days
            WHERE LOWER(EMAIL) = LOWER(?)
              AND HABIT_NAME = ?
              AND DATE = ?
     )
    """
    return sql


def remove_skip_day():
    sql = """
    DELETE FROM habit_skip_days
     WHERE LOWER(EMAIL) = LOWER(?)
       AND HABIT_NAME = ?
       AND DATE = ?
    """
    return sql