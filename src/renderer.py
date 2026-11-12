import sys
from html2image import Html2Image
from src.config import DATA_DIR, LESSON_TIMES

# Размер 1280x800 дает запас по высоте, чтобы суббота с длинными парами не обрезалась
if sys.platform == "win32":
    hti = Html2Image(output_path=str(DATA_DIR), size=(1280, 800))
else:
    hti = Html2Image(
        browser_executable="chromium",
        output_path=str(DATA_DIR),
        size=(1280, 800),
        custom_flags=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-default-apps",
            "--no-first-run",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--hide-scrollbars",
            "--mute-audio"
        ]
    )

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ 
        box-sizing: border-box; 
    }}

    :root {{
        --bg-color: #0c131d;
        --header-bg: #121d2b;
        --border-color: #1e2c3d;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --text-time: #64748b;
        --text-cell: #f1f5f9;
        --accent: #38bdf8;
        --badge-bg: rgba(56, 189, 248, 0.15);
        --badge-border: rgba(56, 189, 248, 0.35);
    }}

    body.light {{
        --bg-color: #f8fafc;
        --header-bg: #e2e8f0;
        --border-color: #cbd5e1;
        --text-main: #0f172a;
        --text-muted: #475569;
        --text-time: #64748b;
        --text-cell: #1e293b;
        --accent: #0284c7;
        --badge-bg: rgba(2, 132, 199, 0.12);
        --badge-border: rgba(2, 132, 199, 0.3);
    }}

    html, body {{
        margin: 0;
        padding: 12px 16px;
        background-color: var(--bg-color);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: var(--text-main);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 19px;
        font-weight: 700;
        margin-bottom: 8px;
        padding: 0 4px;
        height: 30px;
    }}
    .bot-name {{
        color: var(--text-muted);
        font-weight: 500;
        font-size: 15px;
    }}
    table {{
        width: 100%;
        height: calc(100% - 38px);
        border-collapse: collapse;
        table-layout: fixed;
    }}
    th, td {{
        border: 1px solid var(--border-color);
        text-align: center;
        vertical-align: middle;
        padding: 3px 4px; /* Плотные отступы ячеек */
    }}
    th {{
        background-color: var(--header-bg);
        color: var(--text-muted);
        font-size: 13px;
        font-weight: 600;
        height: 44px;
    }}
    th span {{
        display: block;
        font-size: 11px;
        font-weight: normal;
        color: var(--text-time);
        margin-top: 2px;
    }}
    .day-col {{
        width: 76px;
        font-weight: 700;
        background-color: var(--header-bg);
        font-size: 16px;
        color: var(--text-main);
    }}
    .day-date {{
        font-size: 11.5px;
        font-weight: normal;
        color: var(--text-muted);
        display: block;
        margin-top: 2px;
    }}
    .day-badge {{
        display: inline-block;
        font-size: 9.5px;
        font-weight: 600;
        color: var(--accent);
        background-color: var(--badge-bg);
        border: 1px solid var(--badge-border);
        border-radius: 4px;
        padding: 2px 4px;
        margin-top: 3px;
        line-height: 1.1;
    }}
    .cell-content {{
        font-size: 11.5px; /* Компактный шрифт для длинных клинических предметов */
        line-height: 1.22;
        color: var(--text-cell);
        word-wrap: break-word;
        white-space: pre-wrap;
        font-weight: 500;
    }}
</style>
</head>
<body class="{theme_class}">
    <div class="header">
        <div>Расписание: <span style="color: var(--accent);">{group}</span></div>
        <div class="bot-name">Расписание занятий</div>
        <div>{date_range} &nbsp;|&nbsp; Неделя {week_num}</div>
    </div>
    <table>
        <thead>
            <tr>
                <th class="day-col">Пара<br><span style="color: var(--text-time)">Время</span></th>
                {header_cols}
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</body>
</html>
"""


def to_clean_filename(group_name: str) -> str:
    """Переводит русские буквы группы в понятную латиницу: Ст-25/10б -> St-25_10b"""
    translit = {
        "Ст": "St", "ст": "st",
        "а": "a", "А": "A",
        "б": "b", "Б": "B",
        "в": "v", "В": "V",
        "/": "_"
    }
    result = group_name
    for ru, en in translit.items():
        result = result.replace(ru, en)
    return result


def render_schedule_image(group_name: str, week_num: int, days_data, date_range: str, dates_list: list,
                          theme: str = "dark") -> str:
    header_cols = "".join([f"<th>{num}<span>{time}</span></th>" for num, time in LESSON_TIMES])

    rows_html = ""
    for i, day in enumerate(days_data):
        d_date = dates_list[i] if i < len(dates_list) else ""
        badge_html = f"<span class='day-badge'>{day['note']}</span>" if day.get("note") else ""
        cells = f"<td class='day-col'>{day['name']}<span class='day-date'>{d_date}</span>{badge_html}</td>"

        for p, _ in LESSON_TIMES:
            text = day["pairs"].get(p, "")
            cells += f"<td><div class='cell-content'>{text}</div></td>"

        rows_html += f"<tr>{cells}</tr>"

    theme_class = "light" if theme == "light" else "dark"

    html = HTML_TEMPLATE.format(
        theme_class=theme_class,
        group=group_name,
        date_range=date_range,
        week_num=week_num,
        header_cols=header_cols,
        table_rows=rows_html
    )

    clean_group = to_clean_filename(group_name)
    filename = f"schedule_{clean_group}_{week_num}_{theme}.png"

    hti.screenshot(html_str=html, save_as=filename)
    return str(DATA_DIR / filename)