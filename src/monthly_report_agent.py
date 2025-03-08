import operator
from typing import Optional, Annotated, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from lib.daily_work_info import DailyWorkInfo


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
            state.query,
        )
    ])

    extract_chain = extract_prompt | reasoning_model | StrOutputParser()
    result = extract_chain.invoke({})
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


def main():
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

    initial_state = MonthlyReportState(
        target_year_month="202503",
        query="""
        # EXAMPLE日報

        日報No.494

        プロジェクト名：EXAMPLEプロジェクト
        報告日：2025年03月07日(金)

        ## **本日の業務内容**

        * **1. 文言修正**
        * (実績工数) 2.0h
        * (作業進捗率)
        * (作業内容) 文言修正
        * (所感) ローカル確認まで完了

        * **2. APIの設計**
        * (実績工数) 5.5h
        * (作業進捗率)
        * (作業内容) 多言語を考慮した設計
        * (所感) 一旦言語ごとにCSVを分ける形にした

        * **本日の残業予定**
        * なし

        ## **翌営業日の作業予定**

        * **1. サービスに渡す変数が多すぎるのでDTOにまとめたい**
        * (予定工数)
        * (完了目標)
        * (作業内容) サービスに渡す変数が多すぎるのでDTOにまとめたい

        # **My KPT**

        ## **KEEP(今日の作業でよかったこと/継続して実施していきたいこと)**
        * 特になし

        ## **PROBLEM(今日の作業の問題点/解決すべきこと)**
        * チェックボックスはスペースで入力できることを知らなかった

        ## **TRY(翌営業日以降、取り込んでいく作業実行)**
        * 覚えておく

        # **その他**
        * 社内MTG 0.5h
        """
    )

    result = compiled.invoke(initial_state)
    print(result)


if __name__ == "__main__":
    main()
