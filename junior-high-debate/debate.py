#!/usr/bin/env python3
"""
中学受験相談 マルチエージェント討論アプリ

Usage:
    python debate.py [--rounds N] [--premise FILE]
"""

import argparse
import os
import sys
from datetime import datetime

import anthropic
from colorama import Fore, Style, init as colorama_init

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1000

DEFAULT_PREMISE = (
    "小3・5月時点の中学受験生。4科偏差値59.9。算数57.1（安定A）、"
    "理科67.6（ただし平均34.7の難回でブレ大・1位）、国語53.7（前回59.2から低下しB）、"
    "社会58.8。構造を理解して自分で学ぶ自走型。通学は三鷹・吉祥寺から60分以内。"
    "男子校・共学とも検討可。問い：このまま進めばどこまで伸ばせるか、どう育てるべきか。"
)

AGENTS = [
    {
        "id": "teacher",
        "name": "塾講師",
        "color": Fore.YELLOW,
        "system": (
            "あなたは中学受験専門の塾講師です。中学受験を「競争」として捉え、"
            "偏差値・志望校・科目別配点に基づいた具体的なアドバイスを行います。"
            "算数を最重点科目として位置づけ、到達可能な志望校を根拠とともに示します。"
            "誇張せず、データに基づいた分析のみを述べてください。"
            "他の発言者の意見があれば、必要に応じて反論や補足をしてください。"
            "回答は200〜300文字以内にまとめてください。"
        ),
    },
    {
        "id": "educator",
        "name": "教育者",
        "color": Fore.GREEN,
        "system": (
            "あなたは子どもの教育全般を専門とする教育者です。"
            "偏差値よりも知的好奇心・自己動機・長期的な幸福を重視します。"
            "小3時点の成績の不確実性（まだ3年以上先の試験）と、"
            "詰め込み教育・過度な負荷がもたらすリスクを冷静に指摘してください。"
            "塾講師など他の発言者の主張に疑問を呈することも辞しません。"
            "回答は200〜300文字以内にまとめてください。"
        ),
    },
    {
        "id": "consultant",
        "name": "キャリアコンサル",
        "color": Fore.CYAN,
        "system": (
            "あなたはキャリアコンサルタントです。"
            "「20年後の人生」という視点から中学受験の目標そのものを問い直します。"
            "本人の自律性、家族の消耗、「誰のための目標か」という問いを中心に据えます。"
            "大学附属校（例：明治大学付属明治・法政大学付属など）といった"
            "長期的な現実解を一つ具体的に提案してください。"
            "他の発言者への言及も歓迎します。"
            "回答は200〜300文字以内にまとめてください。"
        ),
    },
]

INTEGRATOR = {
    "id": "integrator",
    "name": "統合役",
    "color": Fore.MAGENTA,
    "system": (
        "あなたは議論の統合役です。"
        "これまでの3名（塾講師・教育者・キャリアコンサル）の発言を読み、"
        "それぞれの主張の利点と問題点を公平にまとめてください。"
        "対立点を明示したうえで、統合的な結論を示してください。"
        "「みんな正しい」式の表面的な結論（予定調和）は避け、"
        "トレードオフを正直に示してください。\n"
        "構成：(1) 各見解の長所・短所、(2) 統合的結論\n"
        "回答は400〜600文字以内にまとめてください。"
    ),
}


def build_user_message(premise: str, history: list[dict]) -> str:
    lines = [f"【前提・状況】\n{premise}"]

    if history:
        lines.append("\n【これまでの発言】")
        for entry in history:
            round_label = entry["round"]
            label = f"ラウンド{round_label}" if isinstance(round_label, int) else round_label
            lines.append(f"■ {entry['name']}（{label}）\n{entry['text']}")

    lines.append("\nあなたの発言をしてください。前の発言者を踏まえて反応してください。")
    return "\n".join(lines)


def build_integrator_message(premise: str, history: list[dict]) -> str:
    lines = [f"【前提・状況】\n{premise}", "\n【討論の全発言記録】"]
    for entry in history:
        round_label = entry["round"]
        label = f"ラウンド{round_label}" if isinstance(round_label, int) else round_label
        lines.append(f"■ {entry['name']}（{label}）\n{entry['text']}")
    lines.append("\n上記の議論を踏まえ、統合的なまとめを行ってください。")
    return "\n".join(lines)


def call_agent(client: anthropic.Anthropic, agent: dict, user_message: str) -> str:
    print(f"\n{agent['color']}{'=' * 60}")
    print(f"  {agent['name']}")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")

    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=agent["system"],
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
        full_text = stream.get_final_message().content[0].text

    print("\n")
    return full_text


def run_debate(client: anthropic.Anthropic, premise: str, rounds: int) -> list[dict]:
    history: list[dict] = []

    for round_num in range(1, rounds + 1):
        print(f"\n{Fore.WHITE}{'#' * 60}")
        print(f"  ラウンド {round_num} / {rounds}")
        print(f"{'#' * 60}{Style.RESET_ALL}")

        for agent in AGENTS:
            user_msg = build_user_message(premise, history)
            text = call_agent(client, agent, user_msg)
            history.append({
                "name": agent["name"],
                "round": round_num,
                "text": text,
                "timestamp": datetime.now().isoformat(),
            })

    print(f"\n{Fore.WHITE}{'#' * 60}")
    print("  統合まとめ")
    print(f"{'#' * 60}{Style.RESET_ALL}")

    integrator_msg = build_integrator_message(premise, history)
    integrator_text = call_agent(client, INTEGRATOR, integrator_msg)
    history.append({
        "name": INTEGRATOR["name"],
        "round": "統合",
        "text": integrator_text,
        "timestamp": datetime.now().isoformat(),
    })

    return history


def save_debate_log(premise: str, history: list[dict], rounds: int) -> str:
    now = datetime.now()
    filename = "debate_log.md"

    lines = [
        "# 中学受験相談 討論ログ",
        "",
        f"**実施日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**ラウンド数**: {rounds}  ",
        f"**モデル**: {MODEL}  ",
        "",
        "---",
        "",
        "## 前提・状況",
        "",
        premise,
        "",
        "---",
        "",
        "## 討論記録",
    ]

    current_round = None
    for entry in history:
        round_label = entry["round"]
        if round_label != current_round:
            current_round = round_label
            if round_label == "統合":
                lines += ["", "---", "", "## 統合まとめ", ""]
            else:
                lines += ["", f"## ラウンド {round_label}", ""]

        lines += [
            f"### {entry['name']}",
            f"*{entry['timestamp']}*",
            "",
            entry["text"],
            "",
        ]

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filename


def load_premise(path: str | None) -> str:
    if path is not None:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(script_dir, "premise.txt")
    if os.path.exists(default_path):
        with open(default_path, encoding="utf-8") as f:
            return f.read().strip()

    return DEFAULT_PREMISE


def main() -> None:
    colorama_init()

    parser = argparse.ArgumentParser(
        description="中学受験相談 マルチエージェントAI討論"
    )
    parser.add_argument(
        "--rounds", type=int, default=2,
        help="討論ラウンド数 (デフォルト: 2)",
    )
    parser.add_argument(
        "--premise", type=str, default=None,
        help="前提テキストファイルのパス (デフォルト: premise.txt)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "エラー: 環境変数 ANTHROPIC_API_KEY が設定されていません。\n"
            "  export ANTHROPIC_API_KEY='your-api-key' を実行してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    premise = load_premise(args.premise)

    print(f"\n{Fore.WHITE}{'=' * 60}")
    print("  中学受験相談 マルチエージェント討論")
    print(f"  ラウンド数: {args.rounds}")
    print(f"{'=' * 60}{Style.RESET_ALL}")
    print(f"\n【前提】\n{premise}\n")

    history = run_debate(client, premise, args.rounds)

    log_path = save_debate_log(premise, history, args.rounds)
    print(f"{Fore.WHITE}討論ログを保存しました: {log_path}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
