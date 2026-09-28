import os
from src.parser import get_available_groups, parse_week_schedule
from src.renderer import render_schedule_image


def test():
    groups = get_available_groups()
    print("Найденные группы в таблице:", groups)

    if not groups:
        print("Группы не найдены! Проверьте файл schedule.xlsx")
        return

    # Берем вашу первую группу
    my_group = groups[0]
    print(f"\nГенерируем расписание для: {my_group}...")

    # Парсим 2-ю неделю
    week_num = 2
    data = parse_week_schedule(my_group, week_num)

    dates_mock = ["22.09", "23.09", "24.09", "25.09", "26.09", "27.09"]
    date_range = "22.09 - 27.09"

    img_path = render_schedule_image(my_group, week_num, data, date_range, dates_mock)
    print(f"\n✅ Картинка успешно создана: {img_path}")

    # Автоматически открываем сгенерированную картинку на экране
    os.system(f'start "" "{img_path}"')


if __name__ == "__main__":
    test()