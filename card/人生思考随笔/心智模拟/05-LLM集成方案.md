# LLM集成方案：驱动心智模拟的核心引擎

## LLM的角色定位

### 1. 知识处理器
- 提取和结构化"信念"
- 验证信念的一致性
- 更新知识库

### 2. 推理引擎
- 从信念+欲望构建意图
- 评估可行性
- 生成执行计划

### 3. 对话管理器
- 区分设计者/执行者模式
- 引导密封流程
- 管理检查点对话

### 4. 后台处理器
- 异步问题分析
- 创意孵化
- 模式识别

## 技术架构

### 模型选择

#### 主模型(推理和对话)
- **推荐**: GPT-4, Claude 3, 或类似级别
- **原因**: 需要强大的推理能力和上下文理解
- **用途**: 意图构建、冲突检测、对话管理

#### 辅助模型(知识提取)
- **推荐**: GPT-3.5, 或更轻量级模型
- **原因**: 任务相对简单,成本优化
- **用途**: 信念提取、分类、简单查询

### Prompt工程策略

#### 1. 系统Prompt模板

**设计者模式**:
```
你是一个理性的规划助手,帮助用户制定清晰的目标和计划。

你的职责:
- 提出问题,帮助用户澄清目标
- 提供多个选项供用户选择
- 指出潜在的风险和冲突
- 鼓励用户深入思考

你的风格:
- 使用疑问句和建议句
- 提供分析和权衡
- 不催促用户做决定

当前模式: 设计者
```

**执行者模式**:
```
你是一个行动导向的执行助手,帮助用户完成既定计划。

你的职责:
- 提醒用户执行任务
- 只关注"如何做",不质疑"为什么"
- 记录执行结果
- 在遇到障碍时提供简单的应对方案

你的风格:
- 使用祈使句和肯定句
- 简洁直接,不提供过多选择
- 鼓励立即行动

当前模式: 执行者
重要: 用户的计划已经密封,你不能建议修改目标或规则
```

#### 2. 任务特定Prompt

**信念提取**:
```
从以下文本中提取可作为"信念"的陈述:

文本: {user_input}

要求:
1. 只提取事实性、可验证的陈述
2. 为每个信念评估置信度(0-1)
3. 标注来源类型(科学研究/个人经验/常识)
4. 用JSON格式输出

输出格式:
{
  "beliefs": [
    {
      "content": "...",
      "confidence": 0.8,
      "source_type": "科学研究",
      "category": "时间管理"
    }
  ]
}
```

**意图构建**:
```
基于以下信息构建可执行的意图:

欲望: {desire}
相关信念: {beliefs}

步骤:
1. 评估可行性(0-1分)
2. 如果可行性>0.7,生成详细的执行计划
3. 将计划分解为具体步骤
4. 为每个步骤标注执行模式(设计者/执行者)
5. 设定合理的检查点

输出JSON格式的意图对象。
```

**冲突检测**:
```
检查新项目是否与现有系统冲突:

新项目: {new_item}
现有信念: {existing_beliefs}
现有欲望: {existing_desires}

分析:
1. 逻辑冲突(互相矛盾)
2. 资源冲突(时间/精力)
3. 优先级冲突

输出:
- 冲突列表
- 严重程度(低/中/高)
- 解决建议
```

### 上下文管理

#### 短期上下文(对话级别)
- 当前对话的历史
- 用户的即时意图
- 临时的思考过程

#### 中期上下文(会话级别)
- 当前正在设计/执行的指令
- 最近的检查点结果
- 活跃的后台任务

#### 长期上下文(用户级别)
- 用户的信念库
- 用户的欲望库
- 历史指令和评估结果

#### 实现策略
```python
def build_context(user_id, conversation_id):
    context = {
        "system_prompt": get_mode_prompt(current_mode),
        "user_profile": {
            "beliefs": get_top_beliefs(user_id, limit=20),
            "desires": get_active_desires(user_id),
            "personality": get_user_preferences(user_id)
        },
        "current_session": {
            "active_instruction": get_active_instruction(user_id),
            "conversation_history": get_recent_messages(conversation_id, limit=10)
        },
        "background_tasks": get_pending_tasks(user_id)
    }
    return context
```

## API设计

### 核心端点

```python
# 对话接口
POST /api/chat
{
  "user_id": "uuid",
  "message": "我想建立运动习惯",
  "mode": "designer"  # or "executor"
}

# 信念管理
POST /api/beliefs/extract
GET /api/beliefs/list
PUT /api/beliefs/{id}

# 意图构建
POST /api/intentions/build
GET /api/intentions/{id}/status

# 后台任务
POST /api/background/create
GET /api/background/{id}/result
```

### 流式响应

对于长文本生成,使用SSE(Server-Sent Events):
```python
@app.route('/api/chat/stream')
def chat_stream():
    def generate():
        for chunk in llm.stream(prompt):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    return Response(generate(), mimetype='text/event-stream')
```

## 成本优化

### 1. 智能路由
- 简单任务 → 轻量级模型
- 复杂推理 → 高级模型

### 2. 缓存策略
- 缓存常见的信念提取结果
- 缓存用户的个性化Prompt

### 3. 批处理
- 后台任务批量处理
- 非紧急查询延迟执行

## 安全与隐私

### 数据处理
- 敏感信息本地处理
- 最小化发送给LLM的数据
- 用户数据加密存储

### Prompt注入防护
- 验证用户输入
- 使用结构化输出格式
- 限制LLM的权限范围

## 评估与监控

### 质量指标
- 信念提取准确率
- 意图构建合理性
- 用户满意度

### 性能指标
- 响应时间
- Token使用量
- 成本per用户

---

**创建日期**: 2025-11-11
**状态**: 设计中
