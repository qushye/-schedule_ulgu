from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Текущая неделя"), KeyboardButton(text="⏭ Следующая неделя")],
            [KeyboardButton(text="👥 Сменить группу"), KeyboardButton(text="🎨 Сменить тему")],
            [KeyboardButton(text="🔄 Обновить файл")]
        ],
        resize_keyboard=True
    )

def get_course_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎓 1 курс", callback_data="setcourse:1"),
                InlineKeyboardButton(text="🎓 2 курс", callback_data="setcourse:2"),
                InlineKeyboardButton(text="🎓 3 курс", callback_data="setcourse:3"),
            ]
        ]
    )

def get_group_selection_keyboard(groups: list[str], course: int = 1) -> InlineKeyboardMarkup:
    keyboard = []
    row = []
    for g in groups:
        row.append(InlineKeyboardButton(text=g, callback_data=f"setgroup:{course}:{g}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Кнопка возврата к выбору курса
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад к выбору курса", callback_data="back_to_courses")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_theme_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌙 Тёмная тема", callback_data="settheme:dark"),
                InlineKeyboardButton(text="☀️ Светлая тема", callback_data="settheme:light")
            ]
        ]
    )