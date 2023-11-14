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