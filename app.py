# app.py
import os
import re
import json
from typing import Any, Dict, List

import streamlit as st
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# =========================
# MCP citation 抽出ロジック
# =========================

MCP_CITATION_JSON_RE = re.compile(
    r"【(\d+):(\d+)†([^】]+)】\s*(\{.*?\})",
    re.DOTALL,
)


def extract_mcp_chunk_map(resp) -> Dict[str, Dict[str, str]]:
    """
    citation → {title, chunk} の辞書を返す
    例:
    {
        "4:0†source": {
            "title": "〇〇ドキュメント",
            "chunk": "本文..."
        }
    }
    """
    chunk_map: Dict[str, Dict[str, str]] = {}

    for item in resp.output:
        if getattr(item, "type", None) != "mcp_call":
            continue

        output_str = getattr(item, "output", "") or ""

        for m in MCP_CITATION_JSON_RE.finditer(output_str):
            key = f"{m.group(1)}:{m.group(2)}†{m.group(3)}"
            json_str = m.group(4)

            try:
                data = json.loads(json_str)
            except Exception:
                continue

            chunk_map[key] = {
                "title": data.get("title", "(no title)"),
                "chunk": data.get("chunk", ""),
            }

    return chunk_map


# =========================
# Agent 呼び出し関数
# =========================


def call_foundry_agent(
    user_message: str,
    history: List[Dict[str, str]],
) -> tuple[str, Dict[str, str]]:
    """
    Azure AI Foundry Agent を叩いてレスポンス文字列と
    MCP citation → chunk のマップを返す
    """

    # 環境変数から設定を読む（なければデフォルト）
    project_endpoint = os.environ.get(
        "AZURE_AI_PROJECT_ENDPOINT",
        "https://handson-aifoundry-sc.services.ai.azure.com/api/projects/handson-project",
    )
    agent_name = os.environ.get("AZURE_AI_AGENT_NAME", "knowledge-agent")

    credential = DefaultAzureCredential()

    # 今回は毎回クライアントを作るシンプル実装
    with AIProjectClient(
        endpoint=project_endpoint, credential=credential
    ) as project_client:
        agent = project_client.agents.get(agent_name=agent_name)

        with project_client.get_openai_client() as openai_client:
            # history + 今回の user メッセージ を Responses API 形式に変換
            input_messages = [
                {"role": m["role"], "content": m["content"]} for m in history
            ]
            input_messages.append({"role": "user", "content": user_message})

            response = openai_client.responses.create(
                input=input_messages,
                # 「この Foundry Agent を使え」と指示
                extra_body={
                    "agent": {
                        "name": agent.name,
                        "type": "agent_reference",
                        # MCP の承認を全部自動にしたい場合
                        "require_approval": "never",
                    }
                },
            )

    # 通常のテキスト出力は output_text で取れる
    assistant_text = getattr(response, "output_text", "") or "(no text)"

    # MCP citation → chunk map
    chunk_map = extract_mcp_chunk_map(response)

    return assistant_text, chunk_map


# =========================
# Streamlit UI 本体
# =========================


def main():
    st.set_page_config(page_title="Foundry Agent Chat", page_icon="💬")

    st.title("💬 Azure AI Foundry Agent Chat (Streamlit)")

    st.caption(
        "Azure AI Foundry Agent + Responses API を使った簡易チャット UI（MCP citation 表示付き）"
    )

    # セッションにメッセージ履歴を保持
    if "messages" not in st.session_state:
        st.session_state.messages: List[Dict[str, str]] = [
            {
                "role": "assistant",
                "content": "こんにちは！Azure AI Foundry Agent へのチャットです。",
            }
        ]

    if "last_chunk_map" not in st.session_state:
        st.session_state.last_chunk_map: Dict[str, str] = {}

    # これまでのメッセージを表示
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 入力欄
    user_input = st.chat_input("メッセージを入力してください")

    if user_input:
        # 画面に自分の発話を出す
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 直前までの履歴を渡して Agent を呼ぶ
        history = st.session_state.messages[:-1]  # 今回の user 以外
        with st.chat_message("assistant"):
            with st.spinner("エージェントに問い合わせ中..."):
                try:
                    assistant_text, chunk_map = call_foundry_agent(
                        user_message=user_input,
                        history=history,
                    )
                except Exception as e:
                    assistant_text = f"エラーが発生しました: {e}"
                    chunk_map = {}

            st.markdown(assistant_text)

            if chunk_map:
                st.markdown("---")
                with st.expander("参照されたドキュメント"):
                    for key, info in chunk_map.items():
                        title = info.get("title", "(no title)")
                        chunk = info.get("chunk", "")

                        st.markdown(f"**タイトル:** {title}")

                        st.text_area(
                            label=f"chunk ({key})",
                            value=chunk,
                            height=150,
                            key=f"chunk_{key}",
                        )
                        st.markdown("---")

        # 履歴に assistant の発話を追加
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_text}
        )
        st.session_state.last_chunk_map = chunk_map


if __name__ == "__main__":
    main()
