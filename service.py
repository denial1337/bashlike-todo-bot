import db
from db import (
    get_cursor,
    create_directory,
    get_directory_context,
    create_task,
    change_dir,
    change_dir_to_root,
    get_all_tasks,
    change_dir_to_meta,
    get_user_by_id,
    cursor,
    mark_done,
    remove_dir,
    get_dirs_and_tasks_ids_under_dir,
    get_dir_id_by_name,
)
from typing import NamedTuple, List, Type, Optional

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
    parsed_message = ParsedMessage(command=command, arg=message[len(splited[0]) + 1 :])
    return parsed_message


def ls(user_id):
    return "```" + get_directory_context(user_id) + "```"


def resolve_message(message: str, user_id: int) -> str | None:
    parsed_message = parse_message(message)
    if isinstance(parsed_message, str):
        return parsed_message
    match parsed_message.command:
        case "mkdir" | "сп":
            if parsed_message.arg == "":
                return "Название папки не может быть пустым"
            res = create_directory(parsed_message.arg, user_id)
            if res is None:
                return ls(user_id)
            return res

        case "ls" | "че":
            return ls(user_id)

        case "mktask" | "сз":
            if parsed_message.arg == "":
                return "Название задачи не может быть пустым"
            create_task(parsed_message.arg, user_id)
            return ls(user_id)

        case "tasks" | "вз":
            tasks = get_all_tasks(user_id)
            if tasks is None:
                return "Нет задач"
            return "```" + tasks + "```"

        case "cd" | "пп":
            if parsed_message.arg == "..":
                change_dir_to_meta(user_id)
                return ls(user_id)
            if parsed_message.arg == "":
                change_dir_to_root(user_id)
                return ls(user_id)
            if not change_dir(user_id, parsed_message.arg):
                return f"Папки {parsed_message.arg} не существует"
            else:
                return ls(user_id)

        case "done" | "зз":
            try:
                task_serial = int(parsed_message.arg)
            except ValueError:
                return "Чтобы завершить задачу введите её индекс"
            if mark_done(user_id, task_serial):
                return ls(user_id)

        case "rmdir" | "уп":
            if parsed_message.arg == "":
                return "Название папки не может быть пустым"
            if parsed_message.arg == 'root':
                return "Вы не можете удалить корневую директорию"
            if res := remove_dir(user_id, parsed_message.arg):
                return res
            else:
                return ls(user_id)

        case "user":
            return get_user_by_id(user_id)
        case "test":
            pass

        case _:
            return f"{parsed_message.command} не является командой"
