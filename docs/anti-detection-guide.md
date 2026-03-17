# 🛡️ 高级反检测和邮箱管理指南

## 📋 新增功能总览

你的项目现在已经升级了三个关键系统：

### 1. **高级反检测系统** (`anti_detect.py`)
反检测管理器会为每个注册生成唯一的用户行为档案，包括：
- ✅ **WebDriver 完全隐藏** - 12层深度反检测脚本
- ✅ **浏览器指纹混淆** - CPU/内存/GPU/时区随机化
- ✅ **自适应延迟** - 基于行为档案的智能延迟
- ✅ **随机鼠标移动** - 贝塞尔曲线轨迹 + 自然抖动
- ✅ **追踪防护** - 阻止 GA/Sentry/Mixpanel 等追踪脚本
- ✅ **性能数据伪装** - 随机堆内存大小和加载时间

### 2. **用户邮箱管理** (`email_manager.py`)
支持邮箱池管理，让你可以：
- 📧 添加自己的真实 Outlook/Gmail 邮箱（带 App Password）
- 🔄 自动轮换使用邮箱，减少单个邮箱被标记的风险
- ⏱️ 追踪每个邮箱的使用次数和最后使用时间
- ❌ 动态禁用/启用邮箱
- 📊 查看邮箱池状态

### 3. **改进的浏览器工厂** (`browser_factory.py`)
- 🔐 自动注入反检测脚本到所有新浏览器实例
- 📊 打印详细的用户行为档案（每次注册都不同）

---

## 🚀 快速开始

### 步骤 1: 准备邮箱池

在注册前，你可以添加自己的真实邮箱来提高成功率：

```python
from helpers.email_manager import email_manager

# 添加真实邮箱 (Outlook 示例)
email_manager.add_real_email(
    email="your_outlook@outlook.com",
    app_password="your-app-specific-password",  # 不是邮箱密码！
    description="主要 Outlook 邮箱"
)

# 添加第二个邮箱
email_manager.add_real_email(
    email="another_outlook@outlook.com",
    app_password="another-app-password",
    description="备用邮箱"
)

# 查看邮箱池
email_manager.list_emails()
```

### 步骤 2: 运行注册

```bash
python src/runners/main.py
```

程序会自动：
1. 从邮箱池中选择（优先使用真实邮箱，使用次数最少的）
2. 生成唯一的用户行为档案
3. 注入反检测脚本
4. 执行注册流程

---

## 📧 如何获取 Gmail/Outlook App Password

### Gmail (推荐用于此场景)

1. 启用两步验证：https://myaccount.google.com/security
2. 进入 app passwords：https://myaccount.google.com/apppasswords
3. 选择"邮件"和"Windows 电脑"
4. Google 会生成 16 位密码，复制它

```python
email_manager.add_real_email(
    email="your_email@gmail.com",
    app_password="xxxx xxxx xxxx xxxx",  # 16位，需移除空格
    description="Gmail 邮箱"
)
```

### Outlook

1. 进入账户设置：https://account.microsoft.com/account/security
2. 应用和设备 → 应用密码
3. 选择"邮件"和"Windows"
4. 复制生成的密码

```python
email_manager.add_real_email(
    email="your_email@outlook.com",
    app_password="your-generated-app-password",
    description="Outlook 邮箱"
)
```

---

## 🎯 反检测工作原理

### 每次注册的独特特征

```
📊 用户行为档案:
  🆔 用户ID: a1b2c3d4e5f6g7h8...
  ⌨️  打字速度: 0.087s/字符
  🖱️  点击延迟: 0.234s
  💾 设备内存: 16GB
  🔧 CPU核心: 8
  🌍 语言: en-US
  🕐 时区偏移: -300分钟
```

每次运行时，这些值都会**完全随机化**，模拟不同的真实用户。

### 隐形脚本覆盖

脚本在以下方面进行了伪装：

| 检测点 | 伪装方式 |
|------|--------|
| `navigator.webdriver` | 设为 `undefined` |
| `__webdriver_evaluate` | 删除 |
| `chrome.runtime` | 伪装为空对象 |
| 硬件信息 | CPU/内存随机化 |
| Canvas 指纹 | 返回伪假结果 |
| WebGL | 伪装 Intel 显卡 |
| 插件列表 | 虚拟 PDF 插件 |
| DevTools 检测 | 禁用检测代码 |
| 时区精度 | 降低精度+随机偏移 |
| 性能数据 | 随机化堆内存大小 |

---

## ⚙️ 高级配置

### 调整延迟

如果需要更快或更慢的注册，可以修改 `config.yaml`:

```yaml
# 应用全局延迟倍数（1.0 = 正常速度）
delay_multiplier: 1.2  # 增加 20% 延迟，更像真人
```

### 禁用真实邮箱

如果临时不想使用某个邮箱：

```python
from helpers.email_manager import email_manager

email_manager.disable_email("your_outlook@outlook.com")

# 后续需要时可以重新启用
email_manager.enable_email("your_outlook@outlook.com")
```

### 查看执行日志

每次注册会记录所有延迟和操作：

```python
from helpers.anti_detect import anti_detector

# 在注册完成后
print("执行模式日志:")
for pattern in anti_detector.execution_patterns:
    print(f"  {pattern['context']}: {pattern['delay']:.3f}s @ {pattern['timestamp']}")
```

---

## 🔍 故障排除

### 问题 1: 账户仍被封禁

**可能原因：**
- 代理 IP 质量差（被标记过）
- 邮箱之前被标记
- 注册流程中仍有异常行为

**解决方案：**
1. 切换代理 IP
2. 使用全新的邮箱（从未用于注册过）
3. 增加延迟: `delay_multiplier: 1.5`

### 问题 2: 检测到自动化

**表现：**
- Kiro 要求额外验证
- 邮箱验证链接失败
- "检测到异常行为"提示

**解决方案：**
1. 确保 `undetected-chromedriver` 已安装：`pip install undetected-chromedriver`
2. 在 `config.yaml` 中启用: `use_undetected_chrome: true`
3. 增加所有延迟：改用 `delay_multiplier: 2.0`
4. 手动运行一次验证系统是否可用

### 问题 3: 邮箱访问失败

**可能是：**
- App Password 过期
- 邮箱启用了新的安全策略
- 网络连接问题

**解决方案：**
```python
# 重新生成 App Password，然后：
email_manager.remove_email("your_email@gmail.com")
email_manager.add_real_email(
    email="your_email@gmail.com",
    app_password="new-16-digit-password",
    description="重新配置"
)
```

---

## 📊 性能优化建议

### 最佳实践

1. **使用 undetected-chromedriver**
   ```bash
   pip install undetected-chromedriver
   ```
   
2. **配置高质量代理**
   - 推荐静态代理（固定 IP）
   - 避免共享代理池
   - 定期更换代理 IP

3. **邮箱轮换策略**
   ```python
   # 添加 5-10 个邮箱到池中
   for i in range(5):
       email_manager.add_real_email(
           email=f"account{i}@gmail.com",
           app_password="xxxx xxxx xxxx xxxx",
           description=f"Gmail {i+1}"
       )
   ```

4. **随机注册间隔**
   ```
   在 main.py 中运行时，设置更大的间隔：
   Enter interval between registrations (default 30s): 45
   ```

5. **轮换浏览器引擎**
   ```yaml
   # 在 config.yaml 中轮换:
   browser:
     type: "chrome"  # 这次用 Chrome
     # 下次用 Edge
   ```

---

## 🔐 安全提示

⚠️ **重要：**
- 不要在同一IP上短时间内连续注册过多账户
- 不要使用免费/公共代理
- 不要泄露你的 App Passwords
- 定期检查邮箱是否有异常登录警告

---

## 📚 进阶：自定义行为档案

如果需要更高度定制的行为：

```python
from helpers.anti_detect import anti_detector

# 查看当前档案
print(anti_detector.behavior_profile)

# 自定义延迟
anti_detector.adaptive_delay(min_sec=1, max_sec=3, context="read")

# 手动注入脚本
anti_detector.inject_stealth_scripts(driver)
anti_detector.inject_tracking_prevention(driver)

# 打印执行统计
for pattern in anti_detector.execution_patterns[-10:]:
    print(pattern)
```

---

## 📞 需要帮助？

如果注册仍然失败：

1. **检查 README 中的日志**
   查看 `logs/` 目录下是否有错误信息

2. **启用调试模式**
   在 `config.yaml` 中设置：
   ```yaml
   headless: false  # 可视化运行，观察页面交互
   ```

3. **测试单个邮箱**
   使用 `single_outlook_run.py` 或 `debug_aws_login.py` 逐步排查

4. **检查 Kiro 政策变化**
   频繁访问 https://app.kiro.dev，了解最新反检测政策

---

**祝你好运！💪**
