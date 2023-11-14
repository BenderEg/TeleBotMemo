from random import choice

from aiogram.types import Message
from sortedcontainers import SortedList

from services.base_service import BaseService

class LearningService(BaseService):

    def _group_by_categories(self, lst: list) -> dict:
        d = {}
        for ele in lst:
            if ele['category'] not in d:
                d[ele['category']] = SortedList([(ele['object'], ele['meaning'])])
            else:
                d[ele['category']].add((ele['object'], ele['meaning']))
        return d

    def list_learning_pool(self, lst: list) -> str:

        d = self._group_by_categories(lst)
        res = ''
        for key, value in d.items():
            header = f'<b>{key}:\n\n</b>'.upper()
            objects = '\n======================\n'.join(
                f"{i}. {choice((self._get_view_internal_1, self._get_view_internal_2))(ele, ' = ')}."
                if i == len(value)
                else f"{i}. {choice((self._get_view_internal_1, self._get_view_internal_2))(ele, ' = ')};"
                for i, ele in enumerate(value, 1))
            res += header + objects + '\n\n'
        return res

    def _get_view_internal_1(self, ele: dict, sep: str = "\n -------------------\n"):

        return f"{ele[0]}{sep}<tg-spoiler>{ele[1]}</tg-spoiler>"


    def _get_view_internal_2(self, ele: dict, sep: str = "\n -------------------\n"):

        return f"{ele[1]}{sep}<tg-spoiler>{ele[0]}</tg-spoiler>"

    def list_all_data(self, lst: list) -> str:

        d = self._group_by_categories(lst)
        res = ''
        for key, value in d.items():
            header = f'<b>{key}:\n\n</b>'.upper()
            objects = '\n'.join(f"{i}. <b>{ele[0]}</b> = {ele[1]}."
                            if i == len(value)
                            else f"{i}. <b>{ele[0]}</b> = {ele[1]};"
                            for i, ele in enumerate(value, 1))
            res += header + objects + '\n\n'
        return res

    async def message_paginator(self, text: str, message: Message) -> str:
        i = 0
        while i < len(text):
            current_text = text[i:i+4000]
            text_length = len(current_text)
            j = text_length - 1
            if 0 < text_length < 4000:
                await message.answer(text=current_text,
                                     parse_mode='html')
                break
            elif text_length == 0:
                break
            else:
                while current_text[j] != '\n':
                    j -= 1
                result = text[i:i+j+1]
                await message.answer(text=result,
                                     parse_mode='html')
                i += j+1