from flask import Flask, request, jsonify, redirect
import secrets
import os
from supabase import create_client
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

SUPABASE_URL = "https://uwmtavdejwfroevvadnp.supabase.co"
SUPABASE_KEY = "你的key"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

AUTH_CODES = {}
TOKENS = {}

@app.route("/.well-known/oauth-authorization-server")
def oauth_metadata():
    base = request.host_url.rstrip("/")
    return jsonify({
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"]
    })

@app.route("/oauth/register", methods=["POST"])
def register():
    return jsonify({
        "client_id": "claude-client",
        "client_secret": "not-needed",
        "redirect_uris": request.json.get("redirect_uris", []),
        "grant_types": ["authorization_code"],
        "response_types": ["code"]
    })

@app.route("/oauth/authorize")
def authorize():
    code = secrets.token_urlsafe(16)
    redirect_uri = request.args.get("redirect_uri")
    state = request.args.get("state", "")
    AUTH_CODES[code] = {"redirect_uri": redirect_uri}
    return redirect(f"{redirect_uri}?code={code}&state={state}")

@app.route("/oauth/token", methods=["POST"])
def token():
    new_token = secrets.token_urlsafe(32)
    TOKENS[new_token] = True
    return jsonify({
        "access_token": new_token,
        "token_type": "bearer"
    })

@app.route("/mcp", methods=["POST"])
def mcp():
    body = request.json
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    if method == "initialize":
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "记忆助手", "version": "1.0"}
        }})

    if method == "tools/list":
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
            {"name": "add_memory", "description": "添加一条记忆",
             "inputSchema": {"type": "object", "properties": {
                 "content": {"type": "string"},
                 "category": {"type": "string", "default": "general"}
             }, "required": ["content"]}},
            {"name": "get_memories", "description": "读取所有记忆",
             "inputSchema": {"type": "object", "properties": {
                 "category": {"type": "string", "default": ""}
             }}}
        ]}})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "add_memory":
            db.table("memories").insert({
                "content": args["content"],
                "category": args.get("category", "general")
            }).execute()
            return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"已记住：{args['content']}"}]
            }})

        if name == "get_memories":
            q = db.table("memories").select("*")
            if args.get("category"):
                q = q.eq("category", args["category"])
            data = q.order("created_at", desc=True).execute()
            if not data.data:
                text = "暂无记忆"
            else:
                text = "\n".join([f"[{r['category']}] {r['content']}" for r in data.data])
            return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": text}]
            }})

    return jsonify({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
