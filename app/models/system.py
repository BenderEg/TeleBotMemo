from os import path, makedirs
from shutil import rmtree

from aiogram.filters.state import State, StatesGroup


class FSMmodel(StatesGroup):
    training = State()
    add = State()
    delete = State()
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
