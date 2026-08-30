# LLM Agent 整合設計

> **目標**:讓技能包從「被動執行」升級為「主動決策」的 Agent
> **願景**:Agent 不只執行改善,還會主動分析、規劃、學習

---

## 一、Agent vs LLM Client:差在哪?

### v3.0 LLM Client(LLM 作為工具)

```
使用者:「改善這份報告」
技能包: 呼叫 LLM 評估 → 套用樣板 → 輸出
```

- LLM 只負責單次評估或生成
- 沒有記憶、沒有規劃、沒有工具使用

### v3.0+ Agent(LLM 作為決策者)

```
使用者:「改善這份 Kobo 報告,並解釋為什麼這樣改」
Agent:
  1. (思考)這是 ESD 失效,需要 5-Why + 對照組 + SEM 證據
  2. (規劃)新增 4 張投影片,展開 Summary 為 3 張
  3. (執行)讀取 pptx → 套樣板 → 注入 LLM 生成內容
  4. (驗證)母片保護 ✓ / 內容密度 ✓ / 視覺元素 ✓
  5. (反思)這份報告的弱點在圖片品質,建議下次補拍
  6. (輸出)報告 + 改善說明 + 下次建議
```

---

## 二、Agent 核心能力

### 2.1 ReAct 推理迴圈

```python
class FAReportAgent:
    """具備推理 + 行動能力的 Agent"""
    
    def __init__(self, llm_client, tools: List[Tool]):
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}
        self.memory = ConversationMemory()
        self.max_iterations = 10
    
    def improve(self, report_path: str, goal: str) -> AgentResult:
        """主迴圈:Reason → Act → Observe"""
        
        observation = self._initial_observation(report_path)
        self.memory.add("user", goal)
        
        for i in range(self.max_iterations):
            # === Reason ===
            thought = self.llm.think(
                context=self.memory.get_context(),
                tools=list(self.tools.values()),
            )
            
            # === Act ===
            if thought.needs_tool:
                tool_result = self.tools[thought.tool_name].run(
                    **thought.tool_args
                )
                observation = tool_result
                self.memory.add("tool", tool_result)
            else:
                # Agent 決定結束
                return self._finalize(thought.final_answer)
            
            # === Observe ===
            if self._is_goal_achieved():
                return self._finalize(observation)
        
        return AgentResult(status="max_iterations_reached")
```

### 2.2 工具集(Tools)

Agent 可以呼叫的工具:

| 工具 | 功能 | 何時使用 |
|------|------|---------|
| `parse_pptx` | 解析 pptx 結構 | 開始時理解報告內容 |
| `evaluate_report` | 6 維度評分 | 決定改善方向 |
| `detect_failure_type` | 識別失效類型 | 套用專業樣板 |
| `find_master_layouts` | 列出可用 layout | 選擇合適版型 |
| `add_slide` | 新增投影片 | 執行改善 |
| `modify_slide` | 修改既有投影片 | 精細調整 |
| `verify_master_unchanged` | 驗證母片保護 | 每個動作後 |
| `generate_visual` | 生成視覺元素 | 為內容加圖示 |
| `render_preview` | 生成 PDF 預覽 | 驗證視覺效果 |
| `search_knowledge_base` | 搜尋相似案例 | 學習過往經驗 |

### 2.3 工具定義範例

```python
from pydantic import BaseModel, Field

class ParsePPTXTool(BaseModel):
    """解析 pptx 檔案,提取所有文字、表格、圖片資訊"""
    name: str = "parse_pptx"
    description: str = "讀取 pptx 檔案並回傳結構化內容"
    
    class Arguments(BaseModel):
        file_path: str = Field(..., description="pptx 檔案路徑")
    
    def run(self, file_path: str) -> dict:
        prs = Presentation(file_path)
        return {
            "slide_count": len(prs.slides),
            "slides": [
                {
                    "index": i,
                    "layout": slide.slide_layout.name,
                    "title": extract_title(slide),
                    "text_content": extract_text(slide),
                    "tables": extract_tables(slide),
                    "images": describe_images(slide),
                }
                for i, slide in enumerate(prs.slides)
            ],
        }


class DetectFailureTypeTool(BaseModel):
    """根據報告內容識別失效類型"""
    name: str = "detect_failure_type"
    description: str = "從報告文字推測失效類型(ESD/EOS/THERMAL/...)"
    
    class Arguments(BaseModel):
        report_text: str = Field(..., description="報告文字內容")
    
    def run(self, report_text: str) -> dict:
        prompt = f"""根據以下 FA 報告內容,判斷最可能的失效類型。
        只回傳 JSON: {{"failure_type": "ESD|EOS|THERMAL|MECHANICAL|PROCESS|MATERIAL|DESIGN|UNKNOWN", "confidence": 0.0-1.0, "reasoning": "..."}}
        
        報告:{report_text[:2000]}"""
        
        return self.llm.complete_json(prompt)
```

---

## 三、Agent 工作流程範例

### 完整對話範例

```python
# 場景:使用者給一份 ESD 失效報告,Agent 自主決策如何改善

# === 第 1 輪:理解任務 ===
User: "請改善這份 Kobo 報告(/path/to/kobo.pptx),這是 ESD 失效"

# === 第 2 輪:Reason ===
Agent Thought:
"我需要先理解這份報告的內容和缺失,才能決定改善策略。
讓我先解析 pptx 結構。"
Action: parse_pptx(file_path="/path/to/kobo.pptx")

# === 第 3 輪:Observe ===
Observation: {
  "slide_count": 5,
  "slides": [
    {"title": "Kobo ZHT F2 SPI 無法通訊 Fail Analysis Report", ...},
    {"title": "D0: Symptom(s) - 客退模組樣品", ...},
    ...
  ]
}

# === 第 4 輪:Reason ===
Agent Thought:
"報告有 5 張投影片,沒有 Summary、根因分析、改善對策。
讓我進行 6 維度評估。"
Action: evaluate_report(pptx_content="...", rubric="...")

# === 第 5 輪:Observe ===
Observation: {
  "total_score": 63.5,
  "dimensions": {
    "基本資訊完整性": 70,
    "根因分析": 50,
    "改善對策": 70,
    ...
  }
}

# === 第 6 輪:Reason + 規劃 ===
Agent Thought:
"缺失嚴重程度:
- 基本資訊:MODERATE → 新增 1 張
- 根因分析:SEVERE → 展開為 4 張(5-Why + 對照組 + 證據 + 統計)
- 改善對策:MODERATE → 展開為 3 張(時間軸 + IQC + 監測)
- Summary:不修改,但新增 Executive Summary 與 Key Improvements

失效類型:ESD,需要加入 ESD 防護設計建議。

預計新增投影片:1 + 4 + 3 + 2 = 10 張"
Action: notify_user(message="預計新增 10 張投影片,是否繼續?")

# === 第 7 輪:使用者確認後執行 ===
Agent: 開始執行改善...
Action: add_slide(layout="2L - Topic", title="FA 基本資訊", content=...)
Observation: Slide 6 added
Action: verify_master_unchanged()
Observation: ✓ Master preserved

Action: add_slide(layout="2L - Topic", title="5-Why 根因推導", content=...)
Action: add_slide(layout="2L - Topic", title="統計驗證方法", content=...)
...

# === 第 N 輪:反思 ===
Agent Thought:
"改善完成。讓我反思:
1. 母片保護:✓(XML 完全未變)
2. 內容密度:每張投影片 ≤ 200 字,符合原則
3. 視覺元素:每張都有 checklist 或流程圖
4. 失效類型:已加入 ESD 專屬建議

建議下次:
- 提供更高解析度的 IC 照片
- 補充 DVT golden sample 數據"
Action: generate_report()
```

---

## 四、Agent 與現有 LLM Client 的關係

### 架構圖

```
┌─────────────────────────────────────────────────────────┐
│                    FA Report Agent                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Reasoning Engine                     │  │
│  │  - 規劃(Planning)                                │  │
│  │  - 反思(Reflection)                              │  │
│  │  - 記憶(Memory)                                  │  │
│  └─────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Tool Registry                       │  │
│  │  parse_pptx │ evaluate │ add_slide │ verify ... │  │
│  └─────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │              LLM Clients                         │  │
│  │  OpenAI │ Anthropic │ Ollama │ Mock             │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 共用基礎建設

| 元件 | Agent 用 | LLM Client 用 |
|------|---------|---------------|
| Prompt 樣板 | ✓ | ✓ |
| 結構化輸出解析 | ✓ | ✓ |
| 重試 / 退避 | ✓ | ✓ |
| Token 使用追蹤 | ✓ | ✓ |
| 成本估算 | ✓ | ✓ |

---

## 五、何時用 Agent、何時用普通 LLM Client?

### 使用 Agent(複雜、需要規劃)
- 「改善這份 ESD 失效報告,並解釋為什麼」
- 「批次處理這 50 份報告,根據失效類型自動選樣板」
- 「這份報告特別弱在數據分析,加強這部分」

### 使用普通 LLM Client(簡單、明確)
- 「把這份文字評估成 JSON」(單純評估任務)
- 「生成 5-Why 內容」(單純生成任務)
- 「把這段中文翻譯成英文」(單純轉換任務)

---

## 六、實作優先順序

### Phase 3A:基礎(必要)
- [ ] Tool Registry 抽象層
- [ ] 5 個核心工具(parse_pptx, evaluate, add_slide, verify_master, render_preview)
- [ ] 簡單的 ReAct 迴圈

### Phase 3B:智慧化(選用)
- [ ] 規劃能力(Multi-step planning)
- [ ] 反思能力(失敗後重試)
- [ ] 記憶(跨 session 學習)

### Phase 3C:進階(未來)
- [ ] Multi-Agent(規劃 Agent + 執行 Agent + 驗證 Agent)
- [ ] 使用者互動(中斷、修改、繼續)
- [ ] 經驗累積(從過去改善學習)

---

## 七、範例:Agent Prompt 設計

### System Prompt

```
你是 FA 報告改善專家,具備以下能力:
1. 理解半導體失效分析(FA)報告的結構與缺失
2. 規劃多步驟改善策略
3. 呼叫工具執行具體動作
4. 驗證改善品質(母片保護、內容密度、視覺元素)
5. 反思並提出下次建議

工作原則:
- 母片絕對不能修改(每次動作後必須 verify)
- 一張投影片只講一件事
- 每張投影片至少 1 個視覺元素
- 改善後必須 render_preview 確認視覺

回應格式:Thought → Action → Observation
```

### ReAct 範本

```
可用工具:
{tool_descriptions}

當前狀態:
{current_state}

歷史動作與觀察:
{history}

請決定下一步:
1. 思考(Thought):你為什麼要做這個動作?
2. 動作(Action):呼叫哪個工具?參數是什麼?
3. 如果你已經達成目標,回傳 FINAL_ANSWER
```

---

## 八、風險與緩解

| 風險 | 緩解 |
|------|------|
| Agent 陷入無限迴圈 | max_iterations + 強制收斂條件 |
| Agent 做出破壞性動作 | 每個危險動作都需要 verify |
| LLM 幻覺導致錯誤決策 | 決策後必須用工具驗證 |
| 成本失控 | token 使用追蹤 + 預算上限 |
| Agent 不理解工具 | 詳細的 tool description + few-shot 範例 |

---

## 九、Coding Agent 風格的關鍵特性

### 9.1 為什麼要學 Coding Agent?

| Coding Agent 特性 | FA Report Agent 對應 |
|------------------|---------------------|
| 讀取程式碼理解上下文 | 讀取 pptx 理解報告 |
| 多檔案編輯 | 多投影片編輯 |
| 執行測試驗證 | render + 母片驗證 |
| 錯誤後重試 | 驗證失敗後調整 |
| 使用者互動(interrupt) | 等待使用者確認 |
| TodoWrite / 任務追蹤 | 改善計畫可視化 |
| 長期記憶 / 經驗累積 | 跨報告學習 |

### 9.2 TodoWrite 風格的任務追蹤

```python
class FAReportAgent:
    def __init__(self, ...):
        self.todo_list = TodoList()  # 可視化給使用者看

    def improve(self, report_path, goal):
        # === 開始前:建立 TodoList ===
        self.todo_list.set([
            "✓ 解析 pptx 結構",
            "✓ 評估 6 維度分數",
            "✓ 識別失效類型",
            "⏳ 規劃改善策略",
            "  新增 FA 基本資訊投影片",
            "  新增 5-Why 根因推導",
            "  新增統計驗證方法",
            "  新增關鍵驗證證據",
            "  新增改善對策總覽",
            "  新增 IQC 標準化",
            "  新增監測與知識管理",
            "  強化 Summary 為 3 張",
            "  render PDF 預覽驗證",
            "  母片保護最終驗證",
            "  生成變更說明文件",
        ])

        # === 執行中:逐步更新 ===
        for step in self.todo_list:
            self.todo_list.mark_in_progress(step)
            result = self.execute_step(step)
            if result.success:
                self.todo_list.mark_done(step)
            else:
                self.todo_list.mark_failed(step, reason=result.error)
```

**CLI 輸出範例**(使用者可以看到進度):
```
[1/15] ✓ 解析 pptx 結構
[2/15] ✓ 評估 6 維度分數
[3/15] ✓ 識別失效類型(ESD)
[4/15] ✓ 規劃改善策略(新增 10 張)
[5/15] ⏳ 新增 FA 基本資訊投影片...
[6/15] 新增 5-Why 根因推導
[14/15] ✓ 母片保護最終驗證
[15/15] ✓ 生成變更說明文件

全部完成!輸出: improved.pptx
變更說明: CHANGES.md
```

### 9.3 Interrupt 機制(像 Claude Code 的 Ctrl+C)

Coding Agent 的關鍵特性是**可中斷、可恢復**:

```python
class FAReportAgent:
    def __init__(self, ...):
        self.interrupt_event = threading.Event()
        self.state_checkpoint = None

    def interrupt(self):
        """使用者按下 Ctrl+C 時呼叫"""
        self.interrupt_event.set()

    def improve(self, report_path, goal):
        for step in self.todo_list:
            # === 檢查是否被中斷 ===
            if self.interrupt_event.is_set():
                self._save_checkpoint()  # 儲存目前狀態
                return AgentResult(
                    status="interrupted",
                    checkpoint=self.state_checkpoint,
                    message=f"已中斷於步驟 {step},可從 checkpoint 恢復"
                )

            # === 詢問使用者確認(關鍵決策點) ===
            if step.requires_user_confirmation:
                self._ask_user(step)
                if self.interrupt_event.is_set():
                    return AgentResult(status="interrupted")

            # === 執行並儲存 checkpoint ===
            self._save_checkpoint()
            result = self.execute_step(step)
```

**CLI 互動範例**:
```
Agent: 預計新增 10 張投影片,預估花費 $0.05 GPT-4o tokens。
       是否繼續? [Y/n/edit]
> User: edit
Agent: 請告訴我想修改什麼
> User: 5-Why 那張改用更詳細的 7-Why
Agent: ✓ 已更新計畫,重新開始...
```

### 9.4 Plan Mode(像 Claude Code 的 plan 模式)

Coding Agent 通常有「先看計畫再執行」的模式:

```bash
# Plan mode:只產生計畫,不執行
python fa_agent.py improve report.pptx --plan-only

# 輸出:PLAN.md
"""
# 改善計畫

## 評估結果
- 總分:63.5 (D 級)
- 主要缺失:根因分析、改善對策

## 預計新增投影片(共 10 張)
1. FA 基本資訊(Slide 6)
2. 5-Why 根因推導(Slide 7)
3. 統計驗證方法(Slide 8)
...

## 預估成本
- GPT-4o: $0.05
- 時間: 約 30 秒
"""
```

### 9.5 變更說明文件(CHANGES.md)

像 Coding Agent 的 commit message,自動產生變更記錄:

```markdown
# 變更說明 - 2026-08-30

## 摘要
- 輸入:Kobo RA6080 SPcomFailI.pptx (5 張)
- 輸出:Kobo RA6080 SPcomFailI_improved.pptx (15 張)
- 評估改善:D (63.5) → 預估 B (85+)

## 新增投影片(共 10 張)
| # | 標題 | 對應維度 | 主要內容 |
|---|------|---------|---------|
| 6 | FA 基本資訊 | 基本資訊完整性 | FA-260811-001, 客戶 Kobo, ... |
| 7 | 5-Why 根因推導 | 根因分析 | Why 1-5 流程圖 |

## 母片保護
- ✓ Master XML unchanged
- ✓ No new layouts added
- ✓ All original slides preserved
```

---

## 十、使用者介面考量

### CLI 模式(簡單)
```bash
python fa_agent.py improve /path/to/report.pptx \
  --goal "改善這份 ESD 失效報告" \
  --max-iterations 15 \
  --llm-provider openai
```

### 互動模式(進階,像 Claude Code)
```bash
python fa_agent.py interactive
> Agent: 我已分析完報告,預計新增 10 張投影片,包含 ESD 專屬建議。
> User: 把 5-Why 那張改用更詳細的流程圖
> Agent: 已重新生成,你看一下預覽 (slide-7.pdf)
> User: 繼續
> Agent: ✓ 全部完成。輸出:improved.pptx,變更說明:CHANGES.md
```

---

**整合進度**:本文件擴充了 VISION.md 的「LLM 深度整合」章節,把 LLM 從「被動工具」升級為「主動決策者」。實作上,Phase 3A(基礎 Agent)建議在 v3.0 同步完成,Phase 3B/C 可作為後續迭代。

---

**下一步**:把這個 Agent 設計寫進 `02_refactor_plan.md` 作為 v3.0 的 Phase 3 子項目,並開始實作核心工具集。