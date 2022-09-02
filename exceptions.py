class TokenNotFoundError(Exception):
    """Отсутствует хотя бы одна переменная окружения."""


class HomeworkStatusError(Exception):
    """Недокоументированный статут домашней работы."""


class UnsuccessfulStatusCode(Exception):
    """Статус ответа сервера не 200."""
