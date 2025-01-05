import db
from db import get_cursor, create_directory, get_directory_context, create_task, change_dir, change_dir_to_root, \
    get_all_tasks, change_dir_to_meta, get_user_by_id
from typing import NamedTuple, List, Type, Optional

COMMANDS = [
    'ls', 'cd', 'mktask', 'rmtask', 'tasks', 'mkdir', 'fdir', 'done', 'pwd', 'rmdir', 'user'
]

class ParsedMessage(NamedTuple):
    command: str
    #options: List[str]
    arg: str | None

def parse_message(message: str) -> ParsedMessage | str:
    splited = message.split()
    if (command := splited[0].lower()) not in COMMANDS:
        return f'{command} is not a command'

    parsed_message = ParsedMessage(command=command, arg=message[len(splited[0]) + 1:])
    return parsed_message

def ls(user_id):
    return '```' + get_directory_context(user_id) + '```'

def resolve_message(message: str, user_id: int) -> str | None:
    parsed_message = parse_message(message)
    if isinstance(parsed_message, str):
        return parsed_message
    match parsed_message.command:
        case 'mkdir':
            if parsed_message.arg == '':
                return 'Название папки не может быть пустым'
            create_directory(parsed_message.arg, user_id)
            return ls(user_id)
        case 'ls':
            return ls(user_id)
        case 'mktask':
            if parsed_message.arg == '':
                return 'Название задачи не может быть пустым'
            create_task(parsed_message.arg, user_id)
            return ls(user_id)
            #return f"{parsed_message.arg} added"
        case 'tasks':
            tasks = get_all_tasks(user_id)
            if tasks is None:
                return 'Нет задач'
            return '```' + tasks + '```'
        case 'cd':
            if parsed_message.arg == '..':
                change_dir_to_meta(user_id)
            if parsed_message.arg == '':
                change_dir_to_root(user_id)
            change_dir(user_id, parsed_message.arg)
            return ls(user_id)

        case 'user':
            return get_user_by_id(user_id)




