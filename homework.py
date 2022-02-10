import logging
import os
import time
from json import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    EmptyValueError,
    ExpectedKeysError,
    TheAnswerStatusCodeNot200Error,
    UnknownStatusError,
)

load_dotenv(override=True)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')


RETRY_TIME = 600
# ENDPOINT = 'https://practicum.yandex.ru/api/user_api/'
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Сообщение в Telegram отправлено: {message}')
    except telegram.error.TelegramError as telegram_error:
        logger.error(f'Сообщение в Telegram не отправлено: {telegram_error}')


def get_api_answer(current_timestamp):
    """Получение данных с API сервиса Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    # timestamp = 0 #убрать
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            api_error_msg = f'Неверный код ответа API: {response.status_code}'
            logger.error(api_error_msg)
            raise TheAnswerStatusCodeNot200Error(api_error_msg)
        return response.json()
    except requests.exceptions.RequestException as request_error:
        logging.error(f'Код ответа API: {request_error}')
        raise SystemExit(request_error)
    except JSONDecodeError as json_error:
        logging.error(f'Ошибка полученных данных: {json_error}')


def check_response(response):
    """Проверка ответа API на корректность."""
    if response['homeworks'] is None:
        api_error_msg = 'Отсутсвуют ожидаемые ключи в ответе API'
        logging.error(api_error_msg)
        raise ExpectedKeysError(api_error_msg)
    if response['homeworks'] == []:
        return {}
    # Проверить, что вернулись все ключи ('homework_name' и 'status')
    return response['homeworks'][0]


def parse_status(homework):
    """Информация о статусе домашней работы."""
    homework_name = homework.get('homework_name') or None
    homework_status = homework.get('status')
    if homework_name is None:
        name_error_msg = f'Отсутсвует значение homework_name: {homework_name}'
        logger.error(name_error_msg)
        raise EmptyValueError(name_error_msg)
    if homework_status is None:
        status_error_msg = f'Отсутсвует значение status: {homework_status}'
        logger.error(status_error_msg)
        raise EmptyValueError(name_error_msg)
    if homework_status not in HOMEWORK_STATUSES:
        api_error_msg = f'Недокументированный статус: {homework_status}'
        logger.error(api_error_msg)
        raise UnknownStatusError(api_error_msg)

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}".\n{verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    stop_bot_msg = 'Программа принудительно остановлена.'
    tokens_error_msg = 'Отсутствует обязательная переменная окружения:'
    tokens_status = True
    if PRACTICUM_TOKEN is None:
        tokens_status = False
        logger.critical(f'{tokens_error_msg} PRACTICUM_TOKEN.\n{stop_bot_msg}')
    if TELEGRAM_TOKEN is None:
        tokens_status = False
        logger.critical(f'{tokens_error_msg} TELEGRAM_TOKEN.\n{stop_bot_msg}')
    if TELEGRAM_CHAT_ID is None:
        tokens_status = False
        logger.critical(
            f'{tokens_error_msg} TELEGRAM_CHAT_ID.\n{stop_bot_msg}'
        )
    return tokens_status


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_status = 'reviewing'
    errors = True
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework and current_status != homework['status']:
                message = parse_status(homework)
                send_message(bot, message)
                current_status = homework['status']
                current_timestamp = response['current_date']
                time.sleep(RETRY_TIME)
            logger.debug('Пока изменений нет. Новый запрос через 10 минут.')
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)

        except KeyboardInterrupt:
            stop_bot = input(
                'Вы действительно хотите остановить работу бота? Y/N: '
            )
            if stop_bot in ('Y', 'y'):
                print('До встречи!')
                break
            elif stop_bot in ('N', 'n'):
                print('Продолжаем работать!')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if errors:
                errors = False
                send_message(bot, message)
            logger.critical(message)
            time.sleep(RETRY_TIME)
        else:
            logger.debug('Программа работает без ошибок!')


if __name__ == '__main__':
    main()