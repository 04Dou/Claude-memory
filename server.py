from flask import Flask, request, jsonify, redirect, Response, stream_with_context
import json
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

from flask import Flask, request, jsonify, redirect, Response, stream_with_context
import json
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
