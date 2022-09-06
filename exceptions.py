class TokenNotFoundError(Exception):
    """Отсутствует хотя бы одна переменная окружения."""


class HomeworkStatusError(Exception):
    """Недокоументированный статут домашней работы."""


class UnsuccessfulStatusCode(Exception):
    """Статус ответа сервера не 200."""


class APIAnswerError(Exception):
    """Ошибка при запросе к API."""


class HomeworkEmptyListError(Exception):
    """Cписок домашних работ пуст."""


class NoNewStatusesError(Exception):
    """Отсутствие в ответе новых статусов."""
