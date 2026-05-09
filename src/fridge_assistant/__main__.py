from .app import (
    suggest_recipes, analyze_nutrition,
    generate_shopping_list, scan_receipt
)
from .inventory import (
    add_item, remove_item, use_item, show_inventory, get_expiring_soon
)

def show_menu():
    print("\n🥦 冰箱助手")
    print("─" * 30)
    print("1. 查看库存")
    print("2. 添加食材")
    print("3. 使用食材")
    print("4. 删除食材")
    print("5. 推荐菜谱")
    print("6. 营养分析")
    print("7. 生成购物清单")
    print("8. 扫描小票入库")
    print("0. 退出")
    print("─" * 30)

def main():
    print("🌟 欢迎使用冰箱助手！")
    expiring = get_expiring_soon()
    if expiring:
        print("\n⚠️  以下食材即将过期：")
        for name, info, days_left in expiring:
            print(f"   {name}：还有 {days_left} 天过期！")
    while True:
        show_menu()
        choice = input("请选择：").strip()
        if choice == "1":
            show_inventory()
        elif choice == "2":
            name = input("食材名称：").strip()
            quantity = float(input("数量：").strip())
            unit = input("单位（个/克/毫升等）：").strip()
            expiry = input("过期日期（2026-05-15，不知道直接回车）：").strip()
            add_item(name, quantity, unit, expiry or None)
        elif choice == "3":
            name = input("使用哪个食材：").strip()
            quantity = float(input("使用多少：").strip())
            use_item(name, quantity)
        elif choice == "4":
            name = input("删除哪个食材：").strip()
            remove_item(name)
        elif choice == "5":
            print("\n🍳 正在推荐菜谱...")
            print(suggest_recipes())
        elif choice == "6":
            print("\n💪 正在分析营养...")
            print(analyze_nutrition())
        elif choice == "7":
            print("\n🛒 正在生成购物清单...")
            print(generate_shopping_list())
        elif choice == "8":
            path = input("请输入小票图片路径：").strip()
            scan_receipt(path)
        elif choice == "0":
            print("再见！👋")
            break
        else:
            print("❌ 无效选项，请重新输入")

if __name__ == "__main__":
    main()
