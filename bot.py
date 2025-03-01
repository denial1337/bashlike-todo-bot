import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import Command, CommandObject
import os
from aiogram.enums import ParseMode
import service
from aiogram import F
from dotenv import load_dotenv
from loguru import logger

from db import get_user_by_id, get_directory_context, get_tasks, check_db_exists
from service import parse_message, resolve_message
import db
from exception import MyException


load_dotenv()

api_token = os.environ["API_KEY"]

bot = Bot(token=api_token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

logger.remove()
logger.add("info.log", format="{time} {level} {message}", level="INFO", rotation="10 MB")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # print(message)
    user_id = message.from_user.id
    username = message.from_user.username
    await db.check_user(user_id, username)
    # await message.answer(f'HELLO {user_id}, {ans}')
    s = (
        f"Привет! Это BashLikeTODOBot! Он нужен для записи и хранения твоих задач.\n"
        f"Этот бот исполнен в стиле командной строки, общение происходит посредством текстовых команд."
        f"Полный список команд смотри в /help.\n"
        f"Для начала введи /start."
    )
    await message.answer(s)


@dp.message(Command("help"))
async def cmd_start(message: types.Message):
    s = (
        f"ls(че) - посмотреть список папок и задач внутри текущей директории\n"
        f"mkdir(сп) <Имя папки> - создать новую папку в текущей директории, название папки должно быть уникальным\n"
        f"cd(пп) <Имя папки> перейти в указанную папку \n"
        f"cd(пп) перейти в корневую директорию \n"
        f"cd(пп) .. перейти в предыдущую директорию \n"
        f"mktask(сз) <Твоя задача> - создать задачу в текущей папке\n"
        f"done(зз) <Номер задачи> - завершить задачу\n"
        f"tasks(вз) - посмотреть список активных задач\n"
        f"rmdir(уп) - удалить папку вместе с задачами в ней\n"
    )
    await message.answer(s)



@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    try:
        resolve_ans = await resolve_message(message.text, user_id)
    except MyException as e:
        logger.info(f'got MyException={str(e)}')
        await message.answer(str(e))
    except Exception as e:
        logger.info(f'got Exception={str(e)}')
        await message.answer(str(e))
    else:
        await message.answer(f"{resolve_ans}")


@dp.message(Command("create"))
async def create(message: types.Message, command: CommandObject):
    pass


# Запуск процесса поллинга новых апдейтов
async def main():
    await check_db_exists()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
