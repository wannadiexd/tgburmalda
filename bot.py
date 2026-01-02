import asyncio
import logging
from datetime import datetime
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Импорты из наших модулей
from config import TOKEN, ADMIN_ID, DB_FILE
from database import (
    load_database, save_database, get_user_data, 
    get_all_users, get_user_stats
)
from keyboards import (
    get_main_keyboard, get_admin_keyboard, get_games_keyboard,
    get_bet_options_keyboard, get_bet_amounts_keyboard,
    get_game_result_keyboard, get_back_button, get_reply_keyboard,
    get_profile_keyboard, get_deposit_keyboard, get_cancel_keyboard,
    get_games_reply_keyboard, get_profile_reply_keyboard, get_deposit_amounts_keyboard,
    get_cancel_reply_keyboard, get_bet_type_keyboard, get_bet_amount_keyboard
)
from game_logic import determine_game_result, get_rules_text
from logger import (
    log_start, log_register, log_game_start, log_win, log_loss,
    log_payment, log_balance_change, log_refund, log_admin_action,
    get_today_stats
)
from web_server import start_web_server

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Роутер и состояния
router = Router()

# Хранилище для последних сообщений бота (user_id: [message_ids])
last_bot_messages = {}

class BetStates(StatesGroup):
    waiting_payment = State()
    waiting_withdraw_amount = State()
    waiting_deposit_amount = State()


async def delete_last_message(user_id: int, bot: Bot):
    """Удаляет все последние сообщения бота для пользователя"""
    if user_id in last_bot_messages:
        for message_id in last_bot_messages[user_id]:
            try:
                await bot.delete_message(chat_id=user_id, message_id=message_id)
            except:
                pass
        del last_bot_messages[user_id]
        # Небольшая задержка для анимации удаления
        await asyncio.sleep(0.15)


async def save_message_id(user_id: int, message_id: int):
    """Сохраняет ID последнего сообщения бота"""
    if user_id not in last_bot_messages:
        last_bot_messages[user_id] = []
    last_bot_messages[user_id].append(message_id)


async def clear_message_ids(user_id: int):
    """Очищает список сообщений без удаления"""
    if user_id in last_bot_messages:
        del last_bot_messages[user_id]


@router.message(CommandStart())
async def cmd_start(msg: Message, bot: Bot):
    """Команда /start"""
    users_db = get_all_users()
    is_new_user = msg.from_user.id not in users_db
    
    get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
    
    # Логирование
    if is_new_user:
        log_register(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    else:
        log_start(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    
    # Удаляем только предыдущее сообщение бота
    await delete_last_message(msg.from_user.id, bot)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text=f"🎰 Добро пожаловать, {msg.from_user.first_name}!\n\n"
        f"Делай ставки в Telegram Stars ⭐ и выигрывай! 🍀\n\n"
        f"Выбери действие:",
        reply_markup=get_reply_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)


@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    """Админ-панель"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    log_admin_action(msg.from_user.id, "PANEL_OPEN")
    
    stats = get_user_stats()
    today_stats = get_today_stats()
    
    today_info = ""
    if today_stats:
        today_info = (
            f"\n📊 Сегодня:\n"
            f"   Новых: {today_stats['registers']} | "
            f"Игр: {today_stats['games']} | "
            f"Выигрышей: {today_stats['wins']}\n"
        )
    
    await msg.answer(
        f"👑 АДМИН ПАНЕЛЬ\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🎮 Игр: {stats['total_games']}\n"
        f"💰 Ставок: {stats['total_bets']} ⭐\n"
        f"🏆 Выплат: {stats['total_wins']} ⭐\n"
        f"📈 Прибыль: {stats['total_bets'] - stats['total_wins']} ⭐"
        f"{today_info}\n"
        f"📋 Команды:\n"
        f"/stats [user_id] - статистика\n"
        f"/setbalance [user_id] [сумма]\n"
        f"/addbalance [user_id] [сумма]\n"
        f"/refund [user_id] [payment_id]\n"
        f"/logs - логи за сегодня",
        reply_markup=get_admin_keyboard()
    )


@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    """Статистика пользователя"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    try:
        uid = int(msg.text.split()[1])
        users_db = get_all_users()
        if uid not in users_db:
            return await msg.answer("❌ Не найден")
        
        ud = users_db[uid]
        txt = (
            f"📊 Статистика {uid}\n\n"
            f"💳 Баланс: {ud['balance']} ⭐\n"
            f"🎮 Игр: {ud['games_played']}\n"
            f"💰 Ставок: {ud['total_bets']} ⭐\n"
            f"🏆 Выигрышей: {ud['total_wins']} ⭐\n"
            f"💸 Проигрышей: {ud['total_losses']} ⭐\n\n"
            f"📜 История:\n"
        )
        
        for g in ud['history'][-10:][::-1]:
            r = "✅" if g['win'] else "❌"
            rf = " [ВОЗВРАТ]" if g.get('refunded') else ""
            txt += f"{r} {g['game']} {g['bet_type']} {g['winnings']:+d} ⭐{rf}\n   ID: {g.get('payment_id', 'N/A')[:20]}...\n"
        
        await msg.answer(txt)
    except:
        await msg.answer("❌ Формат: /stats [user_id]")


@router.message(Command("setbalance"))
async def cmd_setbalance(msg: Message, bot: Bot):
    """Установить баланс пользователя"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    try:
        p = msg.text.split()
        if len(p) != 3:
            return await msg.answer("❌ Формат: /setbalance [user_id] [количество]")
        
        uid, amount = int(p[1]), int(p[2])
        ud = get_user_data(uid)
        old_balance = ud['balance']
        ud['balance'] = amount
        save_database(DB_FILE)
        
        # Логирование
        users_db = get_all_users()
        username = users_db[uid].get('username')
        log_balance_change(uid, old_balance, amount, "admin_set", username)
        log_admin_action(msg.from_user.id, "SET_BALANCE", uid, 
                        old=f"{old_balance}⭐", new=f"{amount}⭐")
        
        await msg.answer(
            f"✅ Баланс изменен!\n\n"
            f"👤 User ID: {uid}\n"
            f"💰 Было: {old_balance} ⭐\n"
            f"💳 Стало: {amount} ⭐\n"
            f"📊 Изменение: {amount - old_balance:+d} ⭐"
        )
        
        try:
            await bot.send_message(
                uid,
                f"💫 Ваш баланс изменен администратором\n\n"
                f"💰 Было: {old_balance} ⭐\n"
                f"💳 Стало: {amount} ⭐"
            )
        except:
            pass
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("addbalance"))
async def cmd_addbalance(msg: Message, bot: Bot):
    """Добавить к балансу пользователя"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    try:
        p = msg.text.split()
        if len(p) != 3:
            return await msg.answer("❌ Формат: /addbalance [user_id] [количество]")
        
        uid, amount = int(p[1]), int(p[2])
        ud = get_user_data(uid)
        old_balance = ud['balance']
        ud['balance'] += amount
        save_database(DB_FILE)
        
        # Логирование
        users_db = get_all_users()
        username = users_db[uid].get('username')
        log_balance_change(uid, old_balance, ud['balance'], "admin_add", username)
        log_admin_action(msg.from_user.id, "ADD_BALANCE", uid, 
                        amount=f"{amount:+d}⭐", new_balance=f"{ud['balance']}⭐")
        
        await msg.answer(
            f"✅ Баланс изменен!\n\n"
            f"👤 User ID: {uid}\n"
            f"💰 Было: {old_balance} ⭐\n"
            f"💳 Стало: {ud['balance']} ⭐\n"
            f"📊 Добавлено: {amount:+d} ⭐"
        )
        
        try:
            await bot.send_message(
                uid,
                f"💫 Вам начислено {amount} ⭐\n\n"
                f"💰 Было: {old_balance} ⭐\n"
                f"💳 Стало: {ud['balance']} ⭐"
            )
        except:
            pass
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("refund"))
async def cmd_refund(msg: Message, bot: Bot):
    """Возврат платежа"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    try:
        p = msg.text.split()
        if len(p) != 3:
            return await msg.answer("❌ Формат: /refund [user_id] [payment_id]")
        
        uid, pid = int(p[1]), p[2]
        users_db = get_all_users()
        
        if uid not in users_db:
            return await msg.answer(f"❌ Пользователь {uid} не найден")
        
        ud = users_db[uid]
        tx = next((g for g in ud['history'] if g.get('payment_id') == pid), None)
        
        if not tx:
            return await msg.answer(f"❌ Транзакция не найдена")
        
        if tx.get('refunded'):
            return await msg.answer(f"❌ Уже возвращен: {tx.get('refund_date')}")
        
        await bot.refund_star_payment(user_id=uid, telegram_payment_charge_id=pid)
        
        if tx['win']:
            ud['balance'] -= tx['winnings']
            ud['total_wins'] -= tx['winnings']
        
        tx['refunded'] = True
        tx['refund_date'] = datetime.now().isoformat()
        save_database(DB_FILE)
        
        # Логирование
        username = ud.get('username')
        log_refund(uid, tx['amount'], pid, username)
        log_admin_action(msg.from_user.id, "REFUND", uid, 
                        amount=f"{tx['amount']}⭐", game=tx['game'])
        
        await msg.answer(
            f"✅ Возврат выполнен!\n"
            f"👤 {uid}\n"
            f"💰 {tx['amount']} ⭐\n"
            f"🎮 {tx['game']} - {tx['bet_type']}"
        )
        
        try:
            await bot.send_message(uid, f"💫 Возврат {tx['amount']} ⭐\n{tx['game']} - {tx['bet_type']}")
        except:
            pass
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(Command("users"))
async def cmd_users(msg: Message):
    """Список всех пользователей"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    users_db = get_all_users()
    if not users_db:
        return await msg.answer("📭 Пользователей пока нет")
    
    sorted_users = sorted(users_db.items(), key=lambda x: x[1]['games_played'], reverse=True)
    txt = f"👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ ({len(users_db)})\n\n"
    
    for uid, data in sorted_users:
        username = f"@{data.get('username')}" if data.get('username') else "—"
        first_name = data.get('first_name', '—')
        last_name = data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip() if last_name else first_name
        
        txt += (
            f"👤 {full_name}\n"
            f"   ID: {uid}\n"
            f"   Username: {username}\n"
            f"   💳 Баланс: {data['balance']} ⭐\n"
            f"   🎮 Игр: {data['games_played']}\n\n"
        )
        
        if len(txt) > 3500:
            await msg.answer(txt)
            txt = ""
    
    if txt:
        await msg.answer(txt)


@router.message(Command("logs"))
async def cmd_logs(msg: Message):
    """Просмотр логов за сегодня"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    log_admin_action(msg.from_user.id, "VIEW_LOGS")
    
    stats = get_today_stats()
    if not stats:
        return await msg.answer("📭 Логов за сегодня пока нет")
    
    txt = (
        f"📊 СТАТИСТИКА ЗА СЕГОДНЯ\n\n"
        f"📝 Всего действий: {stats['total_actions']}\n"
        f"🆕 Регистраций: {stats['registers']}\n"
        f"▶️ Запусков бота: {stats['starts']}\n"
        f"🎮 Игр начато: {stats['games']}\n"
        f"✅ Выигрышей: {stats['wins']}\n"
        f"❌ Проигрышей: {stats['losses']}\n"
        f"💳 Платежей: {stats['payments']}\n"
        f"↩️ Возвратов: {stats['refunds']}\n\n"
        f"📁 Файл: logs/users_{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    
    await msg.answer(txt)
    
    # Отправляем последние 15 записей лога
    try:
        log_file = f"logs/users_{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if lines:
            last_lines = lines[-15:]  # Последние 15 записей
            log_text = "📋 Последние 15 действий:\n\n```\n" + "".join(last_lines) + "```"
            await msg.answer(log_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка чтения лога: {e}")
    
    await msg.answer(txt)


@router.message(Command("deposit"))
async def cmd_deposit(msg: Message):
    """Команда пополнения"""
    await msg.answer(
        "💰 Пополнение баланса\n\n"
        "Доступные суммы:\n"
        "⭐ 1, 5, 10, 25, 50, 100, 250 Stars\n\n"
        "Напиши сумму числом (например: 50)\n"
        "Или используй команду:\n"
        "/pay [сумма]"
    )


@router.message(Command("withdraw"))
async def cmd_withdraw(msg: Message, state: FSMContext):
    """Команда вывода"""
    ud = get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
    
    if ud['balance'] < 1:
        return await msg.answer("❌ Недостаточно средств для вывода")
    
    await msg.answer(
        f"💸 Вывод средств\n\n"
        f"💳 Доступно: {ud['balance']} ⭐\n\n"
        f"Введи сумму для вывода:"
    )
    await state.set_state(BetStates.waiting_withdraw_amount)


@router.message(F.text == "🎮 Играть")
async def text_play(msg: Message, bot: Bot):
    """Текстовая команда Играть"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text="🎮 Выбери игру:",
        reply_markup=get_games_reply_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)


@router.message(F.text == "👤 Профиль")
async def text_profile(msg: Message, bot: Bot):
    """Текстовая команда Профиль"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    ud = get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
    
    # Подсчет выигрышных и проигрышных игр
    wins_count = sum(1 for g in ud['history'] if g['win'])
    losses_count = sum(1 for g in ud['history'] if not g['win'])
    wr = (wins_count / ud['games_played'] * 100) if ud['games_played'] > 0 else 0
    
    txt = (
        f"👤 Профиль\n\n"
        f"💳 Баланс: {ud['balance']} ⭐\n"
        f"🎮 Всего игр: {ud['games_played']}\n"
        f"✅ Выигрышей: {wins_count} игр ({wr:.1f}%)\n"
        f"❌ Проигрышей: {losses_count} игр\n"
        f"💰 Всего ставок: {ud['total_bets']} ⭐"
    )
    
    if ud['history']:
        txt += "\n\n📜 Последние 5:\n" + "\n".join(
            f"{'✅' if g['win'] else '❌'} {g['game']} {g['bet_type']} {g['winnings']:+d} ⭐"
            for g in ud['history'][-5:][::-1]
        )
    
    await delete_last_message(msg.from_user.id, bot)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text=txt,
        reply_markup=get_profile_reply_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)


@router.message(F.text == "ℹ️ Правила")
async def text_rules(msg: Message, bot: Bot):
    """Текстовая команда Правила"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text=get_rules_text(),
        reply_markup=get_reply_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)


@router.message(F.text.in_(["🏀 Баскетбол", "🎲 Кости", "⚽ Футбол", "🎯 Дартс", "🎳 Боулинг"]))
async def game_selected(msg: Message, state: FSMContext, bot: Bot):
    """Выбор игры через Reply клавиатуру"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    game = msg.text.split()[0]  # Берем только эмодзи
    
    if game == '🏀':
        txt = f"{game} Баскетбол\n\nВыбери тип ставки:"
    elif game == '🎲':
        txt = f"{game} Кости\n\nВыбери тип ставки:"
    elif game == '⚽':
        txt = f"{game} Футбол\n\nВыбери тип ставки:"
    elif game == '🎯':
        txt = f"{game} Дартс\n\nВыбери тип ставки:"
    elif game == '🎳':
        txt = f"{game} Боулинг\n\nВыбери тип ставки:"
    
    await state.update_data(selected_game=game)
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text=txt,
        reply_markup=get_bet_type_keyboard(game)
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)


@router.message(F.text == "◀️ Назад")
async def back_to_main(msg: Message, state: FSMContext, bot: Bot):
    """Вернуться назад (контекстная кнопка)"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    data = await state.get_data()
    game = data.get('selected_game')
    bet_type = data.get('selected_bet_type')
    
    # Если выбрана сумма - возвращаемся к выбору типа ставки
    if game and bet_type:
        await state.update_data(selected_bet_type=None)
        
        if game == '🏀':
            txt = f"{game} Баскетбол\n\nВыбери тип ставки:"
        elif game == '🎲':
            txt = f"{game} Кости\n\nВыбери тип ставки:"
        elif game == '⚽':
            txt = f"{game} Футбол\n\nВыбери тип ставки:"
        elif game == '🎯':
            txt = f"{game} Дартс\n\nВыбери тип ставки:"
        elif game == '🎳':
            txt = f"{game} Боулинг\n\nВыбери тип ставки:"
        
        sent_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text=txt,
            reply_markup=get_bet_type_keyboard(game)
        )
        await save_message_id(msg.from_user.id, sent_msg.message_id)
    
    # Если выбрана только игра - возвращаемся к выбору игр
    elif game:
        await state.clear()
        sent_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text="🎮 Выбери игру:",
            reply_markup=get_games_reply_keyboard()
        )
        await save_message_id(msg.from_user.id, sent_msg.message_id)
    
    # Если ничего не выбрано - возвращаемся в главное меню
    else:
        await state.clear()
        sent_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text="🎰 Главное меню",
            reply_markup=get_reply_keyboard()
        )
        await save_message_id(msg.from_user.id, sent_msg.message_id)


@router.message(F.text.in_(["💰 Пополнить", "💸 Вывод"]))
async def profile_actions(msg: Message, state: FSMContext, bot: Bot):
    """Действия из профиля"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    if msg.text == "💰 Пополнить":
        sent_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text="💰 Пополнение баланса\n\n"
            "Выбери сумму:",
            reply_markup=get_deposit_amounts_keyboard()
        )
        await save_message_id(msg.from_user.id, sent_msg.message_id)
    elif msg.text == "💸 Вывод":
        ud = get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
        if ud['balance'] < 1:
            sent_msg = await bot.send_message(
                chat_id=msg.from_user.id,
                text="❌ Недостаточно средств для вывода",
                reply_markup=get_profile_reply_keyboard()
            )
            await save_message_id(msg.from_user.id, sent_msg.message_id)
            return
        
        sent_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text=f"💸 Вывод средств\n\n"
            f"💳 Доступно: {ud['balance']} ⭐\n\n"
            f"Введи сумму для вывода:",
            reply_markup=get_cancel_reply_keyboard()
        )
        await save_message_id(msg.from_user.id, sent_msg.message_id)
        await state.set_state(BetStates.waiting_withdraw_amount)


@router.message(F.text.startswith("⭐ "))
async def deposit_amount_selected(msg: Message, bot: Bot, state: FSMContext):
    """Выбор фиксированной суммы пополнения"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    try:
        amount = int(msg.text.replace("⭐ ", ""))
        await delete_last_message(msg.from_user.id, bot)
        
        status_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text=f"💳 Ожидаем оплату {amount} ⭐\n\nСчет отправлен ниже ⬇️",
            reply_markup=get_cancel_reply_keyboard()
        )
        await save_message_id(msg.from_user.id, status_msg.message_id)
        
        invoice_msg = await bot.send_invoice(
            chat_id=msg.from_user.id,
            title=f"Пополнение баланса",
            description=f"Пополнение баланса на {amount} ⭐",
            payload=f"{msg.from_user.id}:deposit:{amount}",
            currency="XTR",
            prices=[LabeledPrice(label=f"Пополнение {amount} ⭐", amount=amount)]
        )
        await save_message_id(msg.from_user.id, invoice_msg.message_id)
        
        # Устанавливаем состояние ожидания оплаты
        await state.set_state(BetStates.waiting_payment)
    except:
        await msg.answer("❌ Ошибка")


@router.message(F.text == "✏️ Своя сумма")
async def custom_deposit_amount(msg: Message, state: FSMContext, bot: Bot):
    """Своя сумма для пополнения"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text="✏️ Введи сумму для пополнения:\n\n"
        "Минимум: 1 ⭐\n"
        "Максимум: 2500 ⭐",
        reply_markup=get_cancel_reply_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)
    await state.set_state(BetStates.waiting_deposit_amount)
    logger.info(f"Установлено состояние waiting_deposit_amount для пользователя {msg.from_user.id}")


@router.message(F.text.in_(["🏀", "🎲", "⚽", "🎯", "🎳"]))
async def game_selected(msg: Message, state: FSMContext, bot: Bot):
    """Выбор игры по эмодзи"""
    game = msg.text
    
    await delete_last_message(msg.from_user.id, bot)
    
    # Показываем варианты ставок
    if game == '🏀':
        txt = f"{game} Баскетбол\n\nВыбери тип ставки:"
    elif game == '🎲':
        txt = f"{game} Кости\n\nВыбери тип ставки:"
    elif game == '⚽':
        txt = f"{game} Футбол\n\nВыбери тип ставки:"
    elif game == '🎯':
        txt = f"{game} Дартс\n\nВыбери тип ставки:"
    elif game == '🎳':
        txt = f"{game} Боулинг\n\nВыбери тип ставки:"
    
    await state.update_data(selected_game=game)
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text=txt,
        reply_markup=get_bet_type_keyboard(game)
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)


async def play_from_balance_text(msg: Message, game: str, bet_type: str, amount: int, user_data: dict, state: FSMContext):
    """Игра с баланса через текстовый интерфейс"""
    uid = msg.from_user.id
    username = msg.from_user.username
    
    log_game_start(uid, game, bet_type, amount, username)
    
    await msg.answer(f"💳 Списываем {amount} ⭐ с баланса...\n\n🎮 Запускаем {game}...")
    
    user_data['balance'] -= amount
    
    dm = await msg.answer_dice(emoji=game)
    await asyncio.sleep(4)
    
    dv = dm.dice.value
    res = determine_game_result(game, bet_type, dv)
    
    user_data['total_bets'] += amount
    user_data['games_played'] += 1
    
    if res['win']:
        w = int(amount * res['coefficient'])
        user_data['balance'] += w
        user_data['total_wins'] += w
        log_win(uid, game, bet_type, amount, w, username)
        
        txt = (
            f"🎉 ВЫИГРЫШ!\n\n"
            f"{game} Выпало: {res['outcome']}\n"
            f"🎯 Ставка: {bet_type}\n\n"
            f"💰 Выигрыш: {w} ⭐ (x{res['coefficient']})\n"
            f"💳 Баланс: {user_data['balance']} ⭐"
        )
    else:
        user_data['total_losses'] += amount
        w = -amount
        log_loss(uid, game, bet_type, amount, username)
        
        txt = (
            f"😔 Не повезло\n\n"
            f"{game} Выпало: {res['outcome']}\n"
            f"🎯 Ставка: {bet_type}\n\n"
            f"💸 Потеря: {amount} ⭐\n"
            f"💳 Баланс: {user_data['balance']} ⭐"
        )
    
    user_data['history'].append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'game': game,
        'bet_type': bet_type,
        'amount': amount,
        'result': res['outcome'],
        'dice_value': dv,
        'win': res['win'],
        'winnings': w,
        'payment_id': 'balance'
    })
    
    save_database(DB_FILE)
    await msg.answer(txt)
    await state.clear()


async def play_from_balance_callback(cb: CallbackQuery, game: str, bet_type: str, amount: int, user_data: dict, state: FSMContext, bot: Bot):
    """Игра с баланса через callback-кнопку"""
    uid = cb.from_user.id
    username = cb.from_user.username
    
    log_game_start(uid, game, bet_type, amount, username)
    
    sent_msg = await bot.send_message(
        chat_id=cb.from_user.id,
        text=f"💳 Списываем {amount} ⭐ с баланса...\n\n🎮 Запускаем {game}..."
    )
    
    user_data['balance'] -= amount
    
    dm = await bot.send_dice(chat_id=cb.from_user.id, emoji=game)
    await asyncio.sleep(4)
    
    dv = dm.dice.value
    res = determine_game_result(game, bet_type, dv)
    
    user_data['total_bets'] += amount
    user_data['games_played'] += 1
    
    if res['win']:
        w = int(amount * res['coefficient'])
        user_data['balance'] += w
        user_data['total_wins'] += w
        log_win(uid, game, bet_type, amount, w, username)
        
        txt = (
            f"🎉 ВЫИГРЫШ!\n\n"
            f"{game} Выпало: {res['outcome']}\n"
            f"🎯 Ставка: {bet_type}\n\n"
            f"💰 Выигрыш: {w} ⭐ (x{res['coefficient']})\n"
            f"💳 Баланс: {user_data['balance']} ⭐"
        )
    else:
        user_data['total_losses'] += amount
        w = -amount
        log_loss(uid, game, bet_type, amount, username)
        
        txt = (
            f"😔 Не повезло\n\n"
            f"{game} Выпало: {res['outcome']}\n"
            f"🎯 Ставка: {bet_type}\n\n"
            f"💸 Потеря: {amount} ⭐\n"
            f"💳 Баланс: {user_data['balance']} ⭐"
        )
    
    user_data['history'].append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'game': game,
        'bet_type': bet_type,
        'amount': amount,
        'result': res['outcome'],
        'dice_value': dv,
        'win': res['win'],
        'winnings': w,
        'payment_id': 'balance'
    })
    
    save_database(DB_FILE)
    await bot.send_message(chat_id=cb.from_user.id, text=txt)
    await state.clear()



@router.message(F.text.in_(["🎯 Гол", "🔄 Застрял", "❌ Мимо", "2️⃣4️⃣6️⃣ Четное", "1️⃣3️⃣5️⃣ Нечетное", 
                             "4️⃣5️⃣6️⃣ Больше 3", "1️⃣2️⃣3️⃣ Меньше 4", "⚽ Гол", "🎯 Центр", "🔴 Красное", 
                             "⚪ Белое", "💥 Страйк"]))
async def bet_type_selected_text(msg: Message, state: FSMContext, bot: Bot):
    """Выбор типа ставки через Reply кнопку"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    # Мапинг кнопок на типы ставок
    bet_mapping = {
        "🎯 Гол": "гол",
        "⚽ Гол": "гол",
        "🔄 Застрял": "застрял",
        "❌ Мимо": "мимо",
        "2️⃣4️⃣6️⃣ Четное": "четное",
        "1️⃣3️⃣5️⃣ Нечетное": "нечетное",
        "4️⃣5️⃣6️⃣ Больше 3": "больше_3",
        "1️⃣2️⃣3️⃣ Меньше 4": "меньше_4",
        "🎯 Центр": "центр",
        "🔴 Красное": "красное",
        "⚪ Белое": "белое",
        "💥 Страйк": "страйк"
    }
    
    bet_type = bet_mapping.get(msg.text)
    data = await state.get_data()
    game = data.get('selected_game')
    
    if not game:
        return await msg.answer("❌ Ошибка: игра не выбрана")
    
    await state.update_data(selected_bet_type=bet_type)
    
    ud = get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text=f"{game} Ставка: {bet_type}\n\n"
             f"💳 Твой баланс: {ud['balance']} ⭐\n\n"
             f"Выбери сумму ставки:",
        reply_markup=get_bet_amount_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)


@router.message(F.text.in_(["⭐ 1", "⭐ 5", "⭐ 10", "⭐ 25", "⭐ 50", "⭐ 100", "⭐ 250", "⭐ 500", "⭐ 1000"]))
async def bet_amount_selected_text(msg: Message, state: FSMContext, bot: Bot):
    """Выбор суммы ставки через Reply кнопку"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    await delete_last_message(msg.from_user.id, bot)
    
    amount = int(msg.text.split()[1])  # Берем число из "⭐ 100"
    data = await state.get_data()
    game = data.get('selected_game')
    bet_type = data.get('selected_bet_type')
    
    if not game or not bet_type:
        return await msg.answer("❌ Ошибка: игра или ставка не выбрана")
    
    ud = get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
    
    if ud['balance'] >= amount:
        # Играем с баланса
        await play_from_balance_text(msg, game, bet_type, amount, ud, state)
    else:
        # Запрашиваем оплату
        await msg.answer(f"💳 Оплата {amount} ⭐\n\nОтправляем счет...")
        await bot.send_invoice(
            chat_id=msg.from_user.id,
            title=f"{game} {bet_type}",
            description=f"Ставка {amount} ⭐ на {bet_type}",
            payload=f"{game}:{bet_type}:{amount}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Ставка", amount=amount)]
        )
        await state.update_data(
            pending_game=game,
            pending_bet_type=bet_type,
            pending_amount=amount
        )


@router.callback_query(F.data == "admin_users")
async def admin_show_users(cb: CallbackQuery):
    """Показать всех пользователей"""
    if cb.from_user.id != ADMIN_ID:
        return await cb.answer("❌ Нет доступа", show_alert=True)
    
    users_db = get_all_users()
    if not users_db:
        return await cb.answer("📭 Пользователей пока нет", show_alert=True)
    
    sorted_users = sorted(users_db.items(), key=lambda x: x[1]['games_played'], reverse=True)
    txt = f"👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ ({len(users_db)})\n\n"
    
    for uid, data in sorted_users:
        username = f"@{data.get('username')}" if data.get('username') else "—"
        first_name = data.get('first_name', '—')
        last_name = data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip() if last_name else first_name
        
        txt += (
            f"👤 {full_name}\n"
            f"   ID: {uid}\n"
            f"   Username: {username}\n"
            f"   💳 Баланс: {data['balance']} ⭐\n"
            f"   🎮 Игр: {data['games_played']}\n\n"
        )
        
        if len(txt) > 3500:
            await cb.message.answer(txt)
            txt = ""
    
    if txt:
        await cb.message.answer(txt)
    
    await cb.answer("✅ Список отправлен")


@router.callback_query(F.data == "admin_stats")
async def admin_show_stats(cb: CallbackQuery):
    """Показать статистику бота"""
    if cb.from_user.id != ADMIN_ID:
        return await cb.answer("❌ Нет доступа", show_alert=True)
    
    users_db = get_all_users()
    stats = get_user_stats()
    
    # Топ-3 игрока
    top_balance = sorted(users_db.items(), key=lambda x: x[1]['balance'], reverse=True)[:3]
    top_games = sorted(users_db.items(), key=lambda x: x[1]['games_played'], reverse=True)[:3]
    
    txt = (
        f"📊 СТАТИСТИКА БОТА\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"🎮 Всего игр: {stats['total_games']}\n"
        f"💰 Всего ставок: {stats['total_bets']} ⭐\n"
        f"🏆 Всего выплачено: {stats['total_wins']} ⭐\n"
        f"💸 Всего проиграно: {stats['total_losses']} ⭐\n"
        f"📈 Прибыль казино: {stats['total_bets'] - stats['total_wins']} ⭐\n\n"
    )
    
    txt += "💎 ТОП-3 ПО БАЛАНСУ:\n"
    for i, (uid, data) in enumerate(top_balance, 1):
        name = data.get('first_name', f"ID{uid}")
        txt += f"{i}. {name}: {data['balance']} ⭐\n"
    
    txt += "\n🎮 ТОП-3 ПО ИГРАМ:\n"
    for i, (uid, data) in enumerate(top_games, 1):
        name = data.get('first_name', f"ID{uid}")
        txt += f"{i}. {name}: {data['games_played']} игр\n"
    
    await cb.message.edit_text(txt, reply_markup=get_back_button("admin_refresh"))
    await cb.answer()


@router.callback_query(F.data == "admin_save")
async def admin_save_db(cb: CallbackQuery):
    """Сохранить базу данных"""
    if cb.from_user.id != ADMIN_ID:
        return await cb.answer("❌ Нет доступа", show_alert=True)
    
    save_database(DB_FILE)
    await cb.answer("✅ База данных сохранена!", show_alert=True)


@router.callback_query(F.data == "admin_refresh")
async def admin_refresh(cb: CallbackQuery):
    """Обновить админ-панель"""
    if cb.from_user.id != ADMIN_ID:
        return await cb.answer("❌ Нет доступа", show_alert=True)
    
    stats = get_user_stats()
    today_stats = get_today_stats()
    
    today_info = ""
    if today_stats:
        today_info = (
            f"\n📊 Сегодня:\n"
            f"   Новых: {today_stats['registers']} | "
            f"Игр: {today_stats['games']} | "
            f"Выигрышей: {today_stats['wins']}\n"
        )
    
    new_text = (
        f"👑 АДМИН ПАНЕЛЬ\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🎮 Игр: {stats['total_games']}\n"
        f"💰 Ставок: {stats['total_bets']} ⭐\n"
        f"🏆 Выплат: {stats['total_wins']} ⭐\n"
        f"📈 Прибыль: {stats['total_bets'] - stats['total_wins']} ⭐"
        f"{today_info}\n"
        f"📋 Команды:\n"
        f"/stats [user_id] - статистика\n"
        f"/setbalance [user_id] [сумма]\n"
        f"/addbalance [user_id] [сумма]\n"
        f"/refund [user_id] [payment_id]\n"
        f"/logs - логи за сегодня"
    )
    
    # Проверяем, изменился ли текст
    if cb.message.text != new_text:
        await cb.message.edit_text(new_text, reply_markup=get_admin_keyboard())
        await cb.answer("🔄 Обновлено")
    else:
        await cb.answer("✅ Данные актуальны", show_alert=True)


@router.callback_query(F.data.startswith("send_stars:"))
async def send_stars_to_user(cb: CallbackQuery, bot: Bot):
    """Отправка звезд пользователю через refund"""
    if cb.from_user.id != ADMIN_ID:
        return await cb.answer("❌ Нет доступа", show_alert=True)
    
    try:
        # Парсим данные: send_stars:user_id:amount
        _, user_id, amount = cb.data.split(":")
        user_id = int(user_id)
        amount = int(amount)
        
        # Получаем данные пользователя
        ud = get_user_data(user_id, None, DB_FILE)
        
        # Проверяем баланс
        if ud['balance'] < amount:
            await cb.answer(f"❌ У пользователя недостаточно средств на балансе", show_alert=True)
            return
        
        # Ищем подходящий платеж для возврата
        available_payments = [p for p in ud.get('payments', []) if not p.get('refunded', False)]
        
        if not available_payments:
            await cb.answer("❌ Нет доступных платежей для возврата. Пользователь должен сначала пополнить баланс.", show_alert=True)
            return
        
        # Ищем платеж с суммой >= запрошенной суммы
        suitable_payment = None
        for payment in available_payments:
            if payment['amount'] >= amount:
                suitable_payment = payment
                break
        
        if not suitable_payment:
            # Берем самый большой доступный платеж
            suitable_payment = max(available_payments, key=lambda x: x['amount'])
            if suitable_payment['amount'] < amount:
                await cb.answer(
                    f"❌ Максимальная сумма возврата: {suitable_payment['amount']} ⭐\n"
                    f"Запрошено: {amount} ⭐",
                    show_alert=True
                )
                return
        
        # Выполняем возврат через Telegram API
        try:
            await bot.refund_star_payment(
                user_id=user_id,
                telegram_payment_charge_id=suitable_payment['telegram_payment_charge_id']
            )
            
            # Помечаем платеж как возвращенный
            suitable_payment['refunded'] = True
            suitable_payment['refund_date'] = datetime.now().isoformat()
            suitable_payment['refund_amount'] = amount
            
            # Списываем с баланса пользователя
            ud['balance'] -= amount
            save_database(DB_FILE)
            
            log_balance_change(user_id, ud['balance'] + amount, ud['balance'], "withdraw", ud.get('username'))
            log_refund(user_id, amount, suitable_payment['telegram_payment_charge_id'], ud.get('username'))
            
            # Уведомляем админа
            await cb.message.edit_text(
                cb.message.text + 
                f"\n\n✅ Возврат выполнен!\n"
                f"💰 Сумма: {amount} ⭐\n"
                f"🔗 Payment ID: {suitable_payment['telegram_payment_charge_id'][:20]}...\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            await cb.answer("✅ Звезды возвращены пользователю!")
            
            # Уведомляем пользователя
            await bot.send_message(
                user_id,
                f"✅ Вывод выполнен!\n\n"
                f"💸 Сумма: {amount} ⭐\n"
                f"💳 Новый баланс: {ud['balance']} ⭐\n\n"
                f"Звезды возвращены на ваш Telegram аккаунт"
            )
            
        except Exception as refund_error:
            await cb.answer(f"❌ Ошибка возврата: {str(refund_error)}", show_alert=True)
            logger.error(f"Ошибка refund: {refund_error}")
        
    except Exception as e:
        await cb.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"Ошибка отправки звезд: {e}")
        await bot.send_message(
            user_id,
            f"✅ Вывод выполнен!\n\n"
            f"💸 Сумма: {amount} ⭐\n"
            f"💳 Новый баланс: {ud['balance']} ⭐"
        )
        
    except Exception as e:
        await cb.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"Ошибка отправки звезд: {e}")


@router.message(F.text == "❌ Отменить")
async def cancel_operation(msg: Message, state: FSMContext, bot: Bot):
    """Отмена текущей операции"""
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    current_state = await state.get_state()
    await state.clear()
    
    await delete_last_message(msg.from_user.id, bot)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text="❌ Операция отменена",
        reply_markup=get_reply_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)



@router.message(StateFilter(BetStates.waiting_deposit_amount), F.text)
async def process_deposit_amount(msg: Message, state: FSMContext, bot: Bot):
    """Обработка ввода своей суммы для пополнения"""
    logger.info(f"process_deposit_amount вызван для пользователя {msg.from_user.id}, текст: {msg.text}")
    
    # Игнорируем кнопку отмены (она обрабатывается отдельно)
    if msg.text == "❌ Отменить":
        return
    
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    try:
        amount = int(msg.text)
        if amount < 1 or amount > 2500:
            return await msg.answer("❌ Сумма должна быть от 1 до 2500 ⭐")
        
        await delete_last_message(msg.from_user.id, bot)
        
        status_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text=f"💳 Ожидаем оплату {amount} ⭐\n\nСчет отправлен ниже ⬇️",
            reply_markup=get_cancel_reply_keyboard()
        )
        await save_message_id(msg.from_user.id, status_msg.message_id)
        
        invoice_msg = await bot.send_invoice(
            chat_id=msg.from_user.id,
            title=f"Пополнение баланса",
            description=f"Пополнение баланса на {amount} ⭐",
            payload=f"{msg.from_user.id}:deposit:{amount}",
            currency="XTR",
            prices=[LabeledPrice(label=f"Пополнение {amount} ⭐", amount=amount)]
        )
        await save_message_id(msg.from_user.id, invoice_msg.message_id)
        
        # Устанавливаем состояние ожидания оплаты
        await state.set_state(BetStates.waiting_payment)
    except ValueError:
        await msg.answer("❌ Введи число от 1 до 2500")


@router.message(StateFilter(BetStates.waiting_withdraw_amount), F.text)
async def process_withdraw(msg: Message, state: FSMContext, bot: Bot):
    """Обработка запроса на вывод"""
    # Игнорируем кнопку отмены (она обрабатывается отдельно)
    if msg.text == "❌ Отменить":
        return
    
    # Удаляем сообщение пользователя
    try:
        await msg.delete()
    except:
        pass
    
    ud = get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
    
    try:
        amount = int(msg.text)
        
        if amount < 1:
            return await msg.answer("❌ Минимальная сумма: 1 ⭐")
        
        if amount > ud['balance']:
            return await msg.answer(f"❌ Недостаточно средств\n💳 Доступно: {ud['balance']} ⭐")
        
        # Создаем инлайн-кнопку для отправки звезд
        send_stars_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💫 Отправить {amount} ⭐",
                callback_data=f"send_stars:{msg.from_user.id}:{amount}"
            )]
        ])
        
        # Отправляем запрос админу
        await bot.send_message(
            ADMIN_ID,
            f"💸 ЗАПРОС НА ВЫВОД\n\n"
            f"👤 User ID: {msg.from_user.id}\n"
            f"👤 Username: @{msg.from_user.username or 'None'}\n"
            f"👤 Имя: {msg.from_user.first_name}\n\n"
            f"💰 Сумма: {amount} ⭐\n"
            f"💳 Баланс: {ud['balance']} ⭐\n\n"
            f"Нажми кнопку ниже, чтобы отправить звезды пользователю:",
            reply_markup=send_stars_kb
        )
        
        await delete_last_message(msg.from_user.id, bot)
        
        sent_msg = await bot.send_message(
            chat_id=msg.from_user.id,
            text="✅ Заявка на вывод отправлена!\n\n"
            f"💸 Сумма: {amount} ⭐\n\n"
            "⏳ Ожидай обработки администратором",
            reply_markup=get_reply_keyboard()
        )
        await save_message_id(msg.from_user.id, sent_msg.message_id)
        
        log_admin_action(msg.from_user.id, "WITHDRAW_REQUEST", amount=f"{amount}⭐")
        await state.clear()
        
    except ValueError:
        await msg.answer("❌ Введи число")


@router.message(F.text == "❌ Отменить")
async def cancel_operation_withdrawal(msg: Message, state: FSMContext, bot: Bot):
    """Отмена операции вывода"""
    current_state = await state.get_state()
    await state.clear()
    
    try:
        await msg.delete()
    except:
        pass
    await delete_last_message(msg.from_user.id, bot)
    
    sent_msg = await bot.send_message(
        chat_id=msg.from_user.id,
        text="❌ Операция отменена",
        reply_markup=get_reply_keyboard()
    )
    await save_message_id(msg.from_user.id, sent_msg.message_id)



@router.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery):
    """Предварительная проверка платежа"""
    await pcq.answer(ok=True)


@router.message(F.successful_payment)
async def success_pay(msg: Message, state: FSMContext, bot: Bot):
    """Успешный платеж"""
    # Парсим payload
    p = msg.successful_payment.invoice_payload.split(":")
    uid = int(p[0])
    action = p[1]
    payment_id = msg.successful_payment.telegram_payment_charge_id
    username = msg.from_user.username
    
    ud = get_user_data(uid, msg.from_user, DB_FILE)
    
    # Удаляем предыдущие сообщения
    await delete_last_message(uid, bot)
    
    if action == "deposit":
        # Пополнение баланса
        amount = int(p[2])
        ud['balance'] += amount
        
        # Сохраняем информацию о платеже для возможности refund
        ud['payments'].append({
            'amount': amount,
            'telegram_payment_charge_id': payment_id,
            'date': datetime.now().isoformat(),
            'refunded': False
        })
        
        save_database(DB_FILE)
        
        log_payment(uid, amount, payment_id, username)
        log_balance_change(uid, ud['balance'] - amount, ud['balance'], "deposit", username)
        
        # Очищаем состояние и возвращаем главную клавиатуру
        await state.clear()
        
        sent_msg = await bot.send_message(
            chat_id=uid,
            text=f"✅ Баланс пополнен!\n\n"
            f"💰 Зачислено: {amount} ⭐\n"
            f"💳 Баланс: {ud['balance']} ⭐",
            reply_markup=get_reply_keyboard()
        )
        await save_message_id(uid, sent_msg.message_id)
    else:
        # Игра
        g, bt, amt = action, p[2], int(p[3])
        
        # Логируем платеж
        log_payment(uid, amt, payment_id, username)
        log_game_start(uid, g, bt, amt, username)
        
        await msg.answer(f"✅ Оплата получена!\n\n🎮 Запускаем {g}...")
        
        # Запускаем игру
        dm = await msg.answer_dice(emoji=g)
        await asyncio.sleep(4)
        
        dv = dm.dice.value
        res = determine_game_result(g, bt, dv)
        
        ud['total_bets'] += amt
        ud['games_played'] += 1
        
        if res['win']:
            w = int(amt * res['coefficient'])
            ud['balance'] += w
            ud['total_wins'] += w
            
            # Логируем выигрыш
            log_win(uid, g, bt, amt, w, username)
            
            txt = (
                f"🎉 ВЫИГРЫШ!\n\n"
                f"{g} Выпало: {res['outcome']}\n"
                f"🎯 Ставка: {bt}\n\n"
                f"💰 Выигрыш: {w} ⭐ (x{res['coefficient']})\n"
                f"💳 Баланс: {ud['balance']} ⭐"
            )
        else:
            ud['total_losses'] += amt
            w = -amt
            
            # Логируем проигрыш
            log_loss(uid, g, bt, amt, username)
            
            txt = (
                f"😔 Не повезло\n\n"
                f"{g} Выпало: {res['outcome']}\n"
                f"🎯 Ставка: {bt}\n\n"
                f"💸 Потеря: {amt} ⭐\n"
                f"💳 Баланс: {ud['balance']} ⭐"
            )
        
        ud['history'].append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'game': g,
            'bet_type': bt,
            'amount': amt,
            'result': res['outcome'],
            'dice_value': dv,
            'win': res['win'],
            'winnings': w,
            'payment_id': msg.successful_payment.telegram_payment_charge_id
        })
        
        save_database(DB_FILE)
        await msg.answer(txt)


async def main():
    """Главная функция"""
    # Загружаем базу данных
    load_database(DB_FILE)
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    logger.info("🎰 Лотерейный бот запущен!")
    logger.info("💳 Прием платежей в Telegram Stars активирован")
    
    # Получаем порт и URL из переменных окружения
    port = int(os.getenv('PORT', 8080))
    webhook_url = os.getenv('RENDER_EXTERNAL_URL')
    
    # Если есть RENDER_EXTERNAL_URL - используем webhook, иначе polling
    if webhook_url:
        webhook_path = f"/webhook/{TOKEN}"
        webhook_full_url = f"{webhook_url}{webhook_path}"
        
        logger.info(f"🌐 Режим: Webhook")
        logger.info(f"📍 URL: {webhook_full_url}")
        
        # Удаляем старый webhook и устанавливаем новый
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(
            url=webhook_full_url,
            drop_pending_updates=True
        )
        
        # Запускаем веб-сервер с webhook
        from aiohttp import web
        app = web.Application()
        
        # Health check endpoint
        async def health(request):
            return web.Response(text="Bot is running! 🎰")
        
        # Webhook endpoint
        async def webhook_handler(request):
            update = await request.json()
            from aiogram.types import Update
            await dp.feed_update(bot, Update(**update))
            return web.Response(text="OK")
        
        app.router.add_get('/', health)
        app.router.add_get('/health', health)
        app.router.add_post(webhook_path, webhook_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"🚀 Webhook запущен на порту {port}")
        
        # Держим сервер запущенным
        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()
            save_database(DB_FILE)
            logger.info("👋 Бот остановлен")
    else:
        # Локальный режим - используем polling
        logger.info("🌐 Режим: Polling (локальный)")
        
        # Запускаем веб-сервер
        web_runner = await start_web_server(port)
        
        try:
            await dp.start_polling(bot)
        finally:
            # Останавливаем веб-сервер
            await web_runner.cleanup()
            # Сохраняем базу данных при остановке
            save_database(DB_FILE)
            logger.info("👋 Бот остановлен")


if __name__ == '__main__':
    asyncio.run(main())
