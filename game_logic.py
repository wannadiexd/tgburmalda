# Игровая логика

from config import COEFFICIENTS


def determine_game_result(game: str, bet_type: str, dice_value: int) -> dict:
    """
    Определение результата игры
    
    Args:
        game: Эмодзи игры (🏀, 🎲, ⚽, 🎯, 🎳)
        bet_type: Тип ставки (гол, мимо, четное и т.д.)
        dice_value: Значение выпавшего кубика
    
    Returns:
        dict: {'win': bool, 'outcome': str, 'coefficient': float}
    """
    
    if game == '🏀':
        outcome = 'гол' if dice_value >= 4 else ('застрял' if dice_value == 3 else 'мимо')
        
    elif game == '🎲':
        outcomes = []
        if dice_value % 2 == 0:
            outcomes.append('четное')
        else:
            outcomes.append('нечетное')
        
        if dice_value > 3:
            outcomes.append('больше_3')
        else:
            outcomes.append('меньше_4')
        
        return {
            'win': bet_type in outcomes,
            'outcome': f"{dice_value} ({', '.join(outcomes)})",
            'coefficient': COEFFICIENTS[game][bet_type] if bet_type in outcomes else 0
        }
        
    elif game == '⚽':
        outcome = 'гол' if dice_value >= 3 else 'мимо'
        
    elif game == '🎯':
        if dice_value == 6:
            outcome = 'центр'
        elif dice_value >= 4:
            outcome = 'красное'
        elif dice_value >= 2:
            outcome = 'белое'
        else:
            outcome = 'мимо'
            
    elif game == '🎳':
        outcome = 'страйк' if dice_value == 6 else 'мимо'
    
    return {
        'win': bet_type == outcome,
        'outcome': outcome,
        'coefficient': COEFFICIENTS[game][bet_type] if bet_type == outcome else 0
    }


def get_rules_text() -> str:
    """Получение текста с правилами игры"""
    return (
        "📋 Правила:\n\n"
        "🏀 БАСКЕТБОЛ\n"
        "• Гол (4-5): x1.8\n"
        "• Застрял (3): x2.2\n"
        "• Мимо (1-2): x1.3\n\n"
        "🎲 КОСТИ\n"
        "• Четное/Нечетное: x1.7\n"
        "• Больше 3: x1.7\n"
        "• Меньше 4: x1.7\n\n"
        "⚽ ФУТБОЛ\n"
        "• Гол (3-5): x1.6\n"
        "• Мимо (1-2): x1.4\n\n"
        "🎯 ДАРТС\n"
        "• Центр (6): x4.0\n"
        "• Красное (4-5): x2.2\n"
        "• Белое (2-3): x1.6\n"
        "• Мимо (1): x1.2\n\n"
        "🎳 БОУЛИНГ\n"
        "• Страйк (6): x2.8\n"
        "• Мимо (1-5): x1.3"
    )
