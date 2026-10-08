from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="JLPT N3 漢字学習アプリ",
    page_icon="漢",
    layout="wide",
)


REQUIRED_COLUMNS = [
    "id",
    "mondai_type",
    "sentence",
    "target",
    "choices",
    "answer",
    "explanation",
]


DEFAULT_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": 1,
        "mondai_type": "Mondai 1",
        "sentence": "来週の【予定】を確認してください。",
        "target": "予定",
        "choices": ["よてい", "ようてい", "よて", "よじょう"],
        "answer": "よてい",
        "explanation": "「予定」は「よてい」と読みます。「予」は「よ」、「定」は「てい」です。",
    },
    {
        "id": 2,
        "mondai_type": "Mondai 1",
        "sentence": "駅の近くに新しい店が【開店】しました。",
        "target": "開店",
        "choices": ["かいてん", "かいでん", "ひらてん", "かいて"],
        "answer": "かいてん",
        "explanation": "「開店」は「かいてん」と読みます。「開」は「かい」、「店」は「てん」です。",
    },
    {
        "id": 3,
        "mondai_type": "Mondai 1",
        "sentence": "健康のために毎日【運動】しています。",
        "target": "運動",
        "choices": ["うんどう", "うんとう", "うどう", "うんど"],
        "answer": "うんどう",
        "explanation": "「運動」は「うんどう」と読みます。「運」は「うん」、「動」は「どう」です。",
    },
    {
        "id": 4,
        "mondai_type": "Mondai 2",
        "sentence": "この薬は食後に【のんで】ください。",
        "target": "のんで",
        "choices": ["飲んで", "食んで", "飯んで", "読んで"],
        "answer": "飲んで",
        "explanation": "「のむ」は「飲む」と書きます。そのて形は「飲んで」です。",
    },
    {
        "id": 5,
        "mondai_type": "Mondai 2",
        "sentence": "明日の朝、駅で友達に【あいます】。",
        "target": "あいます",
        "choices": ["会います", "合います", "開います", "回います"],
        "answer": "会います",
        "explanation": "人に「あう」は「会う」と書きます。したがって「会います」が正解です。",
    },
    {
        "id": 6,
        "mondai_type": "Mondai 2",
        "sentence": "毎晩、本を【よんで】から寝ます。",
        "target": "よんで",
        "choices": ["読んで", "話んで", "語んで", "聞んで"],
        "answer": "読んで",
        "explanation": "本を「よむ」は「読む」と書きます。そのて形は「読んで」です。",
    },
]


def initialize_session_state() -> None:
    if "questions" not in st.session_state:
        st.session_state.questions = [
            question.copy() for question in DEFAULT_QUESTIONS
        ]

    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if "score" not in st.session_state:
        st.session_state.score = 0

    if "total_questions" not in st.session_state:
        st.session_state.total_questions = 0

    if "percentage" not in st.session_state:
        st.session_state.percentage = 0.0


def questions_to_dataframe(
    questions: list[dict[str, Any]],
) -> pd.DataFrame:
    rows = []

    for question in questions:
        row = question.copy()

        if isinstance(row.get("choices"), list):
            row["choices"] = " / ".join(
                str(choice) for choice in row["choices"]
            )

        rows.append(row)

    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS)


def normalize_question(
    question: dict[str, Any],
) -> dict[str, Any]:
    normalized = question.copy()

    choices = normalized.get("choices", [])

    if isinstance(choices, str):
        choices = [
            choice.strip()
            for choice in choices.split("|")
            if choice.strip()
        ]

    normalized["choices"] = list(choices)

    return normalized


def get_next_question_id() -> int:
    existing_ids = []

    for question in st.session_state.questions:
        try:
            existing_ids.append(int(question["id"]))
        except (KeyError, TypeError, ValueError):
            continue

    return max(existing_ids, default=0) + 1


def get_filtered_questions(
    mondai_filter: str,
) -> list[dict[str, Any]]:
    questions = [
        normalize_question(question)
        for question in st.session_state.questions
    ]

    if mondai_filter == "すべて":
        return questions

    return [
        question
        for question in questions
        if question.get("mondai_type") == mondai_filter
    ]


def validate_new_question(
    mondai_type: str,
    sentence: str,
    target: str,
    choices: list[str],
    answer: str,
    explanation: str,
) -> list[str]:
    errors = []

    if mondai_type not in {"Mondai 1", "Mondai 2"}:
        errors.append("問題形式を選択してください。")

    if not sentence.strip():
        errors.append("例文を入力してください。")

    if not target.strip():
        errors.append("出題語を入力してください。")

    if len(choices) != 4:
        errors.append("選択肢は4つ入力してください。")

    if any(not choice.strip() for choice in choices):
        errors.append("4つの選択肢をすべて入力してください。")

    if len(set(choices)) != 4:
        errors.append("4つの選択肢はそれぞれ異なる内容にしてください。")

    if not answer.strip():
        errors.append("正解を入力してください。")

    if answer not in choices:
        errors.append("正解は4つの選択肢の中から選んでください。")

    if not explanation.strip():
        errors.append("解説を入力してください。")

    if target.strip():
        expected = f"【{target.strip()}】"

        if expected not in sentence:
            errors.append(
                f"例文には出題語を {expected} の形式で入れてください。"
            )

    return errors


def render_results(
    questions: list[dict[str, Any]],
) -> None:
    score = int(st.session_state.score)
    total = int(st.session_state.total_questions)
    percentage = float(st.session_state.percentage)

    st.divider()
    st.header("採点結果")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("正解数", f"{score} / {total}")

    with col2:
        st.metric("正答率", f"{percentage:.1f}%")

    with col3:
        if percentage >= 80:
            evaluation = "Excellent"
        elif percentage >= 60:
            evaluation = "Good"
        else:
            evaluation = "要復習"

        st.metric("評価", evaluation)

    st.subheader("解答・解説")

    for index, question in enumerate(questions, start=1):
        question_id = question["id"]

        user_answer = st.session_state.user_answers.get(
            question_id
        )

        correct_answer = question["answer"]

        if user_answer == correct_answer:
            st.success(
                f"問題 {index}: 正解！ "
                f"あなたの答え：{user_answer}"
            )

        elif user_answer is None:
            st.error(
                f"問題 {index}: 未回答。 "
                f"正解：{correct_answer}"
            )

        else:
            st.error(
                f"問題 {index}: 不正解。 "
                f"あなたの答え：{user_answer} / "
                f"正解：{correct_answer}"
            )

        st.info(question["explanation"])


def render_test_mode() -> None:
    st.header("JLPT N3 漢字テスト")

    st.write(
        "Mondai 1 は漢字の読み、Mondai 2 はひらがなに対応する"
        "漢字を選ぶ問題です。"
    )

    selected_filter = st.selectbox(
        "問題形式で絞り込む",
        options=["すべて", "Mondai 1", "Mondai 2"],
        key="test_filter",
    )

    filtered_questions = get_filtered_questions(
        selected_filter
    )

    if not filtered_questions:
        st.warning(
            "現在、この条件に該当する問題はありません。"
        )
        return

    st.info(
        f"表示問題数：{len(filtered_questions)}問"
    )

    with st.form("kanji_test_form"):
        for index, question in enumerate(
            filtered_questions,
            start=1,
        ):
            st.subheader(
                f"問題 {index} — {question['mondai_type']}"
            )

            st.markdown(
                f"**{question['sentence']}**"
            )

            st.radio(
                "答えを1つ選んでください。",
                options=question["choices"],
                key=f"question_{question['id']}",
                index=None,
            )

        submitted = st.form_submit_button(
            "回答を提出して採点する",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        user_answers = {}
        score = 0

        for question in filtered_questions:
            question_id = question["id"]

            answer_key = f"question_{question_id}"

            selected_answer = st.session_state.get(
                answer_key
            )

            user_answers[question_id] = selected_answer

            if selected_answer == question["answer"]:
                score += 1

        total = len(filtered_questions)

        percentage = (
            score / total * 100
            if total > 0
            else 0.0
        )

        st.session_state.user_answers = user_answers
        st.session_state.score = score
        st.session_state.total_questions = total
        st.session_state.percentage = percentage
        st.session_state.submitted = True

        st.rerun()

    if st.session_state.submitted:
        render_results(filtered_questions)


def render_database_mode() -> None:
    st.header("漢字データベース & 管理")

    st.write(
        "現在登録されているJLPT N3漢字問題を確認できます。"
    )

    dataframe = questions_to_dataframe(
        st.session_state.questions
    )

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("新しい問題を追加")

    with st.form(
        "add_question_form",
        clear_on_submit=True,
    ):
        mondai_type = st.selectbox(
            "問題形式",
            options=["Mondai 1", "Mondai 2"],
        )

        sentence = st.text_input(
            "例文",
            placeholder="例：来週の【予定】を確認してください。",
        )

        target = st.text_input(
            "出題語",
            placeholder="例：予定",
        )

        st.markdown("**選択肢（4つ）**")

        col1, col2 = st.columns(2)

        with col1:
            choice_1 = st.text_input("選択肢 1")
            choice_2 = st.text_input("選択肢 2")

        with col2:
            choice_3 = st.text_input("選択肢 3")
            choice_4 = st.text_input("選択肢 4")

        answer_number = st.selectbox(
            "正解",
            options=[
                "選択肢 1",
                "選択肢 2",
                "選択肢 3",
                "選択肢 4",
            ],
        )

        explanation = st.text_area(
            "解説",
            placeholder="この問題の読み方・漢字の使い方などを説明してください。",
        )

        add_submitted = st.form_submit_button(
            "問題を追加",
            type="primary",
            use_container_width=True,
        )

    if add_submitted:
        choices = [
            choice_1.strip(),
            choice_2.strip(),
            choice_3.strip(),
            choice_4.strip(),
        ]

        answer_index_map = {
            "選択肢 1": 0,
            "選択肢 2": 1,
            "選択肢 3": 2,
            "選択肢 4": 3,
        }

        answer_index = answer_index_map[
            answer_number
        ]

        selected_answer = choices[answer_index]

        errors = validate_new_question(
            mondai_type=mondai_type,
            sentence=sentence,
            target=target,
            choices=choices,
            answer=selected_answer,
            explanation=explanation,
        )

        if errors:
            for error in errors:
                st.error(error)
        else:
            new_question = {
                "id": get_next_question_id(),
                "mondai_type": mondai_type,
                "sentence": sentence.strip(),
                "target": target.strip(),
                "choices": choices,
                "answer": selected_answer,
                "explanation": explanation.strip(),
            }

            st.session_state.questions.append(
                new_question
            )

            st.session_state.user_answers = {}
            st.session_state.submitted = False
            st.session_state.score = 0
            st.session_state.total_questions = 0
            st.session_state.percentage = 0.0

            st.rerun()

    st.divider()

    st.subheader("CSVエクスポート")

    export_dataframe = questions_to_dataframe(
        st.session_state.questions
    )

    csv_text = export_dataframe.to_csv(
        index=False
    )

    csv_data = csv_text.encode("utf-8-sig")

    st.download_button(
        label="jlpt_n3_kanji_dataset.csv をダウンロード",
        data=csv_data,
        file_name="jlpt_n3_kanji_dataset.csv",
        mime="text/csv",
        use_container_width=True,
    )


# Initialize application state.
initialize_session_state()


# Application title.
st.title("JLPT N3 漢字学習・研究アプリ")

st.caption(
    "卒業研究 — JLPT N3 Kanji Learning & Test System"
)


# Main tabs.
tab_test, tab_database = st.tabs(
    [
        "📚 JLPT N3 Kanji Test Mode",
        "🗃️ Kanji Database & Management",
    ]
)


with tab_test:
    render_test_mode()


with tab_database:
    render_database_mode()