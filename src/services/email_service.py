"""
邮箱服务模块
支持多种临时邮箱服务：
1. mail.chatgpt.org.uk (默认，无需部署)
2. cloudflare_temp_email (需要自己部署)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import json
import random
import string
import time
import email
from email import policy

from config import (
    EMAIL_WORKER_URL,
    EMAIL_DOMAIN,
    EMAIL_PREFIX_LENGTH,
    EMAIL_WAIT_TIMEOUT,
    EMAIL_POLL_INTERVAL,
    HTTP_TIMEOUT
)
from helpers.utils import http_session, get_user_agent


# ========================================================
# 新的临时邮箱服务: mail.chatgpt.org.uk
# ========================================================

class ChatGPTMailClient:
    """
    基于 mail.chatgpt.org.uk 的临时邮箱客户端
    无需自己部署，直接使用公共服务
    """
    
    def __init__(self):
        self.site_url = "https://mail.chatgpt.org.uk"
        self.base_url = f"{self.site_url}/api"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": self.site_url,
            "Referer": f"{self.site_url}/"
        }
        self.inbox_token = ""
        self.auth_email = ""
        self.auth_expires_at = 0
        self.current_email = None
        self.email_created_at = None  # 邮箱创建时间戳
        self.processed_mail_ids = set()  # 已处理的邮件ID
        self.debug = True  # 调试模式

    def _apply_auth(self, auth: dict):
        if not auth:
            return
        self.inbox_token = auth.get("token", "") or self.inbox_token
        self.auth_email = (auth.get("email", "") or "").strip().lower()
        self.auth_expires_at = int(auth.get("expires_at", 0) or 0)

    def _bootstrap_auth(self):
        """从首页脚本读取 __BROWSER_AUTH，拿到初始 inbox token。"""
        response = http_session.get(
            self.site_url,
            headers=self.headers,
            timeout=HTTP_TIMEOUT
        )
        if response.status_code != 200:
            return

        match = re.search(r"window\.__BROWSER_AUTH\s*=\s*(\{.*?\});", response.text)
        if not match:
            return

        try:
            auth = json.loads(match.group(1))
            self._apply_auth(auth)
        except Exception:
            return

    def _refresh_auth(self, email_address: str = ""):
        """调用 /api/inbox-token 刷新 token。"""
        payload_email = (email_address or self.current_email or self.auth_email or "").strip().lower()
        response = http_session.post(
            f"{self.base_url}/inbox-token",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"email": payload_email},
            timeout=HTTP_TIMEOUT
        )
        if response.status_code != 200:
            return

        data = response.json()
        if data.get("success") and data.get("auth"):
            self._apply_auth(data.get("auth", {}))

    def _api_request(self, method: str, path: str, *, params=None, json_body=None, extra_headers=None, auth_email: str = ""):
        if not self.inbox_token:
            self._bootstrap_auth()

        headers = {**self.headers, **(extra_headers or {})}
        if self.inbox_token:
            headers["X-Inbox-Token"] = self.inbox_token

        response = http_session.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            params=params,
            json=json_body,
            timeout=HTTP_TIMEOUT
        )

        if response.status_code in (401, 403):
            self._refresh_auth(auth_email)
            if self.inbox_token:
                headers["X-Inbox-Token"] = self.inbox_token
                response = http_session.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=HTTP_TIMEOUT
                )

        return response
    
    def generate_email(self):
        """
        从 API 获取一个新的临时邮箱地址
        返回: 邮箱地址字符串，失败返回 None
        """
        try:
            response = self._api_request(
                "GET",
                "/generate-email",
                extra_headers={"Content-Type": "application/json"},
                auth_email=self.current_email or ""
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("auth"):
                    self._apply_auth(result.get("auth", {}))
                if result.get('success') and result.get('data', {}).get('email'):
                    self.current_email = result['data']['email']
                    self.email_created_at = time.time()  # 记录创建时间
                    self.processed_mail_ids.clear()  # 清空已处理邮件列表
                    
                    # 预先获取现有邮件，标记为已处理（避免读取旧邮件）
                    existing_emails = self.fetch_emails(self.current_email)
                    for mail in existing_emails:
                        mail_id = self._get_mail_id(mail)
                        if mail_id:
                            self.processed_mail_ids.add(mail_id)
                    
                    if self.debug and existing_emails:
                        print(f"🔍 检测到 {len(existing_emails)} 封旧邮件，已标记忽略")
                    
                    return self.current_email
                else:
                    print(f"⚠️  API 返回异常: {result}")
            else:
                print(f"⚠️  API 错误: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 获取邮箱失败: {e}")
        
        return None
    
    def _get_mail_id(self, mail: dict) -> str:
        """获取邮件的唯一标识"""
        # 尝试多种可能的ID字段
        mail_id = mail.get('id') or mail.get('messageId') or mail.get('message_id')
        if mail_id:
            return str(mail_id)
        
        # 如果没有ID，用主题+发件人+时间组合作为唯一标识
        subject = mail.get('subject', '')
        sender = mail.get('from', '') or mail.get('sender', '')
        date = mail.get('date', '') or mail.get('received_at', '') or mail.get('created_at', '')
        if subject or sender:
            return f"{sender}|{subject}|{date}"
        
        return None
    
    def fetch_emails(self, email_address: str = None):
        """
        获取指定邮箱的邮件列表
        返回: 邮件列表，失败返回空列表
        """
        if email_address is None:
            email_address = self.current_email
        
        if not email_address:
            print("⚠️  未指定邮箱地址")
            return []
        
        try:
            # 添加时间戳防止缓存
            timestamp = int(time.time() * 1000)
            response = self._api_request(
                "GET",
                "/emails",
                params={"email": email_address, "_t": timestamp},
                extra_headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                },
                auth_email=email_address
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("auth"):
                    self._apply_auth(result.get("auth", {}))
                
                # 调试输出
                if self.debug:
                    print(f"\n🔍 API 原始响应: {result}")
                
                if result.get('success') and result.get('data', {}).get('emails'):
                    return result['data']['emails']
                elif result.get('success'):
                    # 成功但没有邮件
                    return []
                    
        except Exception as e:
            print(f"  获取邮件错误: {e}")
        
        return []
    
    def extract_code_from_email(self, email_data: dict):
        """
        从单封邮件中提取验证码
        支持格式: 6位数字 或 XXX-XXX (如 ABC-123)
        """
        # 合并所有可能包含验证码的字段
        subject = email_data.get('subject', '') or ''
        html_content = email_data.get('html_content', '') or ''
        text_content = email_data.get('text_content', '') or ''
        body = email_data.get('body', '') or ''
        content = email_data.get('content', '') or ''  # 新增：API返回的纯文本内容字段
        
        if self.debug:
            print(f"\n🔍 提取验证码 - 字段分析:")
            print(f"   subject: {subject[:50]}...")
            print(f"   content 长度: {len(content)}")
            print(f"   html_content 长度: {len(html_content)}")
        
        # 策略1: 优先从 HTML 中的 <div class="code"> 提取 (最精确)
        if html_content:
            # AWS 验证邮件的验证码在 <div class="code">...</div> 中
            code_div_pattern = r'<div[^>]*class="code"[^>]*>(\d{6})</div>'
            match = re.search(code_div_pattern, html_content, re.IGNORECASE)
            if match:
                code = match.group(1)
                if self.debug:
                    print(f"   ✅ 从 HTML code div 提取: {code}")
                return code
        
        # 策略2: 从纯文本 content 字段提取 (API 返回的主要字段)
        if content:
            # AWS 格式: "Verification code:: 123456" 或 "Verification code: 123456"
            code_pattern = r'[Vv]erification\s+code:+\s*(\d{6})'
            match = re.search(code_pattern, content)
            if match:
                code = match.group(1)
                if self.debug:
                    print(f"   ✅ 从 content 字段提取: {code}")
                return code
        
        # 策略3: 通用正则匹配 (备用)
        combined = f"{content} {text_content} {body}"
        
        # 验证码正则模式 (按优先级排序)
        patterns = [
            (r'[Vv]erification\s+code:+\s*(\d{6})', 'verification code 格式'),
            (r'code:+\s*(\d{6})', 'code: 格式'),
            (r'\b([A-Z0-9]{3}-[A-Z0-9]{3})\b', 'XXX-XXX 格式'),
            (r'验证码[：:\s]+(\d{6})', '中文验证码格式'),
        ]
        
        for pattern, desc in patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                code = match.group(1)
                if self.debug:
                    print(f"   ✅ 通过 {desc} 提取: {code}")
                return code
        
        # 策略4: 最后尝试从 HTML 提取任意6位数字 (最不精确)
        # 注意：这可能匹配到 CSS 中的数字，所以放在最后
        if html_content:
            # 排除明显的 CSS 值 (如 min-device-width: 320px)
            # 只匹配看起来像验证码的位置
            clean_html = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub(r'<[^>]+>', ' ', clean_html)  # 移除所有HTML标签
            
            match = re.search(r'\b(\d{6})\b', clean_html)
            if match:
                code = match.group(1)
                if self.debug:
                    print(f"   ⚠️ 从清理后的HTML提取 (可能不准确): {code}")
                return code
        
        if self.debug:
            print(f"   ❌ 未能提取到验证码")
        return None
    
    def wait_for_code(self, email_address: str = None, timeout: int = 120):
        """
        等待并提取验证码
        返回: 验证码字符串，超时返回 None
        """
        if email_address is None:
            email_address = self.current_email
        
        print(f"📧 正在监听邮箱: {email_address}")
        print(f"⏳ 最长等待 {timeout} 秒...")
        print(f"🔍 调试模式: {'开启' if self.debug else '关闭'}")
        print(f"📋 已忽略的旧邮件数: {len(self.processed_mail_ids)}")
        
        start_time = time.time()
        poll_interval = 5  # 每5秒轮询一次（避免请求过快）
        
        while time.time() - start_time < timeout:
            emails = self.fetch_emails(email_address)
            
            if emails and len(emails) > 0:
                for mail in emails:
                    # 获取邮件唯一ID
                    mail_id = self._get_mail_id(mail)
                    
                    # 跳过已处理的邮件
                    if mail_id and mail_id in self.processed_mail_ids:
                        if self.debug:
                            print(f"  ⏭️  跳过已处理邮件: {mail.get('subject', 'N/A')[:30]}")
                        continue
                    
                    # 标记为已处理
                    if mail_id:
                        self.processed_mail_ids.add(mail_id)
                    
                    # 检查是否是 AWS 相关邮件
                    sender = str(mail.get('from', '') or mail.get('sender', '')).lower()
                    subject = str(mail.get('subject', '')).lower()
                    
                    if self.debug:
                        print(f"\n📬 新邮件:")
                        print(f"   ID: {mail_id}")
                        print(f"   发件人: {sender}")
                        print(f"   主题: {mail.get('subject', 'N/A')}")
                        print(f"   时间: {mail.get('date', 'N/A')}")
                    
                    # AWS 验证邮件的特征
                    if any(keyword in sender or keyword in subject
                           for keyword in ['amazon', 'aws', 'verify', 'verification', 'builder']):
                        
                        code = self.extract_code_from_email(mail)
                        if code:
                            print(f"\n✅ 收到 AWS 验证邮件!")
                            print(f"   主题: {mail.get('subject', 'N/A')}")
                            print(f"   验证码: {code}")
                            return code
                        else:
                            print(f"  ⚠️  邮件匹配但未提取到验证码")
                            if self.debug:
                                print(f"   HTML内容: {mail.get('html_content', 'N/A')[:200]}...")
            
            elapsed = int(time.time() - start_time)
            print(f"  ⏳ 等待新邮件... ({elapsed}/{timeout}秒)    ", end='\r')
            time.sleep(poll_interval)
        
        print(f"\n❌ 等待验证邮件超时 ({timeout}秒)")
        return None


# ========================================================
# 全局邮箱客户端实例
# ========================================================
_mail_client = ChatGPTMailClient()


def create_temp_email():
    """
    创建临时邮箱 (使用 mail.chatgpt.org.uk 服务)
    返回: (邮箱地址, 邮箱地址)，失败返回 (None, None)
    
    注意: 第二个返回值原本是 JWT token，这里为了兼容性返回邮箱地址本身
    """
    print("📧 正在创建临时邮箱 (mail.chatgpt.org.uk)...")
    
    email_address = _mail_client.generate_email()
    
    if email_address:
        print(f"✅ 邮箱创建成功: {email_address}")
        # 返回 (邮箱地址, 邮箱地址) 以兼容原有接口
        return email_address, email_address
    else:
        print("❌ 创建邮箱失败")
        return None, None


def wait_for_verification_email(email_or_token: str, timeout: int = None):
    """
    等待并提取验证码
    
    参数:
        email_or_token: 邮箱地址 (兼容原有的 jwt_token 参数)
        timeout: 超时时间（秒）
    
    返回: 验证码字符串，未找到返回 None
    """
    if timeout is None:
        timeout = EMAIL_WAIT_TIMEOUT
    
    return _mail_client.wait_for_code(email_or_token, timeout)


# ========================================================
# 兼容旧版 Cloudflare Worker 的函数 (备用)
# ========================================================

def create_temp_email_cloudflare():
    """
    创建临时邮箱 (使用自部署的 Cloudflare Worker)
    返回: (邮箱地址, JWT令牌)，失败返回 (None, None)
    """
    print("正在创建临时邮箱 (Cloudflare Worker)...")

    prefix = ''.join(random.choices(
        string.ascii_lowercase + string.digits,
        k=EMAIL_PREFIX_LENGTH
    ))

    headers = {
        "Content-Type": "application/json",
        "User-Agent": get_user_agent()
    }

    try:
        response = http_session.post(
            f"{EMAIL_WORKER_URL}/api/new_address",
            headers=headers,
            json={"name": prefix},
            timeout=HTTP_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            jwt_token = result.get('jwt')
            actual_email = result.get('address')

            if jwt_token and actual_email:
                print(f"邮箱创建成功: {actual_email}")
                return actual_email, jwt_token
            elif jwt_token:
                fallback_email = f"tmp{prefix}@{EMAIL_DOMAIN}"
                print(f"邮箱创建成功: {fallback_email}")
                return fallback_email, jwt_token
        else:
            print(f"API 错误: HTTP {response.status_code}")

    except Exception as e:
        print(f"创建邮箱失败: {e}")

    return None, None


def fetch_emails_cloudflare(jwt_token: str):
    """获取邮件列表 (Cloudflare Worker 版)"""
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "User-Agent": get_user_agent()
    }
    
    try:
        response = http_session.get(
            f"{EMAIL_WORKER_URL}/api/mails?limit=20&offset=0",
            headers=headers,
            timeout=HTTP_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return result.get('results', result.get('mails', []))
                
    except Exception as e:
        print(f"  获取邮件错误: {e}")
    
    return None


def get_email_detail_cloudflare(jwt_token: str, email_id: str):
    """获取邮件详情 (Cloudflare Worker 版)"""
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "User-Agent": get_user_agent()
    }
    
    try:
        response = http_session.get(
            f"{EMAIL_WORKER_URL}/api/mails/{email_id}",
            headers=headers,
            timeout=HTTP_TIMEOUT
        )
        
        if response.status_code == 200:
            return response.json()
            
    except Exception as e:
        print(f"  获取邮件详情错误: {e}")
    
    return None


def parse_raw_email(raw_content: str):
    """解析原始邮件内容"""
    result = {'subject': '', 'body': '', 'sender': ''}
    
    if not raw_content:
        return result
    
    try:
        msg = email.message_from_string(raw_content, policy=policy.default)
        result['subject'] = msg.get('Subject', '')
        result['sender'] = msg.get('From', '')
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ['text/plain', 'text/html']:
                    payload = part.get_payload(decode=True)
                    if payload:
                        result['body'] = payload.decode('utf-8', errors='ignore')
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                result['body'] = payload.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  解析邮件错误: {e}")
    
    return result
