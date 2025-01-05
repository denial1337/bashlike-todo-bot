import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import Command, CommandObject
import os
from aiogram.enums import ParseMode
import service
from aiogram import F

from db import get_user_by_id, get_directory_context, get_tasks
from service import parse_message, resolve_message
import db


api_token = os.environ['API_KEY']


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=api_token,
          default=DefaultBotProperties(
              parse_mode=ParseMode.MARKDOWN
          ))
# Диспетчер
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    #print(message)
    user_id = message.from_user.id
    username = message.from_user.username
    db.check_user(user_id, username)
    # await message.answer(f'HELLO {user_id}, {ans}')
    s = (f""
         f"Привет! Это BashLikeTODOBot! Он нужен для записи и хранения твоих задач.\n"
         f"Это бот исполнен в стиле командной строки.\n"
         f"Общение происходит посредством команд:\n"
         f"ls (list) - выводит содержимое текущей директории\n"
         f"mkdir (make dir) - создает новую дирректорию в текущей\n"
         f"cd (change dir) - переходит в указанную директорию\n"
         f"mktask - добавляет задачу в текущую директорию\n"
         f"done - помечает задачу как выполненную\n"
         f"Чтобы посмотреть примеры напиши /help")
    await message.answer(s)

@dp.message(Command("help"))
async def cmd_start(message: types.Message):
    s = (f"Изначально ты находишься в корневой директории root, чтобы убедится в этом введи ls\n"
         f"Чтобы создать папку внутри текущей(root) директории напиши mkdir <Имя папки>\n"
         f"Перейди в папку написав cd <Имя папки> и создай задачу task <Твоя задача>\n"
         f"Введи ls и ты увидешь содержмое текущей папки\n"
         f"Чтобы вернутся в корневой каталог используй cd, а если нужно вернутся в предыдущую папку cd ..")
    await message.answer(s)

@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    ans = parse_message(message.text)
    resolve_ans = resolve_message(message.text, user_id)
    #context = get_directory_context(user_id)
    tasks = get_tasks(user_id)
    if resolve_ans:
        await message.answer(f"{resolve_ans}")

@dp.message(Command("create"))
async def create(message: types.Message,
                 command: CommandObject):

    pass

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())