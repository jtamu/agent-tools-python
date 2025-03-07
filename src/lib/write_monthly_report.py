import openpyxl
import openpyxl.cell
from pydantic import BaseModel
from datetime import date, datetime
from typing import List


class DailyWorkInfo(BaseModel):
    date: str
    start_at: str
    end_at: str
    rest_time: str
    work_details: str

example_infos = [
    DailyWorkInfo(date="2025-02-03", start_at="10:00", end_at="20:00", rest_time="1:00", work_details="ほげほげ"),
    DailyWorkInfo(date="2025-02-05", start_at="10:00", end_at="20:00", rest_time="1:00", work_details="テストテスト"),
]


TARGET_MONTH_CELL_POSITION = "J3"
PARTICIPATING_COMPANY_CELL_POSITION = "J4"
WORKER_CELL_POSITION = "J6"
DATE_COL = "B"
START_AT_COL = "E"
END_AT_COL = "F"
REST_TIME_COL = "G"
WORK_DETAILS_COL = "I"
MONTHLY_REPORT_TEMPLATE_PATH = "../../data/templates/monthly_work_report_template.xlsx"
REPORT_SHEET_NAME = "作業報告書"
MONTHLY_REPORT_OUTPUT_PATH = "../../data/outputs/作業報告書_{worker}_{target_month}.xlsx"


def write_monthly_report(worker: str, participating_company: str, target_month: str, infos: List[DailyWorkInfo]):
    # テンプレートの年月だけ先に更新して上書き保存
    # NOTE: 月日を反映させるため、関数をそのまま読み込む必要がある
    # wb = openpyxl.load_workbook(MONTHLY_REPORT_TEMPLATE_PATH)
    # ws = wb[REPORT_SHEET_NAME]

    # target_month_cell = ws[TARGET_MONTH_CELL_POSITION]
    # target_month_cell.value = datetime.strptime(target_month, "%Y%m")

    # wb.save(MONTHLY_REPORT_TEMPLATE_PATH)


    wb = openpyxl.load_workbook(MONTHLY_REPORT_TEMPLATE_PATH, data_only=True)
    ws = wb[REPORT_SHEET_NAME]

    participating_company_cell = ws[PARTICIPATING_COMPANY_CELL_POSITION]
    participating_company_cell.value = participating_company

    worker_name_cell = ws[WORKER_CELL_POSITION]
    worker_name_cell.value = worker

    # target_month_cell = ws[TARGET_MONTH_CELL_POSITION]
    # target_month_cell.value = datetime.strptime(target_month, "%Y%m")

    date_col = ws[DATE_COL]

    for info in infos:
        for date_cell in date_col:
            if isinstance(date_cell, openpyxl.cell.MergedCell) or not isinstance(date_cell.value, date):
                continue

            date_str = date_cell.value.strftime("%Y-%m-%d")
            if date_str == info.date:
                start_at_cell = ws[f"{START_AT_COL}{date_cell.row}"]
                start_at_cell.value = info.start_at

                end_at_cell = ws[f"{END_AT_COL}{date_cell.row}"]
                end_at_cell.value = info.end_at

                rest_time_cell = ws[f"{REST_TIME_COL}{date_cell.row}"]
                rest_time_cell.value = info.rest_time

                work_details_cell = ws[f"{WORK_DETAILS_COL}{date_cell.row}"]
                work_details_cell.value = info.work_details

    wb.save(MONTHLY_REPORT_OUTPUT_PATH.format(worker=worker, target_month=target_month))


if __name__ == "__main__":
    write_monthly_report("山田太郎", "EXAMPLE株式会社", "202502", example_infos)
