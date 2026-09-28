import os
from src.parser import get_available_groups, parse_week_schedule
from src.renderer import render_schedule_image

def test_both_themes():
    groups = get_available_groups()
    if not groups:
        print("❌ Группы не найдены! Проверьте, лежит ли файл schedule.xlsx в папке data/")
        return

    # Берем вашу группу (или первую из списка)
    my_group = groups[0]
    week_num = 2
    dates_mock = ["28.09", "29.09", "30.09", "01.10", "02.10", "03.10"]
    date_range = "28.09 - 03.10"

    print(f"1. Читаем данные для группы: {my_group}...")
    data = parse_week_schedule(my_group, week_num)
    if not data:
        print("❌ Не удалось распарсить расписание!")
        return

    # 1. Генерируем ТЁМНУЮ тему
    print("2. Рендерим ТЁМНУЮ тему...")
    dark_img = render_schedule_image(
        group_name=my_group,
        week_num=week_num,
        days_data=data,
        date_range=date_range,
        dates_list=dates_mock,
        theme="dark"
    )

    # 2. Генерируем СВЕТЛУЮ тему
    print("3. Рендерим СВЕТЛУЮ тему...")
    light_img = render_schedule_image(
        group_name=my_group,
        week_num=week_num,
        days_data=data,
        date_range=date_range,
        dates_list=dates_mock,
        theme="light"
    )

    print("\n✅ Обе картинки готовы!")
    print(f"🌙 Тёмная:  {dark_img}")
    print(f"☀️ Светлая: {light_img}")

    # Открываем обе картинки на экране для сравнения
    os.startfile(dark_img)
    os.startfile(light_img)


from datetime import datetime, timedelta


def check_weeks():
    for offset, name in [(0, "Текущая неделя"), (1, "Следующая неделя")]:
        today = datetime.now() + timedelta(weeks=offset)
        mon = today - timedelta(days=today.weekday())
        sat = mon + timedelta(days=5)

        iso_week = today.isocalendar()[1]

        # Наша новая формула
        week_num = 2 if (iso_week % 2 != 0) else 1

        date_range = f"{mon.strftime('%d.%m')} - {sat.strftime('%d.%m')}"
        print(f"👉 {name}: Неделя {week_num} (Даты: {date_range})")


if __name__ == "__main__":
    check_weeks()