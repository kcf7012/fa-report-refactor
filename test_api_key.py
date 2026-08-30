"""OpenAI API Key 驗證測試

使用方式:
    python test_api_key.py

說明:
    這個腳本會用您的 .env 中的 API key 呼叫真實的 OpenAI API,
    驗證 key 是否有效、模型是否可存取。

    ⚠️ 注意:會消耗少量 token(約 100 tokens,$0.0001 USD)
"""

import sys
from pathlib import Path

# 確保 src/ 在 path 中
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))


def main():
    print("=" * 60)
    print("OpenAI API Key 驗證測試")
    print("=" * 60)
    print()

    # 1. 載入 .env
    try:
        from dotenv import load_dotenv

        env_path = ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✓ 已載入 .env: {env_path}")
        else:
            print(f"⚠️ .env 不存在於 {env_path}")
    except ImportError:
        print("⚠️ python-dotenv 未安裝,跳過 .env 載入")

    # 2. 檢查環境變數
    import os

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("✗ 錯誤:OPENAI_API_KEY 環境變數未設定")
        print("  請在 .env 檔案中設定,或在執行前 export OPENAI_API_KEY=...")
        sys.exit(1)

    masked_key = f"{api_key[:10]}...{api_key[-4:]}"
    print(f"✓ API key 已找到:{masked_key} (長度:{len(api_key)})")
    print()

    model = os.environ.get("FA_IMPROVER_MODEL", "gpt-4o-mini")
    print(f"✓ 使用模型:{model}")
    print()

    # 3. 呼叫 OpenAI API
    print("-" * 60)
    print("正在呼叫 OpenAI API...")
    print()

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            timeout=30.0,
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一個助理。請用繁體中文回答。",
                },
                {
                    "role": "user",
                    "content": "請回答:FA 報告是什麼?(20字以內)",
                },
            ],
            max_tokens=100,
            temperature=0.0,
        )

        # 4. 顯示結果
        print("✓ API 呼叫成功!")
        print(f"  模型:{response.model}")
        print("  Token 使用:")
        print(f"    - prompt: {response.usage.prompt_tokens}")
        print(f"    - completion: {response.usage.completion_tokens}")
        print(f"    - total: {response.usage.total_tokens}")
        print()
        print("  回應內容:")
        print(f"    {response.choices[0].message.content}")
        print()

        # 5. 估算成本
        costs = {
            "gpt-4o-mini": (0.15, 0.60),  # input, output per 1M tokens
            "gpt-4o": (2.50, 10.00),
            "gpt-4o-2024-08-06": (2.50, 10.00),
            "gpt-3.5-turbo": (0.50, 1.50),
            "o1-mini": (3.00, 12.00),
        }
        if model in costs:
            in_rate, out_rate = costs[model]
            in_cost = response.usage.prompt_tokens * in_rate / 1_000_000
            out_cost = response.usage.completion_tokens * out_rate / 1_000_000
            total_cost = in_cost + out_cost
            print(f"  預估成本:${total_cost:.6f} USD")
        print()

        print("=" * 60)
        print("✓ 測試通過!您的 API key 有效且模型可存取")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"✗ API 呼叫失敗:{type(e).__name__}:{e}")
        print()
        print("可能原因:")
        print("  1. API key 無效或過期")
        print("  2. 模型名稱錯誤(可能需要付費帳號)")
        print("  3. 網路問題")
        print("  4. API key 沒有該模型的存取權限")
        return 1


if __name__ == "__main__":
    sys.exit(main())
