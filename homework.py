import logging
import os
import time
from asyncio.log import logger
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot, TelegramError

from exceptions import (APIAnswerError, HomeworkEmptyListError,
                        HomeworkStatusError, NoNewStatusesError,
                        TokenNotFoundError, UnsuccessfulStatusCode)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('SECRET_PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_BOT')
TELEGRAM_CHAT_ID = os.getenv('MY_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: Bot, message: str) -> None:
    """Отправка сообщения в Telegram чат."""
    try:
        logger.debug('Попытка отправки сообщения в Telegram')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError:
        raise TelegramError(
            'Сбой при отправке сообщения в Telegram'
        )


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос к API-сервиса Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.ConnectionError:
        raise APIAnswerError(
            'Произошла ошибка при запросе к API.'
        )
    except requests.exceptions.HTTPError:
        raise APIAnswerError(
            'Произошла ошибка при запросе к API.'
        )
    except requests.exceptions.Timeout:
        raise APIAnswerError(
            'Произошла ошибка при запросе к API.'
        )
    except Exception as e:
        raise e

    if response.status_code != HTTPStatus.OK:
        raise UnsuccessfulStatusCode(
            'Статус ответа сервера не 200: '
            f'Статус ответа {response.status_code}'
        )

    return response.json()


def check_response(response: dict) -> list:
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('API вернул неверный тип данных')
    elif 'homeworks' not in response:
        raise KeyError('Отсутствие ожидаемых ключей словаря в ответе API')
    elif not isinstance(response['homeworks'], list):
        raise TypeError('API вернул неверный тип данных')
    return response.get('homeworks')


def parse_status(homework: dict) -> str:
    """Извлечение статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if not isinstance(homework, dict):
        raise TypeError('API вернул неверный тип данных')
    if homework_name is None:
        raise KeyError('Отсутствие ожидаемых ключей словаря в ответе API')
    if homework_status is None:
        raise KeyError('Отсутствие ожидаемых ключей словаря в ответе API')
    if homework_status not in HOMEWORK_VERDICTS:
        raise HomeworkStatusError(
            'Обнаружен недокументированный статус домашней работы,'
            'в ответе API'
        )

    verdict = HOMEWORK_VERDICTS.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(tokens)


def main() -> None:
    """Основная логика работы бота."""
    # Создаём и настраиваем логгер
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info('Запуск бота')

    if not check_tokens():
        logger.critical('Отсутствует хотя бы одна переменная окружения')
        raise TokenNotFoundError(
            'Отсутствует хотя бы одна переменная окружения'
        )

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    error = None
    current_status = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if len(homework) == 0:
                raise HomeworkEmptyListError
            new_status = homework[0].get('status')
            if new_status == current_status:
                raise NoNewStatusesError
            message = parse_status(homework[0])
            current_status = new_status
            send_message(bot, message)
            logger.info('Сообщение отправлено в Telegram')
            current_timestamp = response.get('current_date')

        except HomeworkEmptyListError:
            logger.debug('Cписок домашних работ пуст')

        except NoNewStatusesError:
            logger.debug('Отсутствие в ответе новых статусов')

        except Exception as new_error:
            message = f'Сбой в работе программы: {new_error}'
            logger.error(message)
            if error != new_error:
                error = new_error
                send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
