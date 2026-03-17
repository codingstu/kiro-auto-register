import os
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from runners.main import run
from runners.post_register_probe import run_post_probe


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main():
    register_count = _env_int("REGISTER_COUNT", 1)
    register_interval = _env_int("REGISTER_INTERVAL", 30)
    post_probe = _env_bool("POST_PROBE", True)
    probe_timeout = _env_int("PROBE_TIMEOUT", 25)

    if register_count < 0:
        print("❌ REGISTER_COUNT 不能小于 0")
        return

    print("=" * 60)
    print("🚀 非交互流水线启动")
    print(f"   注册数量: {register_count}")
    print(f"   注册间隔: {register_interval}s")
    print(f"   注册后探测: {'开启' if post_probe else '关闭'}")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    if register_count == 0:
        print("ℹ️ REGISTER_COUNT=0，跳过注册阶段")
    else:
        for i in range(register_count):
            print(f"\n#### 第 {i + 1}/{register_count} 个账号 ####")
            try:
                ok = run()
                if ok:
                    success_count += 1
                    print(f"✅ 第 {i + 1} 个账号流程完成")
                else:
                    fail_count += 1
                    print(f"❌ 第 {i + 1} 个账号流程未完成（未拿到有效凭证）")
            except Exception as exc:
                fail_count += 1
                print(f"❌ 第 {i + 1} 个账号流程异常: {exc}")

            if i < register_count - 1 and register_interval > 0:
                print(f"⏳ 等待 {register_interval}s 后继续...")
                time.sleep(register_interval)

    print("\n" + "=" * 60)
    print("📊 注册阶段结束")
    print(f"   成功: {success_count}")
    print(f"   失败: {fail_count}")
    print("=" * 60)

    if post_probe:
        project_root = Path(__file__).resolve().parents[2]
        print("\n🔎 开始执行注册后可用性探测...")
        summary = run_post_probe(project_root, probe_timeout=probe_timeout)
        print(f"📄 探测汇总: {summary}")


if __name__ == "__main__":
    main()
