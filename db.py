import os
from typing import Dict, List, Tuple
from exception import MyException
from loguru import logger
import aiosqlite


DATABASE = os.path.join("db", "bashlike.db")


async def mark_done(user_id: int, task_serial: int) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"update task set is_done=True where serial_number=? and user_id=? and is_done=False",
            (task_serial, user_id),
        ) as cursor:
            changed_rows_count = cursor.rowcount
            logger.info(
                f"mark_done(user_id={user_id}, "
                f"task_serial={task_serial}) "
                f"changed_rows_count={changed_rows_count}"
            )
            if changed_rows_count == 1:
                await db.commit()
                return
            raise MyException(f"Нет задачи с номером {task_serial}")


async def get_dir_id_by_name(user_id: int, dir_name: str) -> int:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select id from dir where name=? and user_id=?", (dir_name, user_id)
        ) as cursor:
            res = await cursor.fetchone()
            logger.info(f"get_dir_id_by_name(user_id={user_id}, dir_name={dir_name}) db answer={res}")
            if res is None:
                raise MyException(f"Папка {dir_name} отсутсвует")

            return res[0]


async def fill_dirs_and_tasks_ids_under_dir(
    dirs: List, tasks: List, user_id: int, dir_id: int
) -> None:
    dirs.append(dir_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            "select id from dir where user_id=? and meta_dir_id=?", (user_id, dir_id)
        ) as cursor:
            res = await cursor.fetchall()
            for d in res:
                await fill_dirs_and_tasks_ids_under_dir(dirs, tasks, user_id, d[0])

        async with db.execute(
            "select id from task where dir_id=?", (dir_id,)
        ) as cursor:
            res = await cursor.fetchall()
            for t in res:
                tasks.append(t[0])


async def remove_dir(user_id: int, dir_name: str) -> None:
    logger.info(f"remove_dir({user_id=}, {dir_name})")
    dirs = []
    tasks = []
    dir_id = await get_dir_id_by_name(user_id, dir_name)
    await fill_dirs_and_tasks_ids_under_dir(dirs, tasks, user_id, dir_id)
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
            res = await cursor.fetchone()
            logger.info(f"create_user({user_id=}, {username=}) db answer={res}")

            if res is None:
                raise MyException('Ошибка при регистрации, попробуйте снова')
            root_dir_id = res[0]

            logger.info(f"create_user({user_id=}, {username=}) db update {root_dir_id=}")
            await cursor.execute(
                "insert into user (id, username, active_dir_id, root_dir_id) "
                "values (?,?,?,?)",
                (user_id, username, root_dir_id, root_dir_id),
            )
            await db.commit()


async def delete_user(user_id: int) -> None:
    logger.info(f"delete_user({user_id=})")
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("delete from user where id=?", (user_id,)):
            await db.commit()


async def get_user_by_id(user_id: int) -> str:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(f"select * from user where id=?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            logger.info(f"get_user_by_id(user_id={user_id} db answer={res}")
            if res is None:
                raise MyException(f"Нет пользователя с id={user_id}")
            return res[0]


async def check_user(user_id: int, username: str) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select id from user where id=?", (user_id, )) as cursor:
            res = cursor.fetchone()
            logger.info(f"check_user({user_id=}, {username=}) db answer {res=}")
            if res is None:
                await create_user(user_id, username)


async def set_root_as_active_dir(user_id: int) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"update user set active_dir_id=root_dir_id where id=?", (user_id,)
        ):
            logger.info(f"set_root_as_active_dir(user_id={user_id})")
            await db.commit()


async def get_active_directory_name(user_id: int) -> str:
    # FIXME add join
    dir_id = await get_active_directory_id(user_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(f"select name from dir where id=?", (dir_id,)) as cursor:
            res = await cursor.fetchone()
            logger.info(f"get_active_directory_name(user_id={user_id}) db answer={res}")
            if res is None:
                await set_root_as_active_dir(user_id)
                return "root"

            return res[0]


async def get_root_dir_id(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select root_dir_id from user where id=?", (user_id,)
        ) as cursor:
            res = await cursor.fetchone()
            logger.info(f"get_active_directory_id(user_id={user_id}) db answer={res}")

            if res is None:
                raise MyException("Ошибка при получении корневой папки") # FIXME обработать отсутсвие корневой папки
            return res[0]


async def get_active_directory_id(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select active_dir_id from user where id=?",
            (user_id,),
        ) as cursor:
            res = await cursor.fetchone()
            logger.info(f"get_active_directory_id(user_id={user_id}) db answer={res}")

            if res is None:
                await set_root_as_active_dir(user_id)
                root_id = await get_root_dir_id(user_id)
                return root_id

            return res[0]


async def check_unique(user_id: int, dir_name: str) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select * from dir where "
            f"exists (select * from dir where user_id=? and name=?)",
            (user_id, dir_name),
        ) as cursor:
            res = await cursor.fetchone()
            logger.info(f"check_unique(user_id={user_id}, dir_name={dir_name}) db answer={res}")

            return res is None


async def create_directory(dir_name: str, user_id: int) -> None:
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
        raise MyException("Имя папки должно быть уникальным")


async def get_directories(user_id: int) -> List[str]:
    active_dir_id = await get_active_directory_id(user_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select name from dir where meta_dir_id=?", (active_dir_id,)
        ) as cursor:
            res = await cursor.fetchall()
            logger.info(f"get_directories(user_id={user_id}) db answer={res}")
            if not res:
                return []
            return res


async def get_tasks_max_serial(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select max(serial_number) from task where user_id=?", (user_id,)
        ) as cursor:
            count = await cursor.fetchone()
            logger.info(f"get_tasks_max_serial(user_id={user_id}) db answer={count}")

            return count[0] or 0


async def create_task(content: str, user_id: int) -> None:
    dir_id = await get_active_directory_id(user_id)
    serial_number = await get_tasks_max_serial(user_id) + 1
    logger.info(f"create_task(content={content}, user_id={user_id}) dir_id={dir_id} serial_number={serial_number}")

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
            logger.info(f"get_tasks(user_id={user_id}) dir_id={dir_id} db answer={res}")

            if not res:
                return []
            return res


async def get_all_tasks(user_id: int) -> str:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select serial_number, content from task where user_id=?"
            f" and is_done=FALSE and dir_id not null",
            (user_id,),
        ) as cursor:
            res = await cursor.fetchall()
            logger.info(f"get_all_tasks(user_id={user_id}) db answer={res}")
            if not res:
                raise MyException("Нет активных задач")
            s = "\n"
            for t in res:
                s += f"{t[0]}. {t[1]}\n"
            return s


async def get_directory_context(user_id: int) -> str:
    cur_dir_name = await get_active_directory_name(user_id)
    tasks = await get_tasks(user_id)
    dirs = await get_directories(user_id)
    s = f"\n{cur_dir_name}/\n"
    for directory in dirs:
        s += f"\t{directory[0]}/\n"
    for task in tasks:
        s += f"\t{task[0]}. {task[1]}\n"
    logger.info(f"get_directory_context(user_id={user_id}) context={s}")

    return s


async def change_dir(user_id: int, dir_name: str) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select id from dir "
            f"where user_id=? "
            f"and meta_dir_id not null "
            f"and name=?",
            (user_id, dir_name),
        ) as cursor:
            res = await cursor.fetchone()
            logger.info( f"change_dir(user_id={user_id}, dir_name={dir_name}) db answer={res}")

            if res is None:
                raise MyException(f"Отсутствует папка с именем '{dir_name}'")
            new_active_dir_id = res[0]

            logger.info( f"change_dir(user_id={user_id}, dir_name={dir_name}) update active_dir_id={new_active_dir_id}")
            await cursor.execute(
                f"update user set active_dir_id=? where id=?", (new_active_dir_id, user_id)
            )
            await db.commit()


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
            logger.info(f"change_dir_to_meta(user_id={user_id}) db answer={res}")

            if res is None:
                await set_root_as_active_dir(user_id)
            meta_dir_id = res[0]

            logger.info(f"change_dir_to_meta(user_id={user_id}) update {meta_dir_id=}")
            await cursor.execute(
                f"update user set active_dir_id=? where id=?", (meta_dir_id, user_id)
            )
            await db.commit()


async def change_dir_to_root(user_id: int) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            f"select root_dir_id " f"from user where user.id=?", (user_id,)
        ) as cursor:
            res = await cursor.fetchone()
            logger.info(f"change_dir_to_root(user_id={user_id}) db answer={res}")
            if res is None:
                raise MyException("Ошибка при получении корневой директории")
            root_dir_id = res[0]
            logger.info(f"change_dir_to_root(user_id={user_id}) update {root_dir_id}")

            await cursor.execute(
                f"update user " f"set active_dir_id=? where id=?",
                (root_dir_id, user_id),
            )
            await db.commit()


async def _init_db():
    logger.info("init db")
    async with aiosqlite.connect(DATABASE) as db:
        async with db.cursor() as cursor:
            with open("createdb.sql", "r") as f:
                sql = f.read()
            await cursor.executescript(sql)
            await db.commit()


async def check_db_exists():
    logger.info("check_db_exists")
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master " "WHERE type='table' AND name='user'"
        ) as cursor:
            table_exists = await cursor.fetchall()
            if table_exists:
                return
            await _init_db()
