# Работа с базой данных

import json
import os
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

users_db: Dict = {}


def load_database(db_file: str):
    """Загрузка базы данных из JSON файла"""
    global users_db
    if os.path.exists(db_file):
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Конвертируем ключи обратно в int
                users_db = {int(k): v for k, v in data.items()}
                logger.info(f"✅ База данных загружена: {len(users_db)} пользователей")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки БД: {e}")
            users_db = {}
    else:
        logger.info("📝 База данных не найдена, создана новая")
        users_db = {}


def save_database(db_file: str):
    """Сохранение базы данных в JSON файл"""
    try:
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(users_db, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 База данных сохранена: {len(users_db)} пользователей")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения БД: {e}")


def get_user_data(user_id: int, user_obj=None, db_file: str = None) -> Dict:
    """Получение данных пользователя, создание если не существует"""
    # Перезагружаем базу данных для получения актуальных данных
    if db_file and os.path.exists(db_file):
        load_database(db_file)
    
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': 0,
            'total_bets': 0,
            'total_wins': 0,
            'total_losses': 0,
            'games_played': 0,
            'history': [],
            'payments': [],  # История платежей для возврата
            'username': None,
            'first_name': None,
            'last_name': None
        }
        if db_file:
            save_database(db_file)
    
    # Добавляем поле payments, если его нет (для старых пользователей)
    if 'payments' not in users_db[user_id]:
        users_db[user_id]['payments'] = []
        if db_file:
            save_database(db_file)
    
    # Обновляем информацию о пользователе, если передан объект
    if user_obj:
        users_db[user_id]['username'] = user_obj.username
        users_db[user_id]['first_name'] = user_obj.first_name
        users_db[user_id]['last_name'] = user_obj.last_name
        if db_file:
            save_database(db_file)
    
    return users_db[user_id]


def get_all_users() -> Dict:
    """Получение всех пользователей"""
    return users_db


def update_user_balance(user_id: int, amount: int, db_file: str):
    """Изменение баланса пользователя"""
    if user_id in users_db:
        users_db[user_id]['balance'] += amount
        save_database(db_file)


def add_game_to_history(user_id: int, game_data: dict, db_file: str):
    """Добавление игры в историю пользователя"""
    if user_id in users_db:
        users_db[user_id]['history'].append(game_data)
        save_database(db_file)


def get_user_stats() -> dict:
    """Получение общей статистики по всем пользователям"""
    return {
        'total_users': len(users_db),
        'total_games': sum(u['games_played'] for u in users_db.values()),
        'total_bets': sum(u['total_bets'] for u in users_db.values()),
        'total_wins': sum(u['total_wins'] for u in users_db.values()),
        'total_losses': sum(u['total_losses'] for u in users_db.values())
    }
