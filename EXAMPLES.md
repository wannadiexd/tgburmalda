# 📚 Примеры использования модулей

## 🔧 Добавление новой игры

### 1. Добавьте коэффициенты в `config.py`:
```python
COEFFICIENTS = {
    # ... существующие игры ...
    '🎰': {'джекпот': 10.0, 'три_в_ряд': 5.0, 'проигрыш': 0.0}
}
```

### 2. Добавьте логику в `game_logic.py`:
```python
def determine_game_result(game: str, bet_type: str, dice_value: int) -> dict:
    # ... существующие игры ...
    
    elif game == '🎰':
        if dice_value == 6:
            outcome = 'джекпот'
        elif dice_value >= 4:
            outcome = 'три_в_ряд'
        else:
            outcome = 'проигрыш'
    
    return {...}
```

### 3. Добавьте кнопку в `keyboards.py`:
```python
def get_games_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        # ... существующие игры ...
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="game_🎰")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")]
    ])

def get_bet_options_keyboard(game: str) -> InlineKeyboardMarkup:
    # ... существующие игры ...
    elif game == '🎰':
        buttons = [
            [InlineKeyboardButton(text=f"Джекпот (x10)", callback_data=f"bet_{game}_джекпот")],
            [InlineKeyboardButton(text=f"Три в ряд (x5)", callback_data=f"bet_{game}_три_в_ряд")]
        ]
```

### 4. Добавьте правила в `game_logic.py`:
```python
def get_rules_text() -> str:
    return (
        "📋 Правила:\n\n"
        # ... существующие правила ...
        "🎰 СЛОТЫ\n"
        "• Джекпот (6): x10.0\n"
        "• Три в ряд (4-5): x5.0\n"
        "• Проигрыш (1-3): x0.0\n\n"
    )
```

## 🎨 Добавление новой клавиатуры

В `keyboards.py`:
```python
def get_my_new_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кнопка 1", callback_data="action1")],
        [InlineKeyboardButton(text="Кнопка 2", callback_data="action2")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_menu")]
    ])
```

Использование в `bot.py`:
```python
from keyboards import get_my_new_keyboard

@router.callback_query(F.data == "show_new")
async def show_new(cb: CallbackQuery):
    await cb.message.edit_text("Новое меню", reply_markup=get_my_new_keyboard())
```

## 💾 Добавление нового поля в БД

В `database.py`:
```python
def get_user_data(user_id: int, user_obj=None, db_file: str = None) -> Dict:
    if user_id not in users_db:
        users_db[user_id] = {
            # ... существующие поля ...
            'new_field': 0,  # Новое поле
        }
    # ...
```

## 📊 Добавление новой статистики

В `database.py`:
```python
def get_detailed_stats() -> dict:
    """Расширенная статистика"""
    users = get_all_users()
    return {
        'total_users': len(users),
        'active_users': sum(1 for u in users.values() if u['games_played'] > 0),
        'total_balance': sum(u['balance'] for u in users.values()),
        # Добавьте свои метрики
    }
```

Использование в `bot.py`:
```python
from database import get_detailed_stats

@router.message(Command("detailedstats"))
async def cmd_detailed_stats(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    
    stats = get_detailed_stats()
    txt = f"📊 Детальная статистика:\n\n"
    txt += f"👥 Всего: {stats['total_users']}\n"
    txt += f"✅ Активных: {stats['active_users']}\n"
    txt += f"💰 Общий баланс: {stats['total_balance']} ⭐\n"
    
    await msg.answer(txt)
```

## 🔧 Изменение коэффициентов

Просто откройте `config.py` и измените:
```python
COEFFICIENTS = {
    '🏀': {'гол': 2.0, 'застрял': 3.0, 'мимо': 1.5},  # Увеличили
    # ...
}
```

Перезапустите бота - изменения применятся!

## 💰 Изменение сумм ставок

В `config.py`:
```python
BET_AMOUNTS = [5, 10, 25, 50, 100, 250, 500]  # Добавили 5 и 500
```

## 🎯 Добавление новой команды администратора

В `bot.py`:
```python
@router.message(Command("mycommand"))
async def cmd_mycommand(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Нет доступа")
    
    # Ваш код здесь
    await msg.answer("✅ Выполнено!")
```

## 📝 Лучшие практики

1. **Всегда импортируйте только то, что нужно**
   ```python
   from config import TOKEN, ADMIN_ID  # ✅ Хорошо
   from config import *  # ❌ Плохо
   ```

2. **Используйте функции из модулей**
   ```python
   from database import get_user_data, save_database
   
   ud = get_user_data(user_id)  # ✅ Хорошо
   save_database(DB_FILE)
   ```

3. **Не дублируйте код**
   - Если нужна новая клавиатура - добавьте в `keyboards.py`
   - Если нужна логика игры - добавьте в `game_logic.py`
   - Если нужна работа с БД - добавьте в `database.py`

4. **Комментируйте сложные места**
   ```python
   # Проверяем баланс перед игрой
   if user_data['balance'] >= amount:
       # Играем с баланса
       ...
   ```
