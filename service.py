import db
from db import get_cursor


def check_user(user_id: int) -> None:
    cursor = get_cursor()
    cursor.execute("select id from user"
                   f"where id={user_id}")
    usr = cursor.fetchall()