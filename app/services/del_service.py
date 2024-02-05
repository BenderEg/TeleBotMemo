from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.postgres import db_session
from services.base_service import BaseService

class DeleteService(BaseService):

    def create_delete_builder(
            self, objects: list) -> InlineKeyboardBuilder:
        builder = InlineKeyboardBuilder()
        for ele in objects:
            button_text = f"{ele['object']} = {ele['meaning']}"
            if len(button_text) > 30:
                button_text = f'{button_text[:30]}...'
            builder.button(text=button_text,
                           callback_data=f"{ele['id']}")
        builder.adjust(1)
        return builder

    def filter_objects(self, objects: list, target_id: str) -> tuple:
        target_object = None
        filtered_objects = []
        for ele in objects:
            if ele['id'] == target_id:
                target_object = ele
            else:
                filtered_objects.append(ele)
        return target_object, filtered_objects


async def get_delete_service(db: db_session) -> DeleteService:
    return DeleteService(db)