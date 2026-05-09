import streamlit as st
import tempfile
import os
from fridge_assistant.inventory import (
    load_inventory, add_item, remove_item,
    use_item, get_expiring_soon
)
from fridge_assistant.app import suggest_recipes, analyze_nutrition, generate_shopping_list
from fridge_assistant.vision import analyze_image, parse_items

st.set_page_config(page_title="冰箱助手", layout="wide")
st.title("🥦 冰箱助手")

with st.sidebar:
    st.header("过期提醒")
    expiring = get_expiring_soon()
    if expiring:
        for name, info, days_left in expiring:
            st.warning(f"{name} 还有 {days_left} 天过期！")
    else:
        st.success("没有即将过期的食材 ✅")

tab1, tab2, tab3, tab4 = st.tabs(["📦 库存", "📸 图片入库", "🍳 菜谱推荐", "🛒 购物清单"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("当前库存")
        inventory = load_inventory()
        if inventory:
            for name, info in inventory.items():
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{name}**")
                c2.write(f"{info['数量']}{info['单位']} （{info['过期日期']}）")
                if c3.button("删除", key=f"del_{name}"):
                    remove_item(name)
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
                add_item(name, quantity, unit, str(expiry))
                st.success(f"已添加 {name}！")
                st.rerun()
            else:
                st.error("请输入食材名称")
        st.subheader("使用食材")
        inventory = load_inventory()
        if inventory:
            use_name = st.selectbox("选择食材", list(inventory.keys()))
            use_qty = st.number_input("使用数量", min_value=0.1, value=1.0, step=0.1)
            if st.button("使用", use_container_width=True):
                use_item(use_name, use_qty)
                st.success(f"已使用 {use_name}")
                st.rerun()

with tab2:
    st.subheader("图片识别入库")
    mode = st.radio("识别模式", ["小票", "冰箱实物"], horizontal=True)
    mode_key = "receipt" if mode == "小票" else "fridge"
    uploaded = st.file_uploader("上传图片", type=["jpg", "jpeg", "png"])
    if uploaded:
        st.image(uploaded, caption="上传的图片", use_container_width=True)
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
        st.subheader("识别结果")
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
                add_item(item["name"], item["quantity"], item["unit"], item.get("expiry"))
            st.success("已全部加入库存！")
            del st.session_state["recognized_items"]
            st.rerun()

with tab3:
    st.subheader("今天吃什么？")
    if st.button("推荐菜谱", use_container_width=True):
        with st.spinner("正在思考..."):
            result = suggest_recipes()
        st.markdown(result)
    st.divider()
    st.subheader("营养分析")
    if st.button("分析营养", use_container_width=True):
        with st.spinner("正在分析..."):
            result = analyze_nutrition()
        st.markdown(result)

with tab4:
    st.subheader("购物清单")
    if st.button("生成购物清单", use_container_width=True):
        with st.spinner("正在生成..."):
            result = generate_shopping_list()
        st.markdown(result)
