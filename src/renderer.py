from html2image import Html2Image
from src.config import DATA_DIR, LESSON_TIMES

hti = Html2Image(output_path=str(DATA_DIR), size=(1380, 780))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        padding: 16px;
        background-color: #0c131d;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #ffffff;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 19px;
        font-weight: 600;
        margin-bottom: 12px;
        padding: 0 4px;
    }}
    .bot-name {{
        color: #64748b;
        font-weight: 400;
        font-size: 16px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}
    th, td {{
        border: 1px solid #1e2c3d;
        text-align: center;
        padding: 6px 4px;
        vertical-align: middle;
    }}
    th {{
        background-color: #121d2b;
        color: #94a3b8;
        font-weight: 500;
        font-size: 13px;
    }}
    th span {{
        display: block;
        font-size: 11px;
        color: #64748b;
        margin-top: 2px;
    }}
    .day-col {{
        width: 65px;
        font-weight: bold;
        background-color: #121d2b;
        font-size: 15px;
        color: #f1f5f9;
    }}
    .day-date {{
        font-size: 11px;
        font-weight: normal;
        color: #94a3b8;
        display: block;
        margin-top: 4px;
    }}
    .cell-content {{
        font-size: 11px;
        line-height: 1.25;
        color: #e2e8f0;
        word-wrap: break-word;
        white-space: pre-wrap;
    }}
</style>
</head>
<body>
    <div class="header">
        <div>Расписание: <span style="color: #38bdf8;">{group}</span></div>
        <div class="bot-name">Расписание занятий</div>
        <div>{date_range} &nbsp;|&nbsp; Неделя {week_num}</div>
    </div>
    <table>
        <tr>
            <th class="day-col">Пара<br><span style="color:#64748b">Время</span></th>
            {header_cols}
        </tr>
        {table_rows}
    </table>
</body>
</html>
"""

def render_schedule_image(group_name: str, week_num: int, days_data, date_range: str, dates_list: list) -> str:
    header_cols = "".join([f"<th>{num}<span>{time}</span></th>" for num, time in LESSON_TIMES])

    rows_html = ""
    for i, day in enumerate(days_data):
        d_date = dates_list[i] if i < len(dates_list) else ""
        cells = f"<td class='day-col'>{day['name']}<span class='day-date'>{d_date}</span></td>"

        for p, _ in LESSON_TIMES:
            text = day["pairs"].get(p, "")
            cells += f"<td><div class='cell-content'>{text}</div></td>"

        rows_html += f"<tr>{cells}</tr>"

    html = HTML_TEMPLATE.format(
        group=group_name,
        date_range=date_range,
        week_num=week_num,
        header_cols=header_cols,
        table_rows=rows_html
    )

    clean_group = group_name.replace("/", "_")
    filename = f"schedule_{clean_group}_{week_num}.png"
    hti.screenshot(html_str=html, save_as=filename)
    return str(DATA_DIR / filename)