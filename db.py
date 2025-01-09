import os
from typing import Dict, List, Tuple

import aiosqlite


DATABASE = os.path.join("db", "bashlike.db")


async def mark_done(user_id: int, task_serial: int) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"update task set is_done=True where serial_number=? and user_id=?",
            (task_serial, user_id),
        ) as cursor:
            changed_rows = cursor.rowcount
            await db.commit()
            if changed_rows == 1:
                return True
            return False


async def get_dir_id_by_name(user_id: int, dir_name: str) -> int:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select id from dir where name=? and user_id=?", (dir_name, user_id)
        ) as cursor:
            res = await cursor.fetchone()
            return res[0]


async def get_dirs_and_tasks_ids_under_dir(
    dirs: List, tasks: List, user_id: int, dir_id: int
):
    dirs.append(dir_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            "select id from dir where user_id=? and meta_dir_id=?", (user_id, dir_id)
        ) as cursor:
            res = await cursor.fetchall()
            for d in res:
                await get_dirs_and_tasks_ids_under_dir(dirs, tasks, user_id, d[0])

        async with db.execute(
            "select id from task where dir_id=?", (dir_id,)
        ) as cursor:
            res = await cursor.fetchall()
            for t in res:
                tasks.append(t[0])


async def remove_dir(user_id: int, dir_name: str) -> str | None:
    dirs = []
    tasks = []

    dir_id = await get_dir_id_by_name(user_id, dir_name)
    if dir_id is None:
        return f"Папка {dir_name} отсутсвует"

    await get_dirs_and_tasks_ids_under_dir(dirs, tasks, user_id, dir_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.cursor() as cursor:
            if dirs:
                dirs_placeholders = ", ".join("?" for _ in dirs)
                await cursor.execute(
                    f"delete from dir where id in ({dirs_placeholders})", tuple(dirs)
                )
            if tasks:
                tasks_placeholders = ", ".join("?" for _ in tasks)
                await cursor.execute(
                    f"delete from task where id in ({tasks_placeholders})", tuple(tasks)
                )
        await db.commit()


async def create_user(user_id: int, username: str) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"insert into dir (name, user_id) " f"values ('root',?)", (user_id,)
        ) as cursor:
            await db.commit()

            await cursor.execute(f"select id from dir where user_id=?", (user_id,))
            root_dir_id = await cursor.fetchone()[0]
            if root_dir_id is not None:
                await cursor.execute(
                    "insert into user (id, username, active_dir_id, root_dir_id) "
                    "values (?,?,?,?)",
                    (user_id, username, root_dir_id, root_dir_id),
                )
                await db.commit()
            else:
                print("PROBLEM in create_user")


async def get_user_by_id(user_id: int) -> str | None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(f"select * from user where id=?", (user_id,)) as cursor:
            usr = await cursor.fetchone()
            if usr:
                return usr
            return None


async def check_user(user_id: int, username: str) -> str:
    usr = await get_user_by_id(user_id)
    if usr:
        return f"{usr} IN DA BASE"
    else:
        await create_user(user_id, username)
    usr = await get_user_by_id(user_id)
    return usr


async def set_root_as_active_dir(user_id: int) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"update user set active_dir_id=root_dir_id where id=?", (user_id,)
        ):
            await db.commit()


async def get_active_directory_name(user_id: int) -> str:
    # FIXME add join
    dir_id = await get_active_directory_id(user_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(f"select name from dir where id=?", (dir_id,)) as cursor:
            dir_name = await cursor.fetchone()
            if dir_name:
                return dir_name[0]
            else:
                return None


async def get_active_directory_id(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select COALESCE(active_dir_id, root_dir_id) " f"from user where id=?",
            (user_id,),
        ) as cursor:
            dir_id = await cursor.fetchone()
            if dir_id:
                return dir_id[0]
            else:
                return None


async def check_unique(user_id: int, dir_name: str) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select * from dir where "
            f"exists (select * from dir where user_id=? and name=?)",
            (user_id, dir_name),
        ) as cursor:
            res = await cursor.fetchone()
            return res is None


async def create_directory(dir_name: str, user_id: int) -> None | str:
    active_dir_id = await get_active_directory_id(user_id)
    is_unique = await check_unique(user_id, dir_name)
    if is_unique:
        async with aiosqlite.connect(DATABASE) as db:
            async with db.execute(
                f"insert into dir (name, user_id, meta_dir_id) values (?,?,?)",
                (dir_name, user_id, active_dir_id),
            ):
                await db.commit()
    else:
        return "Имя папки должно быть уникальным"


async def get_directories(user_id: int) -> List[str]:
    active_dir_id = await get_active_directory_id(user_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select name from dir where meta_dir_id=?", (active_dir_id,)
        ) as cursor:
            res = await cursor.fetchall()
            if not res:
                return []
            return res


async def get_tasks_max_serial(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select max(serial_number) from task where user_id=?", (user_id,)
        ) as cursor:
            count = await cursor.fetchone()
            return count[0] or 0


async def create_task(content: str, user_id: int) -> None:
    dir_id = await get_active_directory_id(user_id)
    serial_number = await get_tasks_max_serial(user_id) + 1
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "insert into task (serial_number, dir_id, content, user_id, is_done) "
            "values (?,?,?,?,?)",
            (serial_number, dir_id, content, user_id, False),
        )
        await db.commit()


async def get_tasks(user_id: int) -> List[str]:
    dir_id = await get_active_directory_id(user_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select serial_number, content from task where dir_id=? and is_done=FALSE",
            (dir_id,),
        ) as cursor:
            res = await cursor.fetchall()
            if not res:
                return []
            return res


async def get_all_tasks(user_id: int) -> str | None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select serial_number, content from task where user_id=?"
            f" and is_done=FALSE and dir_id not null",
            (user_id,),
        ) as cursor:
            res = await cursor.fetchall()
            if not res:
                return None
            s = "\n"
            for t in res:
                s += f"{t[0]}. {t[1]}\n"
            return s


async def get_directory_context(user_id: int) -> str:
    cur_dir_name = await get_active_directory_name(user_id)
    if cur_dir_name is None:
        await set_root_as_active_dir(user_id)
        cur_dir_name = "root"
    tasks = await get_tasks(user_id)
    dirs = await get_directories(user_id)
    s = f"\n{cur_dir_name}/\n"
    for directory in dirs:
        s += f"\t{directory[0]}/\n"
    for task in tasks:
        s += f"\t{task[0]}. {task[1]}\n"

    return s


async def change_dir(user_id: int, dir_name: str) -> str | None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select id from dir "
            f"where user_id=? "
            f"and meta_dir_id not null "
            f"and name=?",
            (user_id, dir_name),
        ) as cursor:
            res = await cursor.fetchone()
            new_dir_id = res[0]
            if new_dir_id is None:
                return False

            await cursor.execute(
                f"update user set active_dir_id=? where id=?", (new_dir_id, user_id)
            )
            await db.commit()
        return True


async def change_dir_to_meta(user_id: int) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select dir.meta_dir_id "
            f"from user "
            f"join dir ON user.active_dir_id = dir.id "
            f"where user.id=?",
            (user_id,),
        ) as cursor:
            res = await cursor.fetchone()
            meta_dir_id = res[0]
            if meta_dir_id is None:
                return

            await cursor.execute(
                f"update user set active_dir_id=? where id=?", (meta_dir_id, user_id)
            )
            await db.commit()
    return True


async def change_dir_to_root(user_id: int) -> str | None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select root_dir_id " f"from user where user.id=?", (user_id,)
        ) as cursor:
            res = await cursor.fetchone()
            root_dir_id = res[0]
            if root_dir_id is None:
                return "Отсуствует root"

            await cursor.execute(
                f"update user " f"set active_dir_id=? where id=?",
                (root_dir_id, user_id),
            )
            await db.commit()


async def _init_db():
    """Инициализирует БД"""

    async with aiosqlite.connect(DATABASE) as db:
        with open("createdb.sql", "r") as f:
            sql = f.read()
        await cursor.executescript(sql)
        await db.commit()


async def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master " "WHERE type='table' AND name='user'"
        ) as cursor:
            table_exists = await cursor.fetchall()
            if table_exists:
                return
            await _init_db()
