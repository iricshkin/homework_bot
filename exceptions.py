class ExpectedKeysError(Exception):
    """Ошибка ключей в ответе."""


class EmptyValueError(Exception):
    """Ошибка пустое значение"""


class TheAnswerStatusCodeNot200Error(Exception):
    """Ответ API не равен 200."""


class TheAnswerListError(Exception):
    """Ответ API имеет неверный тип данных."""
