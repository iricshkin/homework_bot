class ExpectedKeysError(Exception):
    """Ошибка ключей в ответе."""


class UnknownStatusError(Exception):
    """Недокументированный статус работы."""


class EmptyValueError(Exception):
    """Ошибка пустое значение"""


class TheAnswerStatusCodeNot200Error(Exception):
    """Ответ API не равен 200."""


class TheAnswerDictOrListError(Exception):
    """Ответ API имеет неверный тип данных."""
