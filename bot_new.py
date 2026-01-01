import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
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
    get_game_result_keyboard, get_back_button
)
from game_logic import determine_game_result, get_rules_text

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Роутер и состояния
router = Router()

class BetStates(StatesGroup):
    waiting_payment = State()


# ==================== КОМАНДЫ ====================

@router.message(CommandStart())
async def cmd_start(msg: Message):
    """Команда /start"""
    get_user_data(msg.from_user.id, msg.from_user, DB_FILE)
    await msg.answer(
        f"🎰 Добро пожаловать, {msg.from_user.first_name}!\n\n"
        f"Делай ставки в Telegram Stars ⭐ и выигрывай! 🍀",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    """Админ-панель"""
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    stats = get_user_stats()
    await msg.answer(
        f"👑 АДМИН ПАНЕЛЬ\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🎮 Игр: {stats['total_games']}\n"
        f"💰 Ставок: {stats['total_bets']} ⭐\n"
        f"🏆 Выплат: {stats['total_wins']} ⭐\n"
        f"📈 Прибыль: {stats['total_bets'] - stats['total_wins']} ⭐\n\n"
        f"📋 Команды:\n"
        f"/stats [user_id] - статистика\n"
        f"/setbalance [user_id] [сумма]\n"
        f"/addbalance [user_id] [сумма]\n"
        f"/refund [user_id] [payment_id]",
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


# ==================== CALLBACK ОБРАБОТЧИКИ ====================

@router.callback_query(F.data == "play")
async def show_games(cb: CallbackQuery):
    """Показать список игр"""
    await cb.message.edit_text("🎮 Выбери игру:", reply_markup=get_games_keyboard())
    await cb.answer()


@router.callback_query(F.data == "profile")
async def show_profile(cb: CallbackQuery):
    """Показать профиль пользователя"""
    ud = get_user_data(cb.from_user.id, cb.from_user, DB_FILE)
    pr = ud['total_wins'] - ud['total_losses']
    wr = (sum(1 for g in ud['history'] if g['win']) / ud['games_played'] * 100) if ud['games_played'] > 0 else 0
    
    txt = (
        f"👤 Профиль\n\n"
        f"💳 Баланс: {ud['balance']} ⭐\n"
        f"🎮 Игр: {ud['games_played']}\n"
        f"📊 Побед: {wr:.1f}%\n"
        f"💰 Ставок: {ud['total_bets']} ⭐\n"
        f"🏆 Выигрышей: {ud['total_wins']} ⭐\n"
        f"💸 Проигрышей: {ud['total_losses']} ⭐\n"
        f"📈 Прибыль: {pr:+d} ⭐\n\n"
    )
    
    if ud['history']:
        txt += "📜 Последние 5:\n" + "\n".join(
            f"{'✅' if g['win'] else '❌'} {g['game']} {g['bet_type']} {g['winnings']:+d} ⭐"
            for g in ud['history'][-5:][::-1]
        )
    
    await cb.message.edit_text(txt, reply_markup=get_back_button("back_menu"))
    await cb.answer()


@router.callback_query(F.data == "rules")
async def show_rules(cb: CallbackQuery):
    """Показать правила"""
    await cb.message.edit_text(get_rules_text(), reply_markup=get_back_button("back_menu"))
    await cb.answer()


@router.callback_query(F.data.startswith("game_"))
async def sel_game(cb: CallbackQuery):
    """Выбор игры"""
    g = cb.data.split("_")[1]
    await cb.message.edit_text(f"{g} Выбери ставку:", reply_markup=get_bet_options_keyboard(g))
    await cb.answer()


@router.callback_query(F.data.startswith("bet_"))
async def sel_bet(cb: CallbackQuery):
    """Выбор типа ставки"""
    p = cb.data.split("_")
    ud = get_user_data(cb.from_user.id, cb.from_user, DB_FILE)
    await cb.message.edit_text(
        f"{p[1]} Выбери сумму:\n\n💳 Твой баланс: {ud['balance']} ⭐",
        reply_markup=get_bet_amounts_keyboard(p[1], p[2], ud['balance'])
    )
    await cb.answer()


@router.callback_query(F.data.startswith("amount_"))
async def sel_amt(cb: CallbackQuery, state: FSMContext):
    """Выбор суммы ставки"""
    p = cb.data.split("_")
    g, bt, amt = p[1], p[2], int(p[3])
    ud = get_user_data(cb.from_user.id, cb.from_user, DB_FILE)
    
    # Проверяем баланс пользователя
    if ud['balance'] >= amt:
        # Играем с баланса
        await play_game_from_balance(cb, g, bt, amt, ud)
    else:
        # Запрашиваем оплату через Stars
        await request_payment(cb, state, g, bt, amt, ud)


async def play_game_from_balance(cb: CallbackQuery, game: str, bet_type: str, amount: int, user_data: dict):
    """Игра с использованием баланса"""
    await cb.message.edit_text(f"💳 Списываем {amount} ⭐ с баланса...\n\n🎮 Запускаем {game}...")
    await cb.answer()
    
    # Списываем с баланса
    user_data['balance'] -= amount
    
    # Запускаем игру
    dm = await cb.message.answer_dice(emoji=game)
    await asyncio.sleep(4)
    
    dv = dm.dice.value
    res = determine_game_result(game, bet_type, dv)
    
    user_data['total_bets'] += amount
    user_data['games_played'] += 1
    
    if res['win']:
        w = int(amount * res['coefficient'])
        user_data['balance'] += w
        user_data['total_wins'] += w
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
        'payment_id': 'balance_payment',
        'paid_with_balance': True
    })
    
    save_database(DB_FILE)
    await cb.message.answer(txt, reply_markup=get_game_result_keyboard())


async def request_payment(cb: CallbackQuery, state: FSMContext, game: str, bet_type: str, amount: int, user_data: dict):
    """Запрос оплаты через Telegram Stars"""
    await state.update_data(game=game, bet_type=bet_type, amount=amount, user_id=cb.from_user.id)
    pl = f"{cb.from_user.id}:{game}:{bet_type}:{amount}"
    
    await cb.message.answer_invoice(
        title=f"{game} Лотерея",
        description=f"Ставка на {bet_type} • {amount} ⭐",
        payload=pl,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"Ставка {bet_type}", amount=amount)]
    )
    
    await cb.message.edit_text(
        f"💳 Счет создан!\n\n"
        f"{game} Ставка: {bet_type}\n"
        f"💰 Сумма: {amount} ⭐\n"
        f"💵 Ваш баланс: {user_data['balance']} ⭐\n\n"
        f"Нажми 'Pay'"
    )
    await cb.answer()


@router.callback_query(F.data == "back_games")
async def back_games(cb: CallbackQuery):
    """Вернуться к выбору игр"""
    await cb.message.edit_text("🎮 Выбери игру:", reply_markup=get_games_keyboard())
    await cb.answer()


@router.callback_query(F.data == "back_menu")
async def back_menu(cb: CallbackQuery):
    """Вернуться в главное меню"""
    await cb.message.edit_text("🎰 Главное меню", reply_markup=get_main_keyboard())
    await cb.answer()


# ==================== АДМИН CALLBACK ОБРАБОТЧИКИ ====================

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
    await cb.message.edit_text(
        f"👑 АДМИН ПАНЕЛЬ\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🎮 Игр: {stats['total_games']}\n"
        f"💰 Ставок: {stats['total_bets']} ⭐\n"
        f"🏆 Выплат: {stats['total_wins']} ⭐\n"
        f"📈 Прибыль: {stats['total_bets'] - stats['total_wins']} ⭐\n\n"
        f"📋 Команды:\n"
        f"/stats [user_id] - статистика\n"
        f"/setbalance [user_id] [сумма]\n"
        f"/addbalance [user_id] [сумма]\n"
        f"/refund [user_id] [payment_id]",
        reply_markup=get_admin_keyboard()
    )
    await cb.answer("🔄 Обновлено")


# ==================== ПЛАТЕЖИ ====================

@router.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery):
    """Предварительная проверка платежа"""
    await pcq.answer(ok=True)


@router.message(F.successful_payment)
async def success_pay(msg: Message):
    """Успешный платеж"""
    # Парсим payload
    p = msg.successful_payment.invoice_payload.split(":")
    uid, g, bt, amt = int(p[0]), p[1], p[2], int(p[3])
    
    await msg.answer(f"✅ Оплата получена!\n\n🎮 Запускаем {g}...")
    
    # Запускаем игру
    dm = await msg.answer_dice(emoji=g)
    await asyncio.sleep(4)
    
    dv = dm.dice.value
    res = determine_game_result(g, bt, dv)
    ud = get_user_data(uid, msg.from_user, DB_FILE)
    
    ud['total_bets'] += amt
    ud['games_played'] += 1
    
    if res['win']:
        w = int(amt * res['coefficient'])
        ud['balance'] += w
        ud['total_wins'] += w
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
    await msg.answer(txt, reply_markup=get_game_result_keyboard())


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Главная функция"""
    # Загружаем базу данных
    load_database(DB_FILE)
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    logger.info("🎰 Лотерейный бот запущен!")
    logger.info("💳 Прием платежей в Telegram Stars активирован")
    
    try:
        await dp.start_polling(bot)
    finally:
        # Сохраняем базу данных при остановке
        save_database(DB_FILE)
        logger.info("👋 Бот остановлен")


if __name__ == '__main__':
    asyncio.run(main())
