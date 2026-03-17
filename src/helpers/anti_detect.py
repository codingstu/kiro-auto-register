"""
高级反检测模块 - 伪装浏览器指纹、隐藏 WebDriver 标记、随机行为
"""

import random
import time
import string
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class AntiDetectionManager:
    """反检测管理器 - 综合伪装和隐形策略"""
    
    def __init__(self):
        self.execution_patterns = []
        self.request_patterns = []
        self.behavior_profile = self._generate_behavior_profile()
    
    def _generate_behavior_profile(self) -> Dict[str, Any]:
        """
        生成唯一的用户行为档案
        模拟真实用户的行为特征
        """
        profile = {
            'typing_speed': random.uniform(0.05, 0.15),  # 打字速度（秒/字符）
            'click_delay': random.uniform(0.1, 0.5),      # 点击延迟
            'scroll_speed': random.uniform(0.5, 2.0),     # 滚动速度
            'mouse_jitter': random.uniform(1, 8),         # 鼠标抖动（像素）
            'think_probability': random.uniform(0.05, 0.2),  # 思考停顿概率
            'think_duration': random.uniform(1, 4),       # 思考时长（秒）
            'reading_time': random.uniform(0.5, 3),       # 阅读时间
            'device_memory': random.choice([4, 8, 16, 32]),  # 设备内存
            'cpu_cores': random.choice([2, 4, 8, 16]),    # CPU核心数
            'screen_depth': random.choice([24, 32]),      # 色彩深度
            'timezone_offset': random.choice([-480, -420, -360, -300, -240, 0, 60, 120, 330, 480, 540, 570, 630]),  # 时区
            'language': random.choice(['en-US', 'en-GB', 'de-DE', 'ja-JP']),
            'unique_id': self._generate_unique_id(),      # 唯一标识
        }
        return profile
    
    @staticmethod
    def _generate_unique_id() -> str:
        """生成唯一用户 ID（模拟真实用户指纹）"""
        return ''.join([secrets.choice(string.ascii_lowercase + string.digits) for _ in range(32)])

    @staticmethod
    def _safe_current_url(driver) -> str:
        try:
            return (driver.current_url or "").strip().lower()
        except Exception:
            return ""

    def _can_run_in_page_context(self, driver) -> bool:
        url = self._safe_current_url(driver)
        # about:blank / data: 页面不注入 execute_script，避免 localStorage 等 API 报错
        return url.startswith("http://") or url.startswith("https://")

    @staticmethod
    def _inject_on_new_document(driver, source: str) -> None:
        # 统一通过 CDP 提前注入，确保后续页面生效
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": source})
    
    def inject_stealth_scripts(self, driver) -> None:
        """
        注入隐形脚本 - 隐藏 WebDriver 检测和伪装浏览器属性
        """
        stealth_js = """
        // ===== 1. 隐藏 WebDriver 检测 =====
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // 隐藏 __webdriver_evaluate
        delete window.__webdriver_evaluate;
        
        // 隐藏 AutomationControlled 标记
        if (window.chrome === undefined) {
            window.chrome = {};
        }
        window.chrome.runtime = undefined;
        
        // ===== 2. 伪装 navigator 属性 =====
        const originalNavigator = window.navigator;
        const navigationProxy = new Proxy(navigator, {
            get: (target, prop) => {
                if (prop === 'webdriver') return false;
                if (prop === 'plugins') return [1, 2, 3];  // 虚拟插件
                if (prop === 'languages') return ['en-US'];
                if (prop === 'deviceMemory') return %d;  // 设备内存
                if (prop === 'hardwareConcurrency') return %d;  // CPU核心
                return target[prop];
            }
        });
        
        // ===== 3. 伪装 DevTools 检测 =====
        let devtools = { open: false, orientation: null };
        const threshold = 160;
        setInterval(function() {
            if (window.outerHeight - window.innerHeight > threshold ||
                window.outerWidth - window.innerWidth > threshold) {
                if (!devtools.open) {
                    devtools.open = true;
                }
            } else {
                if (devtools.open) {
                    devtools.open = false;
                }
            }
        }, 500);
        
        // ===== 4. 伪装性能数据 =====
        const originalPerformance = window.performance;
        Object.defineProperty(window, 'performance', {
            get: () => ({
                ...originalPerformance,
                memory: {
                    jsHeapSizeLimit: Math.random() * 2000000000,
                    totalJSHeapSize: Math.random() * 1000000000,
                    usedJSHeapSize: Math.random() * 500000000,
                },
            }),
        });
        
        // ===== 5. 伪装插件 =====
        const pluginArray = [
            {
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                name: "PDF Viewer",
                version: "1.0"
            },
            {
                description: "Chrome Native PDF Viewer",
                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                name: "Native Client Executable",
                version: "0.1"
            }
        ];
        Object.defineProperty(navigator, 'plugins', {
            get: () => pluginArray,
        });
        
        // ===== 6. 伪装 canvas 指纹 =====
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            if (type === 'image/png' || type === 'image/jpeg') {
                return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
            }
            return originalToDataURL.call(this, type);
        };
        
        // ===== 7. 伪装本地存储（需防御 data: 页面） =====
        try {
            const originalLocalStorage = window.localStorage;
            window.__localStorageProxy = new Proxy(originalLocalStorage, {
                get: (target, prop) => {
                    if (prop === 'getItem') {
                        return (key) => {
                            if (key && key.includes('chrome')) return null;
                            return target.getItem(key);
                        };
                    }
                    return target[prop];
                }
            });
        } catch (e) {
            // ignore storage not available for current protocol
        }
        
        // ===== 8. 隐藏 Chrome 特定对象 =====
        window.chrome = {
            runtime: {}
        };
        delete navigator.requestMediaKeySystemAccess;
        delete navigator.getBattery;
        
        // ===== 9. 伪装 Permissions API =====
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => 
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters);
        
        // ===== 10. 伪装时区 =====
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        Date.prototype.getTimezoneOffset = function() {
            return %d;  // 模拟时区偏移
        };
        
        // ===== 11. 随机化页面加载时间 =====
        window.pageLoadTime = Date.now() - Math.random() * 3000;
        
        // ===== 12. 伪装 WebGL =====
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';  // 伪装 GPU 厂商
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter(parameter);
        };
        """
        
        # 填入行为档案数据
        stealth_js = stealth_js % (
            self.behavior_profile['device_memory'],
            self.behavior_profile['cpu_cores'],
            self.behavior_profile['timezone_offset']
        )
        
        # 注入脚本：优先注入到新文档；仅在 http(s) 页面尝试当前页执行
        try:
            self._inject_on_new_document(driver, stealth_js)
            if self._can_run_in_page_context(driver):
                driver.execute_script(stealth_js)
            print("✅ 隐形脚本已注入 - WebDriver 完全隐藏")
        except Exception as e:
            print(f"⚠️ 隐形脚本注入失败: {e}")
    
    def random_mouse_movement(self, driver, x: int, y: int, steps: int = 5) -> None:
        """
        模拟真实鼠标移动 - 添加多个中间点和轨迹抖动
        """
        from selenium.webdriver.common.action_chains import ActionChains
        
        try:
            action = ActionChains(driver)
            
            # 当前鼠标位置（通过 body 元素作为参考）
            body = driver.find_element("tag name", "body")
            current_x, current_y = 0, 0
            
            # 生成中间点（贝塞尔曲线）
            for i in range(1, steps + 1):
                # 线性插值 + 随机抖动
                progress = i / (steps + 1)
                new_x = int(current_x + (x - current_x) * progress)
                new_y = int(current_y + (y - current_y) * progress)
                
                # 添加随机抖动
                jitter_x = random.randint(-int(self.behavior_profile['mouse_jitter']), 
                                         int(self.behavior_profile['mouse_jitter']))
                jitter_y = random.randint(-int(self.behavior_profile['mouse_jitter']), 
                                         int(self.behavior_profile['mouse_jitter']))
                
                new_x += jitter_x
                new_y += jitter_y
                
                # 随机延迟
                action.move_by_offset(new_x - current_x, new_y - current_y)
                action.pause(random.uniform(0.01, 0.05))
                
                current_x, current_y = new_x, new_y
            
            # 移动到最终位置
            final_jitter_x = random.randint(-int(self.behavior_profile['mouse_jitter']), 
                                           int(self.behavior_profile['mouse_jitter']))
            final_jitter_y = random.randint(-int(self.behavior_profile['mouse_jitter']), 
                                           int(self.behavior_profile['mouse_jitter']))
            action.move_by_offset(x - current_x + final_jitter_x, 
                                 y - current_y + final_jitter_y)
            
            action.perform()
        except Exception as e:
            print(f"⚠️ 鼠标移动失败: {e}")
    
    def adaptive_delay(self, min_sec: float = 0.5, max_sec: float = 2.0, 
                      context: str = "general") -> None:
        """
        自适应延迟 - 基于行为档案和上下文的智能延迟
        
        Args:
            min_sec: 最小延迟
            max_sec: 最大延迟
            context: 延迟上下文 ("click", "type", "read", "think")
        """
        if context == "click":
            delay = random.uniform(
                self.behavior_profile['click_delay'] * min_sec,
                self.behavior_profile['click_delay'] * max_sec
            )
        elif context == "type":
            delay = random.uniform(
                self.behavior_profile['typing_speed'],
                self.behavior_profile['typing_speed'] * 2
            )
        elif context == "read":
            delay = random.uniform(
                self.behavior_profile['reading_time'] * min_sec,
                self.behavior_profile['reading_time'] * max_sec
            )
        elif context == "think":
            # 偶尔有长时间的思考停顿
            if random.random() < self.behavior_profile['think_probability']:
                delay = random.uniform(
                    self.behavior_profile['think_duration'],
                    self.behavior_profile['think_duration'] * 2
                )
            else:
                delay = random.uniform(min_sec, max_sec)
        else:
            delay = random.uniform(min_sec, max_sec)
        
        # 记录执行模式
        self.execution_patterns.append({
            'context': context,
            'delay': delay,
            'timestamp': datetime.now()
        })
        
        time.sleep(delay)
    
    def generate_realistic_user_agent(self) -> str:
        """
        生成逼真的 User-Agent - 模拟最新浏览器版本
        """
        chrome_versions = [
            '120.0.0.0',
            '121.0.0.0',
            '122.0.0.0',
            '123.0.0.0',
        ]
        
        windows_versions = [
            'Windows NT 10.0; Win64; x64',  # Windows 10
            'Windows NT 10.0; Win64; x64; rv:109.0',  # Windows 11
        ]
        
        chrome_version = random.choice(chrome_versions)
        windows_version = random.choice(windows_versions)
        
        # 添加随机 WebKit/Safari 版本
        webkit_version = f'{random.randint(600, 610)}.{random.randint(1, 15)}.{random.randint(1, 100)}'
        
        user_agent = f'Mozilla/5.0 ({windows_version}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}'
        
        return user_agent
    
    def generate_request_headers(self) -> Dict[str, str]:
        """
        生成逼真的 HTTP 请求头
        """
        headers = {
            'User-Agent': self.generate_realistic_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': self.behavior_profile['language'],
            'Cache-Control': f'max-age={random.randint(0, 3600)}',
            'DNT': random.choice(['1', None]),
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': f'"Not A(Brand";v="{random.randint(8, 99)}", "Google Chrome";v="{random.randint(100, 124)}"',
            'Sec-Ch-Ua-Mobile': random.choice(['?0', '?1']),
            'Sec-Ch-Ua-Platform': random.choice(['"Windows"', '"Linux"', '"macOS"']),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 随机移除某些头（不同浏览器可能不同）
        if random.random() > 0.3:
            headers.pop('DNT', None)
        
        return {k: v for k, v in headers.items() if v is not None}
    
    def random_scroll_behavior(self, driver, element=None) -> None:
        """
        模拟真实滚动行为 - 非线性、有暂停
        """
        try:
            if element:
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
            else:
                # 随机滚动到页面不同位置
                scroll_height = driver.execute_script("return document.body.scrollHeight")
                scroll_to = random.randint(0, int(scroll_height * 0.8))
                
                # 分段滚动
                current_scroll = 0
                steps = random.randint(3, 8)
                scroll_step = scroll_to // steps
                
                for _ in range(steps):
                    current_scroll += scroll_step + random.randint(-50, 100)
                    driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                    self.adaptive_delay(0.2, 0.8, context="general")
            
            print("✅ 滚动完成")
        except Exception as e:
            print(f"⚠️ 滚动失败: {e}")
    
    def inject_tracking_prevention(self, driver) -> None:
        """
        注入追踪防护脚本 - 关闭追踪、限制指纹识别
        """
        tracking_protection = """
        // 阻止谷歌分析
        window.ga = undefined;
        window._gat = undefined;
        
        // 阻止 Sentry 错误追踪
        window.Sentry = undefined;
        
        // 阻止 Mixpanel 分析
        window.mixpanel = undefined;
        
        // 阻止 Segment 追踪
        window.analytics = undefined;
        
        // 伪装时间戳精度（防止高精度定时器指纹识别）
        const originalNow = window.performance.now;
        let timeOffset = Math.random() * 1000;
        window.performance.now = function() {
            return originalNow.call(performance) + timeOffset;
        };
        
        // 防止 performance.measureUserAgentSpecificMemory()
        if (performance.measureUserAgentSpecificMemory) {
            delete performance.measureUserAgentSpecificMemory;
        }
        """
        
        try:
            self._inject_on_new_document(driver, tracking_protection)
            if self._can_run_in_page_context(driver):
                driver.execute_script(tracking_protection)
            print("✅ 追踪防护已启用")
        except Exception as e:
            print(f"⚠️ 追踪防护注入失败: {e}")
    
    def get_behavior_summary(self) -> str:
        """
        获取用户行为档案总结
        """
        return f"""
📊 用户行为档案:
  🆔 用户ID: {self.behavior_profile['unique_id'][:16]}...
  ⌨️  打字速度: {self.behavior_profile['typing_speed']:.3f}s/字符
  🖱️  点击延迟: {self.behavior_profile['click_delay']:.3f}s
  💾 设备内存: {self.behavior_profile['device_memory']}GB
  🔧 CPU核心: {self.behavior_profile['cpu_cores']}
  🌍 语言: {self.behavior_profile['language']}
  🕐 时区偏移: {self.behavior_profile['timezone_offset']}分钟
        """


# 全局反检测管理器实例
anti_detector = AntiDetectionManager()
