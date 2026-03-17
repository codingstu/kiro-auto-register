"""
用户邮箱管理模块 - 支持真实邮箱和一次性邮箱
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime


class UserEmailManager:
    """
    用户邮箱管理 - 支持真实 Outlook/Gmail 和一次性邮箱
    """
    
    def __init__(self):
        self.emails_dir = Path("key/emails")
        self.emails_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.emails_dir / "email_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载邮箱配置"""
        if self.config_file.exists():
            return json.loads(self.config_file.read_text(encoding='utf-8'))
        return {
            'email_pool': [],
            'used_emails': [],
            'email_mode': 'mixed',  # mixed, real, temp
        }
    
    def _save_config(self):
        """保存邮箱配置"""
        self.config_file.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def add_real_email(self, email: str, app_password: str, description: str = "") -> bool:
        """
        添加真实邮箱 (Outlook/Gmail with App Password)
        
        Args:
            email: 邮箱地址
            app_password: 应用密码（不是账户密码）
            description: 描述
        
        Returns:
            是否添加成功
        """
        email_entry = {
            'email': email,
            'password': app_password,
            'type': 'real',
            'description': description,
            'added_at': datetime.now().isoformat(),
            'usage_count': 0,
            'last_used': None,
            'enabled': True
        }
        
        # 检查是否已存在
        for existing in self.config['email_pool']:
            if existing['email'] == email:
                print(f"⚠️  邮箱 {email} 已存在")
                return False
        
        self.config['email_pool'].append(email_entry)
        self._save_config()
        print(f"✅ 已添加真实邮箱: {email}")
        return True
    
    def get_email_for_registration(self) -> Optional[Tuple[str, str, str]]:
        """
        获取用于注册的邮箱
        优先级: 已启用的真实邮箱 > 生成临时邮箱
        
        Returns:
            (邮箱, 密码/token, 类型)
        """
        # 先尝试轮换真实邮箱
        enabled_real_emails = [
            e for e in self.config['email_pool']
            if e['type'] == 'real' and e['enabled']
        ]
        
        if enabled_real_emails:
            # 选择使用次数最少的邮箱
            selected = min(enabled_real_emails, key=lambda x: x['usage_count'])
            selected['usage_count'] += 1
            selected['last_used'] = datetime.now().isoformat()
            self._save_config()
            
            print(f"📧 使用真实邮箱: {selected['email']} (使用{selected['usage_count']}次)")
            return (selected['email'], selected['password'], 'real')
        
        # 回退到临时邮箱
        print("📧 使用一次性临时邮箱")
        return ("temp", "temp_token", "temp")
    
    def list_emails(self):
        """列出所有配置的邮箱"""
        print("\n📧 邮箱池:")
        if not self.config['email_pool']:
            print("  (空)")
            return
        
        for i, email in enumerate(self.config['email_pool'], 1):
            status = "✅" if email['enabled'] else "❌"
            print(f"  {i}. {status} {email['email']} ({email['type']}) - 使用{email['usage_count']}次")
    
    def remove_email(self, email: str) -> bool:
        """移除邮箱"""
        original_len = len(self.config['email_pool'])
        self.config['email_pool'] = [
            e for e in self.config['email_pool'] if e['email'] != email
        ]
        
        if len(self.config['email_pool']) < original_len:
            self._save_config()
            print(f"✅ 已移除邮箱: {email}")
            return True
        
        print(f"⚠️  邮箱未找到: {email}")
        return False
    
    def disable_email(self, email: str) -> bool:
        """禁用邮箱"""
        for e in self.config['email_pool']:
            if e['email'] == email:
                e['enabled'] = False
                self._save_config()
                print(f"✅ 已禁用邮箱: {email}")
                return True
        
        print(f"⚠️  邮箱未找到: {email}")
        return False
    
    def enable_email(self, email: str) -> bool:
        """启用邮箱"""
        for e in self.config['email_pool']:
            if e['email'] == email:
                e['enabled'] = True
                self._save_config()
                print(f"✅ 已启用邮箱: {email}")
                return True
        
        print(f"⚠️  邮箱未找到: {email}")
        return False


# 全局邮箱管理器
email_manager = UserEmailManager()
