import streamlit as st
import tempfile
import os
from fridge_assistant.inventory import (
    sign_up, sign_in, sign_out,
    load_inventory, add_item, remove_item,
    use_item, get_expiring_soon,
)
from fridge_assistant.app import suggest_recipes, analyze_nutrition, generate_shopping_list, parse_voice_text
from fridge_assistant.vision import analyze_image, parse_items

st.set_page_config(page_title="冰箱助手", layout="wide")

# ── 工具函数 ──────────────────────────────────────────

def get_session():
    return st.session_state.get("session")

def get_token():
    s = get_session()
    return s.session.access_token if s else None

def get_user_id():
    s = get_session()
    return s.user.id if s else None

# ── 登录 / 注册页 ─────────────────────────────────────

def show_auth_page():
    st.title("🥦 冰箱助手")
    tab_login, tab_signup = st.tabs(["登录", "注册"])

    with tab_login:
        email = st.text_input("邮箱", key="login_email")
        password = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录", use_container_width=True):
            try:
                res = sign_in(email, password)
                st.session_state["session"] = res
                st.success("登录成功！")
                st.rerun()
            except Exception as e:
                st.error(f"登录失败：{e}")

    with tab_signup:
        email = st.text_input("邮箱", key="signup_email")
        password = st.text_input("密码（至少6位）", type="password", key="signup_pwd")
        if st.button("注册", use_container_width=True):
            try:
                sign_up(email, password)
                st.success("注册成功！请检查邮箱确认后再登录。")
            except Exception as e:
                st.error(f"注册失败：{e}")

# ── 主应用 ────────────────────────────────────────────

def show_main_app():
    token = get_token()
    user_id = get_user_id()

    # 侧边栏
    with st.sidebar:
        st.markdown(f"👤 **{get_session().user.email}**")
        if st.button("退出登录"):
            sign_out(token)
            del st.session_state["session"]
            st.rerun()
        st.divider()
        st.header("过期提醒")
        expiring = get_expiring_soon(token)
        if expiring:
            for item in expiring:
                st.warning(f"{item['name']} 还有 {item['days_left']} 天过期！")
        else:
            st.success("没有即将过期的食材 ✅")

    st.title("🥦 冰箱助手")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 库存", "📸 图片入库", "🎤 语音入库", "🍳 菜谱推荐", "🛒 购物清单"])

    # ── Tab1：库存 ──
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("当前库存")
            inventory = load_inventory(token)
            expiring_ids = {i["id"] for i in get_expiring_soon(token)}
            if inventory:
                for item in inventory:
                    c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                    warning = "⚠️" if item["id"] in expiring_ids else ""
                    c1.write(f"**{item['name']}** {warning}")
                    c2.write(f"{item['quantity']}{item['unit']} （{item['expiry']}）")
                    # 使用
                    use_qty = c3.number_input("用", min_value=0.1,
                                              value=1.0, step=0.1,
                                              key=f"use_{item['id']}")
                    if c3.button("✓", key=f"usebtn_{item['id']}"):
                        use_item(token, item["id"], use_qty, item["quantity"], item["unit"])
                        st.rerun()
                    if c4.button("删除", key=f"del_{item['id']}"):
                        remove_item(token, item["id"])
                        st.rerun()
            else:
                st.info("冰箱是空的！")

        with col2:
            st.subheader("添加食材")
            name = st.text_input("食材名称")
            quantity = st.number_input("数量", min_value=0.1, value=1.0, step=0.1)
            unit = st.selectbox("单位", ["个", "克", "毫升", "盒", "斤", "袋", "根", "片"])
            expiry = st.date_input("过期日期")
            if st.button("添加", use_container_width=True):
                if name:
                    add_item(token, user_id, name, quantity, unit, str(expiry))
                    st.success(f"已添加 {name}！")
                    st.rerun()
                else:
                    st.error("请输入食材名称")

    # ── Tab2：图片入库 ──
    with tab2:
        st.subheader("图片识别入库")
        mode = st.radio("识别模式", ["小票", "冰箱实物"], horizontal=True)
        mode_key = "receipt" if mode == "小票" else "fridge"
        uploaded = st.file_uploader("上传图片", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.image(uploaded, use_container_width=True)
            if st.button("开始识别", use_container_width=True):
                with st.spinner("正在识别..."):
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                        f.write(uploaded.getvalue())
                        tmp_path = f.name
                    result = analyze_image(tmp_path, mode=mode_key)
                    os.unlink(tmp_path)
                    items = parse_items(result)
                    st.session_state["recognized_items"] = items
                    st.success(f"识别到 {len(items)} 个食材！")
        if "recognized_items" in st.session_state:
            st.subheader("识别结果（可修改）")
            items = st.session_state["recognized_items"]
            for i, item in enumerate(items):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                items[i]["name"] = c1.text_input("名称", item["name"], key=f"name_{i}")
                items[i]["quantity"] = c2.number_input("数量", value=item["quantity"], key=f"qty_{i}")
                items[i]["unit"] = c3.selectbox("单位", ["个", "克", "毫升", "盒", "斤"], key=f"unit_{i}")
                expiry = c4.date_input("过期日期", key=f"exp_{i}")
                items[i]["expiry"] = str(expiry)
            if st.button("全部加入库存", use_container_width=True):
                for item in items:
                    add_item(token, user_id, item["name"], item["quantity"],
                             item["unit"], item.get("expiry"))
                st.success("已全部加入库存！")
                del st.session_state["recognized_items"]
                st.rerun()

    # ── Tab3：语音入库 ──
    with tab3:
        st.subheader("🎤 语音录入食材")
        st.write("说一段话描述你买了什么，AI 自动解析成食材列表")
        audio = st.audio_input("点击录音")
        if audio:
            with st.spinner("正在识别语音..."):
                from fridge_assistant.voice import transcribe_audio
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio.getvalue())
                    tmp_path = f.name
                text = transcribe_audio(tmp_path)
                os.unlink(tmp_path)
            st.success("识别完成！")
            st.write(f"**识别内容：** {text}")
            with st.spinner("正在解析食材..."):
                items = parse_voice_text(text)
            if items:
                st.session_state["voice_items"] = items
                st.success(f"解析到 {len(items)} 个食材！")
            else:
                st.error("没有解析到食材，请重试")
        if "voice_items" in st.session_state:
            st.subheader("解析结果")
            items = st.session_state["voice_items"]
            for i, item in enumerate(items):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                items[i]["name"] = c1.text_input("名称", item["name"], key=f"vname_{i}")
                items[i]["quantity"] = c2.number_input("数量", value=float(item["quantity"]), key=f"vqty_{i}")
                items[i]["unit"] = c3.selectbox("单位", ["个", "克", "毫升", "盒", "斤", "袋"], key=f"vunit_{i}")
                items[i]["expiry"] = c4.text_input("过期日期", item.get("expiry") or "", key=f"vexp_{i}")
            if st.button("全部加入库存 ✅", use_container_width=True, key="voice_add"):
                for item in items:
                    add_item(token, user_id, item["name"], item["quantity"],
                             item["unit"], item["expiry"] or None)
                st.success("已全部加入库存！")
                del st.session_state["voice_items"]
                st.rerun()

    # ── Tab4：菜谱推荐 ──
    with tab4:
        st.subheader("今天吃什么？")
        if st.button("推荐菜谱", use_container_width=True):
            with st.spinner("正在思考..."):
                result = suggest_recipes(token)
            st.markdown(result)
        st.divider()
        st.subheader("营养分析")
        if st.button("分析营养", use_container_width=True):
            with st.spinner("正在分析..."):
                result = analyze_nutrition(token)
            st.markdown(result)

    # ── Tab5：购物清单 ──
    with tab5:
        st.subheader("购物清单")
        if st.button("生成购物清单", use_container_width=True):
            with st.spinner("正在生成..."):
                result = generate_shopping_list(token)
            st.markdown(result)


# ── 入口 ──────────────────────────────────────────────

if get_session():
    show_main_app()
else:
    show_auth_page()
