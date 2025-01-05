import os
from typing import Dict, List, Tuple

import sqlite3


conn = sqlite3.connect(os.path.join("db", "bashlike.db"))
cursor = conn.cursor()

def get_cursor():
    return cursor

def create_user(user_id: int, username: str) -> None:
    cursor.execute(f"insert into dir (name, user_id) "
                   f"values ('root',{user_id})")
    conn.commit()
    cursor.execute(f"select id from dir where user_id={user_id}")

    root_dir_id = cursor.fetchone()[0]
    if root_dir_id is not None:
        cursor.execute("insert into user (id, username, active_dir_id, root_dir_id) "
                       "values (?,?,?,?)",
                       (user_id, username, root_dir_id, root_dir_id))
        conn.commit()
    else:
        print('PROBLEM in create_user')


def get_user_by_id(user_id: int) -> str | None:
    cursor.execute(f"select * from user where id={user_id}")
    usr = cursor.fetchone()
    if usr:
        return usr
    return None

def check_user(user_id: int, username: str) -> str:
    usr = get_user_by_id(user_id)
    if usr:
        return f'{usr}IN DA BASE'
    else:
        create_user(user_id, username)
    usr = get_user_by_id(user_id)
    return usr


def get_active_directory_id(user_id: int) -> int:
    cursor.execute(f"select active_dir_id from user "
                   f"where id={user_id}")
    dir_id = cursor.fetchone()
    return dir_id[0]

def get_active_directory_name(user_id: int) -> str:
    #FIXME add join
    dir_id = get_active_directory_id(user_id)
    cursor.execute(f"select name from dir "
                   f"where id={dir_id}")
    dir_name = cursor.fetchone()
    return dir_name[0]

def create_directory(dir_name: str, user_id: int) -> None:
    active_dir_id = get_active_directory_id(user_id)

    cursor.execute(f"insert into dir (name, user_id, meta_dir_id) "
                   "values (?,?,?)",
                   (dir_name, user_id, active_dir_id))
    conn.commit()

def get_directories(user_id: int) -> List[str]:
    active_dir_id = get_active_directory_id(user_id)

    cursor.execute(f"select name from dir where meta_dir_id={active_dir_id}")
    res = cursor.fetchall()
    if not res:
        return []
    return res


def get_tasks_count(user_id: int) -> int:
    cursor.execute(f'select count(id) from task where user_id={user_id}')
    count = cursor.fetchone()
    if count:
        return count[0]

def create_task(content: str, user_id: int) -> None:
    dir_id = get_active_directory_id(user_id)
    serial_number = get_tasks_count(user_id) + 1
    cursor.execute("insert into task (serial_number, dir_id, content, user_id, is_done) "
                   "values (?,?,?,?,?)",
                   (serial_number, dir_id, content, user_id, False))
    conn.commit()

def get_tasks(user_id: int) -> List[str]:
    dir_id = get_active_directory_id(user_id)
    cursor.execute(f"select serial_number, content from task where dir_id={dir_id} and is_done=FALSE")
    res = cursor.fetchall()
    if not res:
        return []
    return res

def get_all_tasks(user_id: int) -> str | None:
    cursor.execute(f"select serial_number, content from task where user_id={user_id}")
    res = cursor.fetchall()
    if not res:
        return None
    s = '\n'
    for t in res:
        s += f"{t[0]}. {t[1]}\n"
    return s

def get_directory_context(user_id: int) -> str:
    cur_dir_name = get_active_directory_name(user_id)
    tasks = get_tasks(user_id)
    dirs = get_directories(user_id)
    s = f"\n{cur_dir_name}/\n"
    for directory in dirs:
        s += f"\t{directory[0]}/\n"
    for task in tasks:
        s += f"\t{task[0]}. {task[1]}\n"

    return s


def change_dir(user_id: int, dir_name: str) -> str | None:
    active_dir_id = get_active_directory_id(user_id)
    cursor.execute(f"select id from dir "
                   f"where user_id={user_id} "
                   #f"and root_dir_id={active_dir_id} "
                   f"and name='{dir_name}'"
                   )
    if (f := cursor.fetchone()) is None:
        return f'{dir_name} does not exist'
    new_dir_id = f[0]

    cursor.execute(f"update user "
                   f"set active_dir_id={new_dir_id} "
                   f"where id={user_id}")

    conn.commit()


def change_dir_to_meta(user_id: int) -> str:
    cursor.execute(f"select dir.meta_dir_id "
                   f"from user "
                   f"join dir ON user.active_dir_id = dir.id "
                   f"where user.id={user_id}")
    meta_dir_id = cursor.fetchone()[0]
    if meta_dir_id is None:
        return 'meta dir does not exist'

    cursor.execute(f"update user "
                   f"set active_dir_id={meta_dir_id} "
                   f"where id={user_id}")
    conn.commit()
    return "dir changed"

def change_dir_to_root(user_id: int) -> str:
    cursor.execute(f"select root_dir_id "
                   f"from user "
                   f"where user.id={user_id}")
    root_dir_id = cursor.fetchone()[0]
    print('ROOT', root_dir_id)
    if root_dir_id is None:
        return 'root dir does not exist'

    cursor.execute(f"update user "
                   f"set active_dir_id={root_dir_id} "
                   f"where id={user_id}")
    conn.commit()
    return "dir changed"


def _init_db():
    """Инициализирует БД"""
    with open("createdb.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()

def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='user'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()

check_db_exists()



