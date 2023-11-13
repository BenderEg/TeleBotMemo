from aiogram import Bot
from aiogram.types import BotCommand

async def set_main_menu(bot: Bot):

    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command='/list_all',
                   description='Вывод всех объектов'),
        BotCommand(command='/add',
                   description='Добавление объектов'),
        BotCommand(command='/delete',
                   description='Удаление объектов'),
        BotCommand(command='/training',
                   description='Режим тренировки'),
        BotCommand(command='/learn',
                   description='Режим изучения'),
        BotCommand(command='/add_category',
                   description='Добавление категории для хранения объектов'),
        BotCommand(command='/choose_category',
                   description='Выбор категории'),
        BotCommand(command='/help',
                   description='Справка по работе бота'),
        BotCommand(command='/cancel',
                   description='Для выхода из режима'),
            ]
    await bot.set_my_commands(main_menu_commands)
