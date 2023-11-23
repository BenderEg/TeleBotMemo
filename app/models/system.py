from os import path, makedirs
from shutil import rmtree

from aiogram.filters.state import State, StatesGroup


class FSMmodel(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    training = State()        # Состояние тренировки
    add = State()  # Состояние добавления объектов
    delete = State()  # Состояние удаления объектов
    add_category = State()
    choose_category = State()

class FileHandler():

    def __init__(self, chat: str, name: str) -> None:

        self.name = name
        self.chat = chat
        self.file_path = None

    def __enter__(self):

        output_folder = path.join('temp', str(self.chat))
        if not path.exists(output_folder):
            makedirs(output_folder, exist_ok=True)
        self.file_path = output_folder
        return output_folder

    def __exit__(self, *args):
        rmtree(self.file_path)
        return False
