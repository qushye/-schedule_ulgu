from vkbottle import Keyboard, KeyboardButtonColor, Text

def get_vk_main_keyboard() -> str:
    """Главное меню расписания"""
    return (
        Keyboard(one_time=False, inline=False)
        .add(Text("📅 Текущая неделя"), color=KeyboardButtonColor.PRIMARY)
        .add(Text("⏭ Следующая неделя"), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("⚙️ Мой профиль и настройки"), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

def get_vk_profile_keyboard() -> str:
    """Действия внутри профиля (inline)"""
    return (
        Keyboard(inline=True)
        .add(Text("🎓 Сменить курс и группу", payload={"action": "change_course"}), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("🎨 Сменить тему", payload={"action": "change_theme"}), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

def get_vk_course_keyboard() -> str:
    """Выбор курса (нижняя клавиатура с гарантированным возвратом)"""
    return (
        Keyboard(one_time=False, inline=False)
        .add(Text("🎓 1 курс", payload={"course": 1}), color=KeyboardButtonColor.PRIMARY)
        .add(Text("🎓 2 курс", payload={"course": 2}), color=KeyboardButtonColor.PRIMARY)
        .add(Text("🎓 3 курс", payload={"course": 3}), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("⬅️ Назад в главное меню", payload={"action": "back_to_main"}), color=KeyboardButtonColor.NEGATIVE)
        .get_json()
    )

def get_vk_group_keyboard(groups: list[str], course: int = 1) -> str:
    """Выбор группы (по 3 в ряд + кнопка возврата)"""
    kb = Keyboard(one_time=False, inline=False)
    count = 0
    for g in groups:
        kb.add(Text(g, payload={"set_course": course, "set_group": g}), color=KeyboardButtonColor.SECONDARY)
        count += 1
        if count % 3 == 0:
            kb.row()

    if count % 3 != 0:
        kb.row()

    kb.add(Text("⬅️ Назад к выбору курса", payload={"action": "change_course"}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()

def get_vk_theme_keyboard() -> str:
    """Выбор темы оформления (inline)"""
    return (
        Keyboard(inline=True)
        .add(Text("🌙 Тёмная", payload={"set_theme": "dark"}), color=KeyboardButtonColor.SECONDARY)
        .add(Text("☀️ Светлая", payload={"set_theme": "light"}), color=KeyboardButtonColor.SECONDARY)
        .row()
        .add(Text("⬅️ Назад в профиль", payload={"action": "back_to_profile"}), color=KeyboardButtonColor.NEGATIVE)
        .get_json()
    )