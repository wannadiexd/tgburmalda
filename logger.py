# Система логирования действий пользователей

import logging
from datetime import datetime
import json
import os

# Настройка логгера для действий пользователей
user_logger = logging.getLogger('user_actions')
user_logger.setLevel(logging.INFO)

# Создаем папку для логов если её нет
if not os.path.exists('logs'):
    os.makedirs('logs')

# Файловый обработчик - лог файл с датой
log_file = f"logs/users_{datetime.now().strftime('%Y-%m-%d')}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
user_logger.addHandler(file_handler)


def log_user_action(action: str, user_id: int, username: str = None, first_name: str = None, **kwargs):
    """
    Логирование действия пользователя
    
    Args:
        action: Тип действия (START, WIN, LOSS, REGISTER, etc.)
        user_id: ID пользователя
        username: Username пользователя
        first_name: Имя пользователя
        **kwargs: Дополнительные данные для логирования
    """
    user_info = f"ID:{user_id}"
    if username:
        user_info += f" @{username}"
    if first_name:
        user_info += f" ({first_name})"
    
    # Формируем дополнительные данные
    extra_info = ""
    if kwargs:
        extra_info = " | " + " | ".join([f"{k}:{v}" for k, v in kwargs.items()])
    
    log_message = f"{action:15} | {user_info}{extra_info}"
    user_logger.info(log_message)


# Удобные функции для частых действий

def log_start(user_id: int, username: str = None, first_name: str = None):
    """Пользователь запустил бота"""
    log_user_action("START", user_id, username, first_name)


def log_register(user_id: int, username: str = None, first_name: str = None):
    """Новый пользователь зарегистрировался"""
    log_user_action("REGISTER", user_id, username, first_name)


def log_game_start(user_id: int, game: str, bet_type: str, amount: int, username: str = None):
    """Начало игры"""
    log_user_action("GAME_START", user_id, username, 
                   game=game, bet=bet_type, amount=f"{amount}⭐")


def log_win(user_id: int, game: str, bet_type: str, amount: int, winnings: int, username: str = None):
    """Выигрыш"""
    log_user_action("WIN", user_id, username,
                   game=game, bet=bet_type, bet_amount=f"{amount}⭐", 
                   winnings=f"{winnings}⭐", profit=f"+{winnings-amount}⭐")


def log_loss(user_id: int, game: str, bet_type: str, amount: int, username: str = None):
    """Проигрыш"""
    log_user_action("LOSS", user_id, username,
                   game=game, bet=bet_type, amount=f"{amount}⭐")


def log_payment(user_id: int, amount: int, payment_id: str, username: str = None):
    """Платеж через Stars"""
    log_user_action("PAYMENT", user_id, username,
                   amount=f"{amount}⭐", payment_id=payment_id[:20])


def log_balance_change(user_id: int, old_balance: int, new_balance: int, reason: str, username: str = None):
    """Изменение баланса"""
    change = new_balance - old_balance
    log_user_action("BALANCE_CHANGE", user_id, username,
                   reason=reason, old=f"{old_balance}⭐", 
                   new=f"{new_balance}⭐", change=f"{change:+d}⭐")


def log_refund(user_id: int, amount: int, payment_id: str, username: str = None):
    """Возврат платежа"""
    log_user_action("REFUND", user_id, username,
                   amount=f"{amount}⭐", payment_id=payment_id[:20])


def log_admin_action(admin_id: int, action: str, target_user_id: int = None, **kwargs):
    """Действие администратора"""
    extra = f"target_user:{target_user_id}" if target_user_id else ""
    if kwargs:
        extra += " | " + " | ".join([f"{k}:{v}" for k, v in kwargs.items()])
    log_user_action(f"ADMIN_{action}", admin_id, extra_info=extra)


def log_error(user_id: int, error: str, username: str = None):
    """Ошибка при действии пользователя"""
    log_user_action("ERROR", user_id, username, error=error)


def get_today_stats():
    """Получить статистику за сегодня из логов"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        stats = {
            'total_actions': len(lines),
            'starts': sum(1 for line in lines if 'START' in line),
            'registers': sum(1 for line in lines if 'REGISTER' in line),
            'games': sum(1 for line in lines if 'GAME_START' in line),
            'wins': sum(1 for line in lines if 'WIN' in line and 'GAME' not in line),
            'losses': sum(1 for line in lines if 'LOSS' in line),
            'payments': sum(1 for line in lines if 'PAYMENT' in line),
            'refunds': sum(1 for line in lines if 'REFUND' in line),
        }
        return stats
    except FileNotFoundError:
        return None
