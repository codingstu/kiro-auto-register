#!/usr/bin/env python3
"""
📧 邮箱管理工具 - 交互式命令行工具
用于配置和管理用于注册的邮箱池
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.email_manager import email_manager
from colorama import Fore, Back, Style, init

# 初始化 colorama
init(autoreset=True)


def print_header():
    """打印标题"""
    print(f"\n{Back.CYAN}{Fore.WHITE} 📧 邮箱池管理工具 {Style.RESET_ALL}\n")


def print_menu():
    """打印菜单"""
    print("=" * 50)
    print("请选择操作:")
    print("  1️⃣  - 添加 Gmail 邮箱")
    print("  2️⃣  - 添加 Outlook 邮箱")
    print("  3️⃣  - 添加自定义邮箱")
    print("  4️⃣  - 列出所有邮箱")
    print("  5️⃣  - 禁用邮箱")
    print("  6️⃣  - 启用邮箱")
    print("  7️⃣  - 移除邮箱")
    print("  0️⃣  - 退出")
    print("=" * 50)


def add_gmail():
    """添加 Gmail 邮箱"""
    print(f"\n{Fore.CYAN}📧 添加 Gmail 邮箱{Style.RESET_ALL}")
    print("=" * 50)
    
    print(f"{Fore.YELLOW}如何获取 Gmail App Password:{Style.RESET_ALL}")
    print("  1. 启用两步验证: https://myaccount.google.com/security")
    print("  2. 进入应用密码: https://myaccount.google.com/apppasswords")
    print("  3. 选择'邮件'和'Windows 电脑'")
    print("  4. Google 生成 16 位密码，复制粘贴到下面")
    print()
    
    email = input(f"{Fore.GREEN}📧 Gmail 邮箱地址：{Style.RESET_ALL} ").strip()
    if not email:
        print(f"{Fore.RED}❌ 邮箱不能为空{Style.RESET_ALL}")
        return
    
    app_password = input(f"{Fore.GREEN}🔑 App Password (16位，不含空格)：{Style.RESET_ALL} ").strip()
    if not app_password or len(app_password) < 10:
        print(f"{Fore.RED}❌ App Password 无效{Style.RESET_ALL}")
        return
    
    description = input(f"{Fore.GREEN}📝 描述 (可选)：{Style.RESET_ALL} ").strip() or "Gmail 邮箱"
    
    if email_manager.add_real_email(email, app_password, description):
        print(f"\n{Fore.GREEN}✅ Gmail 邮箱已添加{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ 邮箱添加失败{Style.RESET_ALL}")


def add_outlook():
    """添加 Outlook 邮箱"""
    print(f"\n{Fore.CYAN}📧 添加 Outlook 邮箱{Style.RESET_ALL}")
    print("=" * 50)
    
    print(f"{Fore.YELLOW}如何获取 Outlook App Password:{Style.RESET_ALL}")
    print("  1. 进入账户安全: https://account.microsoft.com/account/security")
    print("  2. 应用和设备 → 应用密码")
    print("  3. 选择'邮件'和'Windows 电脑'")
    print("  4. 复制生成的密码粘贴到下面")
    print()
    
    email = input(f"{Fore.GREEN}📧 Outlook 邮箱地址：{Style.RESET_ALL} ").strip()
    if not email:
        print(f"{Fore.RED}❌ 邮箱不能为空{Style.RESET_ALL}")
        return
    
    app_password = input(f"{Fore.GREEN}🔑 App Password：{Style.RESET_ALL} ").strip()
    if not app_password:
        print(f"{Fore.RED}❌ App Password 不能为空{Style.RESET_ALL}")
        return
    
    description = input(f"{Fore.GREEN}📝 描述 (可选)：{Style.RESET_ALL} ").strip() or "Outlook 邮箱"
    
    if email_manager.add_real_email(email, app_password, description):
        print(f"\n{Fore.GREEN}✅ Outlook 邮箱已添加{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ 邮箱添加失败{Style.RESET_ALL}")


def add_custom():
    """添加自定义邮箱"""
    print(f"\n{Fore.CYAN}📧 添加自定义邮箱{Style.RESET_ALL}")
    print("=" * 50)
    
    email = input(f"{Fore.GREEN}📧 邮箱地址：{Style.RESET_ALL} ").strip()
    if not email:
        print(f"{Fore.RED}❌ 邮箱不能为空{Style.RESET_ALL}")
        return
    
    app_password = input(f"{Fore.GREEN}🔑 邮箱密码/App Password：{Style.RESET_ALL} ").strip()
    if not app_password:
        print(f"{Fore.RED}❌ 密码不能为空{Style.RESET_ALL}")
        return
    
    description = input(f"{Fore.GREEN}📝 描述 (可选)：{Style.RESET_ALL} ").strip() or "自定义邮箱"
    
    if email_manager.add_real_email(email, app_password, description):
        print(f"\n{Fore.GREEN}✅ 邮箱已添加{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ 邮箱添加失败{Style.RESET_ALL}")


def list_emails():
    """列出所有邮箱"""
    print(f"\n{Fore.CYAN}📧 邮箱池{Style.RESET_ALL}")
    print("=" * 50)
    
    emails = email_manager.config.get('email_pool', [])
    
    if not emails:
        print(f"{Fore.YELLOW}(空 - 将使用临时邮箱){Style.RESET_ALL}")
        return
    
    for i, email in enumerate(emails, 1):
        status_icon = "✅" if email['enabled'] else "❌"
        email_type = f"[{email['type'].upper()}]"
        usage_info = f"已用{email['usage_count']}次"
        
        print(f"  {i}. {status_icon} {email['email']} {email_type}")
        print(f"      └─ {email['description']} ({usage_info})")
        
        if email['last_used']:
            print(f"      └─ 最后使用: {email['last_used']}")


def disable_email():
    """禁用邮箱"""
    print(f"\n{Fore.CYAN}❌ 禁用邮箱{Style.RESET_ALL}")
    print("=" * 50)
    
    email_manager.list_emails()
    
    email = input(f"{Fore.GREEN}📧 输入要禁用的邮箱地址：{Style.RESET_ALL} ").strip()
    if not email:
        print(f"{Fore.RED}❌ 邮箱不能为空{Style.RESET_ALL}")
        return
    
    if email_manager.disable_email(email):
        print(f"{Fore.GREEN}✅ 邮箱已禁用{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ 邮箱未找到{Style.RESET_ALL}")


def enable_email():
    """启用邮箱"""
    print(f"\n{Fore.CYAN}✅ 启用邮箱{Style.RESET_ALL}")
    print("=" * 50)
    
    email_manager.list_emails()
    
    email = input(f"{Fore.GREEN}📧 输入要启用的邮箱地址：{Style.RESET_ALL} ").strip()
    if not email:
        print(f"{Fore.RED}❌ 邮箱不能为空{Style.RESET_ALL}")
        return
    
    if email_manager.enable_email(email):
        print(f"{Fore.GREEN}✅ 邮箱已启用{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ 邮箱未找到{Style.RESET_ALL}")


def remove_email():
    """移除邮箱"""
    print(f"\n{Fore.RED}🗑️  移除邮箱{Style.RESET_ALL}")
    print("=" * 50)
    
    email_manager.list_emails()
    
    email = input(f"{Fore.GREEN}📧 输入要移除的邮箱地址：{Style.RESET_ALL} ").strip()
    if not email:
        print(f"{Fore.RED}❌ 邮箱不能为空{Style.RESET_ALL}")
        return
    
    confirm = input(f"{Fore.YELLOW}⚠️  确定删除 {email}？(y/n)：{Style.RESET_ALL} ").strip().lower()
    if confirm != 'y':
        print(f"{Fore.YELLOW}❌ 已取消{Style.RESET_ALL}")
        return
    
    if email_manager.remove_email(email):
        print(f"{Fore.GREEN}✅ 邮箱已移除{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ 邮箱未找到{Style.RESET_ALL}")


def main():
    """主函数"""
    print_header()
    
    while True:
        print_menu()
        choice = input(f"{Fore.CYAN}请选择 (0-7)：{Style.RESET_ALL} ").strip()
        
        if choice == '1':
            add_gmail()
        elif choice == '2':
            add_outlook()
        elif choice == '3':
            add_custom()
        elif choice == '4':
            list_emails()
        elif choice == '5':
            disable_email()
        elif choice == '6':
            enable_email()
        elif choice == '7':
            remove_email()
        elif choice == '0':
            print(f"\n{Fore.YELLOW}👋 再见！{Style.RESET_ALL}\n")
            break
        else:
            print(f"{Fore.RED}❌ 无效选择{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}按 Enter 继续...{Style.RESET_ALL}")
        print("\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}👋 已退出{Style.RESET_ALL}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ 错误: {e}{Style.RESET_ALL}\n")
        sys.exit(1)
