import db
from db import (
    create_directory,
    get_directory_context,
    create_task,
    change_dir,
    change_dir_to_root,
    get_all_tasks,
    change_dir_to_meta,
    get_user_by_id,
    mark_done,
    remove_dir,
    fill_dirs_and_tasks_ids_under_dir,
    get_dir_id_by_name,
    delete_user,
)
from typing import NamedTuple, List, Type, Optional
from loguru import logger

from exception import MyException

COMMANDS = [
    "ls",
    "cd",
    "mktask",
    "rmtask",
    "tasks",
    "mkdir",
    "fdir",
    "done",
    "pwd",
    "rmdir",
    "user",
]


class ParsedMessage(NamedTuple):
    command: str
    # options: List[str]
    arg: str | None


def parse_message(message: str) -> ParsedMessage | str:
    splited = message.split()
    command = splited[0].lower()
    parsed_message = ParsedMessage(
        command=command, arg=message[len(splited[0]) + 1 :].strip()
    )
    return parsed_message


async def ls(user_id):
    context = await get_directory_context(user_id)
    return "```" + context + "```"


async def resolve_message(message: str, user_id: int) -> str:
    logger.info(f"start resolve message={message} for user_id={user_id}")
    parsed_message = parse_message(message)
    logger.info(f"message={message} parsed to {parsed_message}")
    if isinstance(parsed_message, str):
        return parsed_message
    match parsed_message.command:
        case "mkdir" | "сп":
            if parsed_message.arg == "":
                return "Название папки не может быть пустым"
            await create_directory(parsed_message.arg, user_id)
            return await ls(user_id)

        case "ls" | "че":
            return await ls(user_id)

        case "mktask" | "сз":
            if parsed_message.arg == "":
                raise MyException("Задача не может быть пустой")
            await create_task(parsed_message.arg, user_id)
            return await ls(user_id)

        case "tasks" | "вз":
            tasks = await get_all_tasks(user_id)
            return "```" + tasks + "```"

        case "cd" | "пп":
            if parsed_message.arg == "..":
                await change_dir_to_meta(user_id)
            elif parsed_message.arg == "":
                await change_dir_to_root(user_id)
            else:
                await change_dir(user_id, parsed_message.arg)

            return await ls(user_id)

        case "done" | "зз":
            try:
                task_serial = int(parsed_message.arg)
            except ValueError:
                raise MyException("Чтобы завершить задачу введите её индекс")
            await mark_done(user_id, task_serial)
            return await ls(user_id)

        case "rmdir" | "уп":
            if parsed_message.arg == "":
                raise MyException("Название папки не может быть пустым")
            if parsed_message.arg == "root":
                raise MyException("Вы не можете удалить корневую директорию")

            await remove_dir(user_id, parsed_message.arg)
            return await ls(user_id)

        case "user":
            return await get_user_by_id(user_id)

        case "test":
            pass

        case "deleteme":
            await delete_user(user_id)

        case _:
            raise MyException(f"'{parsed_message.command}' не является командой")
