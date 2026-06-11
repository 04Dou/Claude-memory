from mcp.server.fastmcp import FastMCP
from supabase import create_client
import os

SUPABASE_URL = "https://uwmtavdejwfroevvadnp.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "你的key")

db = create_client(SUPABASE_URL, SUPABASE_KEY)

mcp = FastMCP("记忆助手")

@mcp.tool()
def add_memory(content: str, category: str = "general") -> str:
    """添加一条记忆"""
    db.table("memories").insert({
        "content": content,
        "category": category
    }).execute()
    return f"已记住：{content}"

@mcp.tool()
def get_memories(category: str = "") -> str:
    """读取所有记忆"""
    q = db.table("memories").select("*")
    if category:
        q = q.eq("category", category)
    data = q.order("created_at", desc=True).execute()
    if not data.data:
        return "暂无记忆"
    return "\n".join([f"[{r['category']}] {r['content']}" for r in data.data])

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
