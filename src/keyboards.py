from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Текущая неделя"), KeyboardButton(text="⏭ Следующая неделя")],
            [KeyboardButton(text="👥 Сменить группу"), KeyboardButton(text="🔄 Обновить файл")]
        ],
        resize_keyboard=True
    )

def get_group_selection_keyboard(groups: list[str]) -> InlineKeyboardMarkup:
    keyboard = []
    row = []
    for g in groups:
        row.append(InlineKeyboardButton(text=g, callback_data=f"setgroup:{g}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)