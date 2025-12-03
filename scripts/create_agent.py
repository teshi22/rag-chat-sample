import os
import uuid

import requests
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()

# エージェント構成に必要な設定値を取得
credential = DefaultAzureCredential()
mcp_endpoint = os.getenv("MCP_ENDPOINT")
project_endpoint = os.getenv("PROJECT_ENDPOINT")
project_resource_id = os.getenv("PROJECT_RESOURCE_ID")
project_connection_name = (
    os.getenv("PROJECT_CONNECTION_NAME") or "knowledgebase-" + uuid.uuid4().hex[:8]
)
agent_name = os.getenv("AGENT_NAME")
agent_model = os.getenv("AGENT_MODEL", "gpt-4.1")  # 省略時は標準モデルを利用

missing_env = [
    name
    for name, value in {
        "MCP_ENDPOINT": mcp_endpoint,
        "PROJECT_ENDPOINT": project_endpoint,
        "PROJECT_RESOURCE_ID": project_resource_id,
        "AGENT_NAME": agent_name,
    }.items()
    if not value
]
if missing_env:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_env)}"
    )

# エージェント作成前に Azure ML プロジェクト接続を作成／更新
bearer_token_provider = get_bearer_token_provider(
    credential, "https://management.azure.com/.default"
)
headers = {"Authorization": f"Bearer {bearer_token_provider()}"}
connection_url = (
    f"https://management.azure.com{project_resource_id}/connections/"
    f"{project_connection_name}?api-version=2025-10-01-preview"
)
connection_payload = {
    "name": project_connection_name,
    "type": "Microsoft.MachineLearningServices/workspaces/connections",
    "properties": {
        "authType": "ProjectManagedIdentity",
        "category": "RemoteTool",
        "target": mcp_endpoint,
        "isSharedToAll": True,
        "audience": "https://search.azure.com/",
        "metadata": {"ApiType": "Azure"},
    },
}
response = requests.put(connection_url, headers=headers, json=connection_payload)
response.raise_for_status()
print(f"Connection '{project_connection_name}' created or updated successfully.")

# プロジェクトクライアントを初期化
project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)

# エージェントへの指示文を定義
instructions = """
You are a helpful assistant that must use the knowledge base to answer all the questions from user. You must never answer from your own knowledge under any circumstances.
Every answer must always provide annotations for using the MCP knowledge base tool and render them as: `【message_idx:search_idx†source_name】`
If you cannot find the answer in the provided knowledge base you must respond with "I don't know".
"""

# MCP ツールを知識ベース接続付きで生成
mcp_kb_tool = MCPTool(
    server_label="knowledge-base",
    server_url=mcp_endpoint,
    require_approval="never",
    allowed_tools=["knowledge_base_retrieve"],
    project_connection_id=project_connection_name,
)

# MCP ツールを利用してエージェントを作成
agent = project_client.agents.create_version(
    agent_name=agent_name,
    definition=PromptAgentDefinition(
        model=agent_model, instructions=instructions, tools=[mcp_kb_tool]
    ),
)

print(f"Agent '{agent_name}' created or updated successfully.")
