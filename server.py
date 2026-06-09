from mcp.server.fastmcp import FastMCP
from supabase import create_client
from datetime import datetime

SUPABASE_URL = "https://uwmtavdejwfroevvadnp.supabase.co"
SUPABASE_KEY = "sb_publishable_LQ8-fakghOGuDprdtoEhDQ_LnNfxPjV"

mcp = FastMCP("记忆助手")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

@mcp.tool()
def add_memory(content: str, category: str = "general") -> str:
    """添加一条记忆"""
    db.table("memories").insert({"content": content, "category": category}).execute()
    return f"✅ 已记住：{content}"

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

@mcp.tool()
def add_reminder(content: str, remind_at: str) -> str:
    """添加提醒"""
    db.table("reminders").insert({"content": content, "remind_at": remind_at}).execute()
    return f"✅ 提醒已设置：{content}（{remind_at}）"

@mcp.tool()
def check_reminders() -> str:
    """检查未完成的提醒"""
    now = datetime.now().isoformat()
    data = db.table("reminders").select("*").lte("remind_at", now).eq("done", False).execute()
    if not data.data:
        return "✅ 没有待处理的提醒"
    result = "⏰ 以下提醒需要处理：\n"
    for r in data.data:
        result += f"- [#{r['id']}] {r['content']}（{r['remind_at']}）\n"
    return result

@mcp.tool()
def complete_reminder(reminder_id: int) -> str:
    """标记提醒为已完成"""
    db.table("reminders").update({"done": True}).eq("id", reminder_id).execute()
    return f"✅ 提醒 #{reminder_id} 已完成"

if __name__ == "__main__":
    mcp.run(transport="sse")
