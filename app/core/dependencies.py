from typing import Annotated

from aiogram3_di import Depends

from services.add_service import AddService, get_add_service
from services.category_service import CategoryService, get_category_service
from services.csv_service import CsvService, get_csv_service
from services.del_service import DeleteService, get_delete_service
from services.learning_service import LearningService, get_learning_service
from services.user_service import UserService, get_user_service


user_service = Annotated[UserService, Depends(get_user_service)]
category_service = Annotated[CategoryService, Depends(get_category_service)]
add_service = Annotated[AddService, Depends(get_add_service)]
del_service = Annotated[DeleteService, Depends(get_delete_service)]
csv_service = Annotated[CsvService, Depends(get_csv_service)]
learning_service = Annotated[LearningService, Depends(get_learning_service)]