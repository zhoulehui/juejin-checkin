#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稀土掘金每日签到 + 自动抽奖脚本（支持多账号）

多账号使用方法：
  本地运行：在脚本同目录下新建 cookies 文件夹，每个账号放一个 .txt 文件：
      cookies/账号1.txt   <- 文件内容为该账号的 Cookie
      cookies/账号2.txt   <- 文件内容为该账号的 Cookie
  云端运行（GitHub Actions 等）：设置环境变量 JUEJIN_COOKIES，每行一个账号，
     支持 "显示名=Cookie" 或直接写 Cookie。
  文件名/显示名就是账号名，脚本会逐个账号执行签到 + 抽奖。
  也兼容旧版单账号用法（juejin_cookie.txt / 命令行参数 / 环境变量 JUEJIN_COOKIE）。
"""

import requests
import json
import time
import os
import sys

# 设置标准输出为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from typing import Optional

# 掘金 API 基础 URL
BASE_URL = "https://api.juejin.cn"

class JuejinCheckin:
    def __init__(self, cookie: str):
        """
        初始化 JuejinCheckin

        Args:
            cookie: 掘金网站的 Cookie 字符串
        """
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Cookie": cookie,
            "Origin": "https://juejin.cn",
            "Referer": "https://juejin.cn/",
            "Accept": "application/json, text/plain, */*",
        })

    def check_in(self, debug: bool = False) -> dict:
        """
        执行每日签到

        Returns:
            dict: 签到结果
        """
        # 需要添加 aid=5240 参数，否则 API 返回空响应
        url = f"{BASE_URL}/growth_api/v1/check_in?aid=5240"

        try:
            response = self.session.post(url)

            # 调试信息
            if debug:
                print(f"\n[调试] 签到请求详细信息:")
                print(f"  请求 URL: {url}")
                print(f"  请求方法：POST")
                print(f"  响应状态码：{response.status_code}")
                print(f"  响应原始内容：{response.text[:500]}")

            try:
                result = response.json()
            except json.JSONDecodeError as e:
                if debug:
                    print(f"  JSON 解析失败：{e}")
                return {
                    "success": False,
                    "message": f"响应解析失败：{str(e)}",
                    "data": {"raw_response": response.text},
                    "debug": {
                        "status_code": response.status_code,
                        "raw_response": response.text
                    }
                }

            if result.get("err_no") == 0:
                return {
                    "success": True,
                    "message": "签到成功!",
                    "data": result.get("data", {})
                }
            elif result.get("err_no") == 403 or '今日已签到' in result.get('err_msg', ''):
                return {
                    "success": False,
                    "message": "今日已签到",
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "message": f"签到失败：{result.get('err_msg', '未知错误')} (错误码：{result.get('err_no')})",
                    "data": result,
                    "debug": {
                        "err_no": result.get("err_no"),
                        "err_msg": result.get("err_msg"),
                        "status_code": response.status_code
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"签到异常：{str(e)}",
                "data": {},
                "debug": {"exception": str(e)}
            }

    def get_lottery_config(self) -> dict:
        """
        获取抽奖配置（剩余次数等）

        Returns:
            dict: 抽奖配置信息
        """
        # 需要添加 aid=5240 参数
        url = f"{BASE_URL}/growth_api/v1/lottery_config/get?aid=5240"

        try:
            response = self.session.get(url)
            result = response.json()

            if result.get("err_no") == 0:
                return {
                    "success": True,
                    "data": result.get("data", {})
                }
            else:
                return {
                    "success": False,
                    "message": result.get("err_msg", "获取配置失败"),
                    "data": {}
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取配置异常：{str(e)}",
                "data": {}
            }

    def draw_lottery(self) -> dict:
        """
        执行单次抽奖

        Returns:
            dict: 抽奖结果
        """
        # 需要添加 aid=5240 参数
        url = f"{BASE_URL}/growth_api/v1/lottery/draw?aid=5240"

        try:
            response = self.session.post(url)
            result = response.json()

            if result.get("err_no") == 0:
                prize = result.get("data", {}).get("lottery_name", "未中奖")
                return {
                    "success": True,
                    "message": f"抽奖结果：{prize}",
                    "data": result.get("data", {})
                }
            else:
                return {
                    "success": False,
                    "message": f"抽奖失败：{result.get('err_msg', '未知错误')}",
                    "data": result
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"抽奖异常：{str(e)}",
                "data": {}
            }

    def get_current_points(self) -> dict:
        """
        获取当前积分

        Returns:
            dict: 积分信息
        """
        url = f"{BASE_URL}/growth_api/v1/get_cur_point"

        try:
            response = self.session.get(url)
            result = response.json()

            if result.get("err_no") == 0:
                return {
                    "success": True,
                    "points": result.get("data", 0)
                }
            else:
                return {
                    "success": False,
                    "message": result.get("err_msg", "获取积分失败"),
                    "points": 0
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取积分异常：{str(e)}",
                "points": 0
            }

    def run(self, auto_draw: bool = True, debug: bool = False, account_name: str = ""):
        """
        运行完整的签到 + 抽奖流程

        Args:
            auto_draw: 是否自动抽奖，默认 True
            debug: 是否显示调试信息，默认 False
            account_name: 账号名（多账号模式下用于标识当前账号），默认空
        """
        title = f"稀土掘金签到脚本 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if account_name:
            title = f"[{account_name}] {title}"
        print("=" * 50)
        print(title)
        print("=" * 50)

        # 1. 执行签到
        print("\n[1] 执行签到...")
        checkin_result = self.check_in(debug=debug)
        print(f"    {checkin_result['message']}")

        # 2. 获取当前积分
        print("\n[2] 查询当前积分...")
        points_result = self.get_current_points()
        if points_result["success"]:
            print(f"    当前积分：{points_result['points']}")
        else:
            print(f"    {points_result['message']}")

        # 3. 执行抽奖
        if auto_draw:
            print("\n[3] 执行抽奖...")
            config_result = self.get_lottery_config()

            if config_result["success"]:
                free_count = config_result["data"].get("free_count", 0)
                print(f"    剩余免费抽奖次数：{free_count}")

                if free_count > 0:
                    # 执行免费抽奖
                    for i in range(free_count):
                        print(f"    第 {i+1} 次抽奖...")
                        draw_result = self.draw_lottery()
                        print(f"    {draw_result['message']}")
                        time.sleep(1)  # 避免请求过快
                else:
                    print("    没有免费抽奖次数")
                    print("    提示：每日签到后可获得 1 次免费抽奖机会")
            else:
                print(f"    {config_result.get('message', '获取抽奖配置失败')}")

        print("\n" + "=" * 50)
        print("任务完成!")
        print("=" * 50)


def get_script_dir() -> str:
    """返回脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))


def load_cookie_from_file(filepath: str) -> Optional[str]:
    """
    从单个文件加载 Cookie

    Args:
        filepath: Cookie 文件路径

    Returns:
        str or None: Cookie 字符串，失败返回 None
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            cookie = f.read().strip()
            if cookie:
                return cookie
    except FileNotFoundError:
        print(f"Cookie 文件不存在：{filepath}")
    except Exception as e:
        print(f"读取 Cookie 文件失败：{e}")
    return None


def load_all_cookies() -> list:
    """
    加载所有账号的 Cookie（多账号模式）

    扫描脚本目录下的 cookies 文件夹：
    - 文件夹内每个 .txt 文件代表一个账号
    - 文件名（不含扩展名）作为账号名，文件内容是 Cookie

    Returns:
        list[tuple[str, str]]: [(账号名, Cookie), ...]，没有则返回空列表
    """
    accounts = []
    cookies_dir = os.path.join(get_script_dir(), "cookies")

    if os.path.isdir(cookies_dir):
        for fname in sorted(os.listdir(cookies_dir)):
            if fname.lower().endswith(".txt"):
                filepath = os.path.join(cookies_dir, fname)
                cookie = load_cookie_from_file(filepath)
                if cookie:
                    name = os.path.splitext(fname)[0]
                    accounts.append((name, cookie))
    else:
        print(f"未找到 cookies 文件夹：{cookies_dir}")

    return accounts


def main():
    """主函数"""
    print("稀土掘金每日签到 + 抽奖脚本（支持多账号）\n")

    cookie = None

    # 1. 命令行参数（单账号，兼容旧用法）
    if len(sys.argv) > 1:
        cookie = sys.argv[1].strip()

    if cookie:
        checkin = JuejinCheckin(cookie)
        checkin.run(auto_draw=True)
        return

    accounts = []

    # 2. 多账号环境变量 JUEJIN_COOKIES（用于 GitHub Actions 等云端场景）
    #    每行一个账号：支持 "显示名=Cookie" 或直接写 Cookie
    multi = os.getenv("JUEJIN_COOKIES")
    if multi:
        for idx, line in enumerate(multi.strip().splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            if "=" in line:
                name, _, ck = line.partition("=")
                name, ck = name.strip(), ck.strip()
            else:
                name, ck = f"账号{idx}", line.strip()
            if ck:
                accounts.append((name, ck))

    # 3. 单账号环境变量（兼容旧用法）
    if not accounts:
        single = os.getenv("JUEJIN_COOKIE")
        if single:
            accounts = [("默认账号", single)]

    # 4. 多账号模式：读取 cookies 文件夹下所有账号（本地用法）
    if not accounts:
        accounts = load_all_cookies()
    if not accounts:
        # 5. 兼容旧版单账号文件 juejin_cookie.txt
        single = load_cookie_from_file(os.path.join(get_script_dir(), "juejin_cookie.txt"))
        if single:
            accounts = [("默认账号", single)]

    if not accounts:
        print("错误：未找到任何账号的 Cookie！")
        print("多账号模式：在脚本目录下新建 cookies 文件夹，每个账号放一个 .txt 文件")
        print("  例如：cookies/账号1.txt  cookies/账号2.txt，文件内容为该账号的 Cookie")
        print("旧版单账号模式：将 Cookie 保存到 juejin_cookie.txt，或使用命令行参数 / 环境变量 JUEJIN_COOKIE")
        print("\n获取 Cookie 方法:")
        print("  1. 打开 https://juejin.cn/ 并登录")
        print("  2. 按 F12 打开开发者工具")
        print("  3. 刷新页面，在 Network 标签找到任意请求")
        print("  4. 复制请求头中的 Cookie 值")
        return

    print(f"共发现 {len(accounts)} 个账号，开始逐个签到...\n")
    for i, (name, account_cookie) in enumerate(accounts, 1):
        checkin = JuejinCheckin(account_cookie)
        checkin.run(auto_draw=True, account_name=f"{name}（{i}/{len(accounts)}）")
        time.sleep(2)  # 账号之间稍作停顿，避免请求过快

    print("\n全部账号处理完成！")


if __name__ == "__main__":
    main()
