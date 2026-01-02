# Клавиатуры для бота

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from config import COEFFICIENTS, BET_AMOUNTS


def get_reply_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная клавиатура внизу чата"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Играть"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="ℹ️ Правила")]
        ],
        resize_keyboard=True,
        persistent=True
    )


def get_games_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с играми"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏀 Баскетбол"), KeyboardButton(text="🎲 Кости")],
            [KeyboardButton(text="⚽ Футбол"), KeyboardButton(text="🎯 Дартс")],
            [KeyboardButton(text="🎳 Боулинг")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )


def get_profile_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура профиля"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Пополнить"), KeyboardButton(text="💸 Вывод")],
            [KeyboardButton(text="🎮 Играть"), KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )


def get_deposit_amounts_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с суммами пополнения"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ 1"), KeyboardButton(text="⭐ 5"), KeyboardButton(text="⭐ 10")],
            [KeyboardButton(text="⭐ 25"), KeyboardButton(text="⭐ 50"), KeyboardButton(text="⭐ 100")],
            [KeyboardButton(text="⭐ 250"), KeyboardButton(text="✏️ Своя сумма")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="ℹ️ Правила", callback_data="rules")]
    ])


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ-панель"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats")],
        [InlineKeyboardButton(text="💾 Сохранить БД", callback_data="admin_save")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh")]
    ])


def get_games_keyboard() -> InlineKeyboardMarkup:
    """Выбор игры"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_🏀")],
        [InlineKeyboardButton(text="🎲 Кости", callback_data="game_🎲")],
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="game_⚽")],
        [InlineKeyboardButton(text="🎯 Дартс", callback_data="game_🎯")],
        [InlineKeyboardButton(text="🎳 Боулинг", callback_data="game_🎳")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")]
    ])


def get_bet_options_keyboard(game: str) -> InlineKeyboardMarkup:
    """Выбор типа ставки для игры"""
    buttons = []
    
    if game == '🏀':
        buttons = [
            [InlineKeyboardButton(text=f"Гол (x{COEFFICIENTS[game]['гол']})", callback_data=f"bet_{game}_гол")],
            [InlineKeyboardButton(text=f"Застрял (x{COEFFICIENTS[game]['застрял']})", callback_data=f"bet_{game}_застрял")],
            [InlineKeyboardButton(text=f"Мимо (x{COEFFICIENTS[game]['мимо']})", callback_data=f"bet_{game}_мимо")]
        ]
    elif game == '🎲':
        buttons = [
            [InlineKeyboardButton(text=f"Четное (x{COEFFICIENTS[game]['четное']})", callback_data=f"bet_{game}_четное")],
            [InlineKeyboardButton(text=f"Нечетное (x{COEFFICIENTS[game]['нечетное']})", callback_data=f"bet_{game}_нечетное")],
            [InlineKeyboardButton(text=f"Больше 3 (x{COEFFICIENTS[game]['больше_3']})", callback_data=f"bet_{game}_больше_3")],
            [InlineKeyboardButton(text=f"Меньше 4 (x{COEFFICIENTS[game]['меньше_4']})", callback_data=f"bet_{game}_меньше_4")]
        ]
    elif game == '⚽':
        buttons = [
            [InlineKeyboardButton(text=f"Гол (x{COEFFICIENTS[game]['гол']})", callback_data=f"bet_{game}_гол")],
            [InlineKeyboardButton(text=f"Мимо (x{COEFFICIENTS[game]['мимо']})", callback_data=f"bet_{game}_мимо")]
        ]
    elif game == '🎯':
        buttons = [
            [InlineKeyboardButton(text=f"Центр (x{COEFFICIENTS[game]['центр']})", callback_data=f"bet_{game}_центр")],
            [InlineKeyboardButton(text=f"Красное (x{COEFFICIENTS[game]['красное']})", callback_data=f"bet_{game}_красное")],
            [InlineKeyboardButton(text=f"Белое (x{COEFFICIENTS[game]['белое']})", callback_data=f"bet_{game}_белое")],
            [InlineKeyboardButton(text=f"Мимо (x{COEFFICIENTS[game]['мимо']})", callback_data=f"bet_{game}_мимо")]
        ]
    elif game == '🎳':
        buttons = [
            [InlineKeyboardButton(text=f"Страйк (x{COEFFICIENTS[game]['страйк']})", callback_data=f"bet_{game}_страйк")],
            [InlineKeyboardButton(text=f"Мимо (x{COEFFICIENTS[game]['мимо']})", callback_data=f"bet_{game}_мимо")]
        ]
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_bet_amounts_keyboard(game: str, bet_type: str, user_balance: int = 0) -> InlineKeyboardMarkup:
    """Выбор суммы ставки"""
    buttons = []
    for amt in BET_AMOUNTS:
        text = f"⭐ {amt} Stars"
        if user_balance >= amt:
            text += " 💳"  # Значок что можно оплатить с баланса
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"amount_{game}_{bet_type}_{amt}")])
    
    # Добавляем кнопку "Своя сумма"
    buttons.append([InlineKeyboardButton(text="✏️ Своя сумма", callback_data=f"custom_amount_{game}_{bet_type}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"game_{game}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw")],
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")]
    ])


def get_deposit_keyboard() -> InlineKeyboardMarkup:
    """Выбор суммы пополнения"""
    buttons = []
    for amt in BET_AMOUNTS:
        buttons.append([InlineKeyboardButton(text=f"⭐ {amt} Stars", callback_data=f"deposit_amount_{amt}")])
    
    buttons.append([InlineKeyboardButton(text="✏️ Своя сумма", callback_data="deposit_custom")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="profile")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_game_result_keyboard() -> InlineKeyboardMarkup:
    """Кнопки после игры"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть ещё", callback_data="play")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")]
    ])


def get_back_button(callback: str = "back_menu") -> InlineKeyboardMarkup:
    """Кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback)]
    ])


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
    ])


def get_cancel_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply клавиатура с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить")]
        ],
        resize_keyboard=True
    )


def get_bet_type_keyboard(game: str) -> InlineKeyboardMarkup:
    """Inline клавиатура для выбора типа ставки"""
    buttons = []
    
    if game == '🏀':
        buttons = [
            [InlineKeyboardButton(text="🎯 Гол", callback_data="bet_type:гол")],
            [InlineKeyboardButton(text="🔄 Застрял", callback_data="bet_type:застрял")],
            [InlineKeyboardButton(text="❌ Мимо", callback_data="bet_type:мимо")]
        ]
    elif game == '🎲':
        buttons = [
            [InlineKeyboardButton(text="2️⃣ 4️⃣ 6️⃣ Четное", callback_data="bet_type:четное")],
            [InlineKeyboardButton(text="1️⃣ 3️⃣ 5️⃣ Нечетное", callback_data="bet_type:нечетное")],
            [InlineKeyboardButton(text="4️⃣ 5️⃣ 6️⃣ Больше 3", callback_data="bet_type:больше_3")],
            [InlineKeyboardButton(text="1️⃣ 2️⃣ 3️⃣ Меньше 4", callback_data="bet_type:меньше_4")]
        ]
    elif game == '⚽':
        buttons = [
            [InlineKeyboardButton(text="⚽ Гол", callback_data="bet_type:гол")],
            [InlineKeyboardButton(text="❌ Мимо", callback_data="bet_type:мимо")]
        ]
    elif game == '🎯':
        buttons = [
            [InlineKeyboardButton(text="🎯 Центр", callback_data="bet_type:центр")],
            [InlineKeyboardButton(text="🔴 Красное", callback_data="bet_type:красное")],
            [InlineKeyboardButton(text="⚪ Белое", callback_data="bet_type:белое")],
            [InlineKeyboardButton(text="❌ Мимо", callback_data="bet_type:мимо")]
        ]
    elif game == '🎳':
        buttons = [
            [InlineKeyboardButton(text="💥 Страйк", callback_data="bet_type:страйк")],
            [InlineKeyboardButton(text="❌ Мимо", callback_data="bet_type:мимо")]
        ]
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_games")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_bet_amount_keyboard() -> InlineKeyboardMarkup:
    """Inline клавиатура для выбора суммы ставки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ 1", callback_data="bet_amount:1"),
            InlineKeyboardButton(text="⭐ 5", callback_data="bet_amount:5"),
            InlineKeyboardButton(text="⭐ 10", callback_data="bet_amount:10")
        ],
        [
            InlineKeyboardButton(text="⭐ 25", callback_data="bet_amount:25"),
            InlineKeyboardButton(text="⭐ 50", callback_data="bet_amount:50"),
            InlineKeyboardButton(text="⭐ 100", callback_data="bet_amount:100")
        ],
        [
            InlineKeyboardButton(text="⭐ 250", callback_data="bet_amount:250"),
            InlineKeyboardButton(text="⭐ 500", callback_data="bet_amount:500"),
            InlineKeyboardButton(text="⭐ 1000", callback_data="bet_amount:1000")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_bet_type")]
    ])


