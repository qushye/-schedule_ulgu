from vkbottle import Keyboard, KeyboardButtonColor, Text

def get_vk_main_keyboard() -> str:
    return (
        Keyboard(one_time=False, inline=False)
        .add(Text("📅 Текущая неделя"), color=KeyboardButtonColor.PRIMARY)
        .add(Text("⏭ Следующая неделя"), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("⚙️ Мой профиль и настройки"), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

def get_vk_profile_keyboard() -> str:
    return (
        Keyboard(inline=True)
        .add(Text("🎓 Сменить курс и группу", payload={"action": "change_course"}), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("🎨 Сменить тему", payload={"action": "change_theme"}), color=KeyboardButtonColor.SECONDARY)
        .get_json()
    )

def get_vk_course_keyboard() -> str:
    return (
        Keyboard(inline=True)
        .add(Text("🎓 1 курс", payload={"course": 1}), color=KeyboardButtonColor.PRIMARY)
        .add(Text("🎓 2 курс", payload={"course": 2}), color=KeyboardButtonColor.PRIMARY)
        .add(Text("🎓 3 курс", payload={"course": 3}), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("⬅️ Назад в профиль", payload={"action": "back_to_profile"}), color=KeyboardButtonColor.NEGATIVE)
        .get_json()
    )

def get_vk_group_keyboard(groups: list[str], course: int = 1) -> str:
    """Нижняя клавиатура подгрупп (по 3 в ряд, без лимитов inline)"""
    kb = Keyboard(one_time=False, inline=False)
    count = 0
    for g in groups:
        kb.add(Text(g, payload={"set_course": course, "set_group": g}), color=KeyboardButtonColor.SECONDARY)
        count += 1
        # По 3 кнопки в ряд, чтобы компактно поместились все 20 групп
        if count % 3 == 0:
            kb.row()

    if count % 3 != 0:
        kb.row()

    kb.add(Text("⬅️ Назад к выбору курса", payload={"action": "change_course"}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()
def get_vk_theme_keyboard() -> str:
    return (
        Keyboard(inline=True)
        .add(Text("🌙 Тёмная", payload={"set_theme": "dark"}), color=KeyboardButtonColor.SECONDARY)
        .add(Text("☀️ Светлая", payload={"set_theme": "light"}), color=KeyboardButtonColor.SECONDARY)
        .row()
        .add(Text("⬅️ Назад в профиль", payload={"action": "back_to_profile"}), color=KeyboardButtonColor.NEGATIVE)
        .get_json()
    )