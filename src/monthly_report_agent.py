import os
import operator
from typing import Optional, Annotated, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph
from lib.daily_work_info import DailyWorkInfo
from lib.find_report_files import find_report_files, read_file_contents
from lib.write_monthly_report import validate_report_within_target_month, write_monthly_report


class MonthlyReportState(BaseModel):
    target_year_month: str = Field(description="対象年月")
    query: str = Field(description="作業日報")
    is_within_target_date_range: bool = Field(default=False, description="対象年月の範囲内かどうかの判定結果")
    extracted_daily_report: str = Field(default="", description="抽出された作業日報")
    daily_work_infos: Annotated[List[DailyWorkInfo], operator.add] = Field(default=[], description="作業日報データのリスト")


class WithinTargetDateRangeJudgement(BaseModel):
    judge: bool = Field(description="判定結果")
    reason: str = Field(description="判定理由")


def determine_within_target_date_range(state: MonthlyReportState) -> dict[str, bool]:
    model = ChatOpenAI(model="gpt-4o", temperature=0.0)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "与えられた作業日報が、指定年月のものであるかを判断してください。",
        ),
        (
            "human",
            """
            指定年月: {target_year_month}

            作業日報:
            {query}
            """
        )
    ])

    chain = prompt | model.with_structured_output(WithinTargetDateRangeJudgement)
    result: WithinTargetDateRangeJudgement = chain.invoke({
        "query": state.query,
        "target_year_month": state.target_year_month,
    })
    return {"is_within_target_date_range": result.judge}


def extract_daily_report(state: MonthlyReportState) -> dict[str, str]:
    reasoning_model = ChatOpenAI(model="gpt-4o", temperature=0.0)

    extract_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """与えられた作業日報から、以下のデータを抽出してください。
            1. 報告日
                - "2025-03-07"形式で返却してください。
            2. 開始時刻
                - "10:00"固定としてください。
            3. 勤務時間
                - 「本日の業務内容」の「実績工数」の合計で算出してください。
                - "1:00"形式で返却してください。
            4. 規定休憩時間
                - "1:00"固定としてください。
            5. 社内業務
                - 「社内MTG」などの時間が記載されている場合は、その時間を足して算出してください。
                - "1:00"形式で返却してください。
            6. 休憩時間
                - 4.と5.の結果を足して算出してください（社内業務は現場の勤務時間には含まれないため）。
                - "1:00"形式で返却してください。
            7. 終了時刻
                - 開始時刻から3.と6.の合計を足して算出してください。
            8. 業務内容
                - 「本日の業務内容」に記載の業務内容のうち、最も実績工数が大きいもの

            注意点:
            - 「本日の業務内容」には、複数の項目が記載されている場合があるため、見落とさないよう注意してください。"""
        ),
        (
            "human",
            "{query}",
        )
    ])

    extract_chain = extract_prompt | reasoning_model | StrOutputParser()
    result = extract_chain.invoke({"query": state.query})
    return {"extracted_daily_report": result}


def convert_daily_work_info(state: MonthlyReportState) -> dict[str, List[DailyWorkInfo]]:
    model = ChatOpenAI(model="gpt-4o", temperature=0.0)

    convert_prompt = ChatPromptTemplate.from_template("""
    与えられた業務日報の抽出データから、適切なフォーマットに変換してください。
    注意点:
    - 業務内容に時間の情報は含めないでください。

    抽出データ:
    {extracted_data}
    """)

    convert_chain = convert_prompt | model.with_structured_output(DailyWorkInfo)
    convert_result = convert_chain.invoke({"extracted_data": state.extracted_daily_report})
    return {"daily_work_infos": [convert_result]}


def compile_workflow() -> CompiledGraph:
    workflow = StateGraph(MonthlyReportState)

    workflow.add_node("determine_within_target_date_range", determine_within_target_date_range)
    workflow.add_node("extract_daily_report", extract_daily_report)
    workflow.add_node("convert_daily_work_info", convert_daily_work_info)

    workflow.set_entry_point("determine_within_target_date_range")
    workflow.add_conditional_edges(
        "determine_within_target_date_range",
        lambda state: state.is_within_target_date_range,
        {
            True: "extract_daily_report",
            False: END,
        }
    )
    workflow.add_edge("extract_daily_report", "convert_daily_work_info")
    workflow.add_edge("convert_daily_work_info", END)

    compiled = workflow.compile()
    return compiled


def main():
    validate_report_within_target_month("202502")

    compiled = compile_workflow()

    data_path = os.getenv("ROOT_DIR") + "/data"
    report_files = find_report_files(f"{data_path}/inputs/example/202502")

    state = None
    for file in report_files:
        contents = read_file_contents(file)
        if not state:
            state = MonthlyReportState(target_year_month="202502", query=contents)
        else:
            state.query = contents

        result = compiled.invoke(state)
        state = MonthlyReportState(**result)

    write_monthly_report("山田太郎", "EXAMPLE株式会社", "202502", state.daily_work_infos)


if __name__ == "__main__":
    main()
