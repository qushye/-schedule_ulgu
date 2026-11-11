from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное нижнее меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Текущая неделя"), KeyboardButton(text="⏭ Следующая неделя")],
            [KeyboardButton(text="⚙️ Мой профиль и настройки")]
        ],
        resize_keyboard=True
    )

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Действия в профиле"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Сменить курс и группу", callback_data="change_course_group")],
            [InlineKeyboardButton(text="🎨 Сменить тему", callback_data="change_theme")]
        ]
    )

def get_course_selection_keyboard(show_back_to_profile: bool = False) -> InlineKeyboardMarkup:
    """Выбор курса"""
    buttons = [
        [
            InlineKeyboardButton(text="🎓 1 курс", callback_data="setcourse:1"),
            InlineKeyboardButton(text="🎓 2 курс", callback_data="setcourse:2"),
            InlineKeyboardButton(text="🎓 3 курс", callback_data="setcourse:3"),
        ]
    ]
    if show_back_to_profile:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="back_to_profile")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_group_selection_keyboard(groups: list[str], course: int = 1) -> InlineKeyboardMarkup:
    """Выбор группы курса"""
    keyboard = []
    row = []
    for g in groups:
        row.append(InlineKeyboardButton(text=g, callback_data=f"setgroup:{course}:{g}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад к выбору курса", callback_data="back_to_courses")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_theme_keyboard() -> InlineKeyboardMarkup:
    """Переключение темы с кнопкой возврата"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌙 Тёмная", callback_data="settheme:dark"),
                InlineKeyboardButton(text="☀️ Светлая", callback_data="settheme:light")
            ],
            [InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="back_to_profile")]
        ]
    )