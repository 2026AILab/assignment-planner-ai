# ============================================
# 1. 道具を読みこむ（os / gradio / OpenAI を使えるようにする）
# ============================================
import os
import re
import gradio as gr
from openai import OpenAI


def parse_items(text):
    normalized = text.replace("、", "\n").replace(",", "\n").replace("，", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def format_numbered(items):
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))


def normalize_schedule_text(text):
    days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
    normalized = text
    for day in days:
        normalized = re.sub(rf"{day}：\s*\n\s*", f"{day}：", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


# ============================================
# 2. AIとつなぐ準備をする
# ============================================
BASE_URL = "https://education-demo-app.services.ai.azure.com/openai/v1"
API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("環境変数 AZURE_OPENAI_API_KEY が設定されていません。")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ============================================
# 3. AIの役割・出力フォーマットを決める
# ============================================
system_prompt = """
あなたは月曜日から金曜日までのスケジュールを提案するアシスタントです。
ユーザーから受け取った条件に合わせて、余裕をもって進められるスケジュールを2つ提案してください。

【スケジュール1】
名：（特徴がわかる名前）
月曜日：
火曜日：
水曜日：
木曜日：
金曜日：

【スケジュール2】
名：（特徴がわかる名前）
月曜日：
火曜日：
水曜日：
木曜日：
金曜日：

注意事項：
- 必ず2つ提案する
- 課題の期限は同じ番号の課題のものです。
- 予定のある曜日には課題をあまり多く入れず、時間などを指定してください
- 特に力を入れたい課題を多めに入れる。
- 各曜日の「月曜日：」などの行には、必ず具体的な予定内容、課題を1から2個入れてください。
- 「（最大2個...）」のような説明文は出力しないでください。
- 月曜日から金曜日の各行は、必ず「曜日：内容」の1行で書いてください。
- 「月曜日：」の直後で改行せず、同じ行に内容を書いてください。
"""


# ============================================
# 4. ボタンが押されるたびに呼ばれる関数を定義する
# ============================================
def teian(work_raw, school, time_zone, limit_raw):
    work_items = parse_items(work_raw)
    limit_items = parse_items(limit_raw)

    if len(limit_items) < len(work_items):
        limit_items.extend(["未設定"] * (len(work_items) - len(limit_items)))
    elif len(limit_items) > len(work_items):
        limit_items = limit_items[: len(work_items)]

    work = format_numbered(work_items) if work_items else "1. なし"
    limit = format_numbered(limit_items) if work_items else "1. なし"

    user_prompt = f"""
    次の条件で月曜日から金曜日までのスケジュールを2つ提案してください。

    やるべき課題：{work}
    予定のある日：{school}
    特に力を入れたい課題：{time_zone}
    課題の期限：{limit}
    """

    res = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return normalize_schedule_text(res.output_text)


# ============================================
# 5. 入力欄つきの画面を作成して起動する
# ============================================
gr.Interface(
    fn=teian,
    inputs=[
        gr.Textbox(label="やるべき課題（カンマ区切り）", placeholder="英語のワーク, 数学の問題集"),
        gr.Textbox(label="予定のある日", placeholder="月曜日など"),
        gr.Textbox(label="特に力を入れたい課題", placeholder="数学の問題集"),
        gr.Textbox(label="課題の期限（課題と同じ順番でカンマ区切り）", placeholder="金曜日, 木曜日"),],
    outputs=gr.Textbox(label="1週間のスケジュール提案", lines=16),
    title="課題スケジュール提案AI",
    submit_btn="スケジュールを提案してもらう",
).launch(share=True, auth=("student", "edu2026"))