from datetime import date, datetime
from supabase import create_client, Client
from .config import settings

def get_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)

# ── 认证 ──────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    """注册新用户"""
    client = get_client()
    res = client.auth.sign_up({"email": email, "password": password})
    return res

def sign_in(email: str, password: str) -> dict:
    """登录，返回 session"""
    client = get_client()
    res = client.auth.sign_in_with_password({"email": email, "password": password})
    return res

def sign_out(access_token: str) -> None:
    """登出"""
    client = get_client()
    client.auth.sign_out()

# ── 内部工具 ──────────────────────────────────────────

def _authed_client(access_token: str) -> Client:
    """返回携带用户 JWT 的 client，RLS 才能生效"""
    client = get_client()
    client.postgrest.auth(access_token)
    return client

# ── 库存 CRUD ─────────────────────────────────────────

def add_item(access_token: str, user_id: str,
             name: str, quantity: float, unit: str,
             expiry_date: str = None) -> None:
    """添加或更新食材（同名则覆盖）"""
    client = _authed_client(access_token)
    name = name.strip()
    data = {
        "user_id": user_id,
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "expiry": expiry_date or "未知",
        "updated_at": datetime.utcnow().isoformat(),
    }
    # upsert：同一用户同名食材直接更新
    client.table("inventory").upsert(
        data, on_conflict="user_id,name"
    ).execute()
    print(f"✅ 已添加：{name} {quantity}{unit}")

def remove_item(access_token: str, item_id: str) -> None:
    """删除食材（按 id）"""
    client = _authed_client(access_token)
    client.table("inventory").delete().eq("id", item_id).execute()

def update_item(access_token: str, item_id: str,
                name: str, quantity: float, unit: str,
                expiry_date: str = None) -> None:
    """更新食材信息"""
    client = _authed_client(access_token)
    client.table("inventory").update({
        "name": name.strip(),
        "quantity": quantity,
        "unit": unit,
        "expiry": expiry_date or "未知",
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", item_id).execute()

def use_item(access_token: str, item_id: str,
             quantity: float, current_quantity: float, unit: str) -> None:
    """使用食材，扣减库存；用完自动删除"""
    client = _authed_client(access_token)
    remaining = current_quantity - quantity
    if remaining <= 0:
        client.table("inventory").delete().eq("id", item_id).execute()
        print(f"✅ 已用完，从库存移除")
    else:
        client.table("inventory").update({
            "quantity": remaining,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", item_id).execute()
        print(f"✅ 已使用 {quantity}{unit}，剩余 {remaining}{unit}")

def load_inventory(access_token: str) -> list[dict]:
    """读取当前用户的全部库存，返回列表"""
    client = _authed_client(access_token)
    res = client.table("inventory").select("*").order("name").execute()
    return res.data or []

def get_expiring_soon(access_token: str, days: int = 3) -> list[dict]:
    """返回即将过期（days 天内）的食材列表"""
    inventory = load_inventory(access_token)
    today = date.today()
    result = []
    for item in inventory:
        if item["expiry"] == "未知":
            continue
        try:
            expiry = datetime.strptime(item["expiry"], "%Y-%m-%d").date()
            days_left = (expiry - today).days
            if days_left <= days:
                item["days_left"] = days_left
                result.append(item)
        except ValueError:
            continue
    return result

def show_inventory(access_token: str) -> None:
    """CLI 用：打印库存"""
    inventory = load_inventory(access_token)
    if not inventory:
        print("冰箱是空的！")
        return
    expiring_ids = {i["id"] for i in get_expiring_soon(access_token)}
    print("\n📦 当前库存：")
    print("─" * 40)
    for item in inventory:
        warning = " ⚠️ 快过期！" if item["id"] in expiring_ids else ""
        print(f"  {item['name']}: {item['quantity']}{item['unit']} （过期：{item['expiry']}）{warning}")
    print("─" * 40)
