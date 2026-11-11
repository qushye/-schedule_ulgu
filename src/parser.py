import openpyxl
from src.config import COURSES, DAYS_CONFIG

def clean_dummy_markers(text: str) -> str:
    """Убирает одиночные крестики (x / х), прочерки и точки, превращая их в пустое окно"""
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.lower() in ["x", "х", "-", "—", ".", "окно", "нет"]:
        return ""
    return cleaned

def get_cell_value(sheet, row: int, col: int) -> str:
    """Считывает текст ячейки с учетом объединения и очищает от крестиков-заглушек"""
    val = sheet.cell(row=row, column=col).value
    if val is not None:
        return clean_dummy_markers(str(val))

    for rng in sheet.merged_cells.ranges:
        if rng.min_row <= row <= rng.max_row and rng.min_col <= col <= rng.max_col:
            top_val = sheet.cell(row=rng.min_row, column=rng.min_col).value
            return clean_dummy_markers(str(top_val)) if top_val is not None else ""
    return ""

def get_available_groups(course: int = 1) -> list[str]:
    """Считывает список всех доступных групп выбранного курса"""
    excel_path = COURSES.get(course, COURSES[1])["path"]
    if not excel_path.exists():
        return []

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.worksheets[0]
    groups = []
    for col in range(4, sheet.max_column + 1):
        val = sheet.cell(row=1, column=col).value
        if val:
            g = str(val).strip()
            if g and g not in groups:
                groups.append(g)
    return groups

def parse_week_schedule(group_name: str, week_num: int, course: int = 1):
    """Парсит расписание на выбранную неделю и курс"""
    excel_path = COURSES.get(course, COURSES[1])["path"]
    if not excel_path.exists():
        return None

    wb = openpyxl.load_workbook(excel_path, data_only=True)

    # Умный поиск нужного листа (работает для любого курса: "1курс-1неделя", "2курс-1неделя" и т.д.)
    target_sheet = None
    for name in wb.sheetnames:
        clean_name = name.lower().replace(" ", "")
        if f"{week_num}недел" in clean_name:
            target_sheet = wb[name]
            break

    # Если название листа нестандартное — берем 1-й лист для 1 недели и 2-й лист для 2 недели
    if target_sheet is None:
        idx = 0 if week_num == 1 else min(1, len(wb.worksheets) - 1)
        target_sheet = wb.worksheets[idx]

    sheet = target_sheet

    group_col = None
    for col in range(4, sheet.max_column + 1):
        val = sheet.cell(row=1, column=col).value
        if val and str(val).strip().lower() == group_name.strip().lower():
            group_col = col
            break

    if not group_col:
        return None

    schedule_data = []
    for day_full, day_short, start_row in DAYS_CONFIG:
        col_a_text = get_cell_value(sheet, start_row, 1).lower()
        note = "Лекции" if "лекци" in col_a_text else ""

        pairs = {}
        for p in range(1, 9):
            row = start_row + (p - 1)
            pairs[p] = get_cell_value(sheet, row, group_col)

        schedule_data.append({
            "name": day_short,
            "note": note,
            "pairs": pairs
        })

    return schedule_data