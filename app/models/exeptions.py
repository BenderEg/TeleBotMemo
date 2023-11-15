class CsvReadExeption(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.msg = 'Ошибка чтения файла'

class ServerErrorExeption(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.msg = 'Произошла ошибка на стороне сервера.\n\
Поддержка была уведомлена о проишедшей ошибке. Мы примем меры для ее устранения.\n\
Несохраненные данные могут быть утеряны.'