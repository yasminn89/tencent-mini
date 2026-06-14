# RepoMind PE 方案文档

> 项目：腾讯 Mini Project 2 — RepoMind 代码语义检索
> 目标：通过 Prompt Engineering 优化 LLM 在代码语义检索任务上的准确率
> 模型：DeepSeek Chat (deepseek-chat)
> 评测集：147 条（人工精选 50 条 + ast 自动解析 97 条）

---

## 一、最优方案速览

**推荐配置：System Prompt + CoT 推理链**

- 综合得分：**80.3%**（vs 基线 68.7%，绝对提升 +11.6 个百分点）
- 单维度最大提升：CoT（+6.2%）
- 最大瓶颈突破：冷门函数定位 +14.4%

> ⚠️ 注意：Few-shot 在我们的实验中出现**负迁移**，最优方案中**不包含 Few-shot**。详见报告第三节。

---

## 二、可直接复用的 Prompt 模板

### 2.1 System Prompt

### 2.2 CoT 推理引导（附加到 System Prompt 末尾）

### 2.3 调用示例（Python）

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_API_KEY",
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = '''<上方 2.1 完整内容>'''
COT_INSTRUCTION = '''<上方 2.2 完整内容>'''

def query_requests_source(user_query: str) -> str:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + COT_INSTRUCTION},
            {"role": "user", "content": user_query}
        ],
        max_tokens=1024,
        temperature=0.1
    )
    return response.choices[0].message.content

# 使用示例
answer = query_requests_source("如何在 requests 中设置请求超时？")
print(answer)
```

---

## 三、Few-shot 示例库（备用，注意负迁移风险）

虽然 Few-shot 在我们的全量评测中表现为负迁移，但在某些**特定子场景**（如 D_edge 边界查询）有明显提升。如需使用，建议**按查询类型动态选择示例**而非固定3条。

### 3.1 Few-shot 示例库（20 条，按类别组织）


#### A 简单查询

**示例 1**
```
查询：requests库里发送GET请求的核心函数在哪里？
回答：在 requests/api.py 中的 get() 函数。它是对 request() 函数的简单封装，内部调用 request('GET', url, **kwargs)。
```

**示例 2**
```
查询：请求响应的状态码在哪个类里存储？
回答：在 requests/models.py 的 Response 类中。Response 对象通过 self.status_code 属性存储 HTTP 状态码。
```

**示例 3**
```
查询：HTTP Basic Auth 认证是怎么实现的？
回答：在 requests/auth.py 中的 HTTPBasicAuth 类实现。它通过 __call__ 方法在请求 headers 中添加 Authorization: Basic <base64编码> 头。
```

**示例 4**
```
查询：Cookie 是如何被处理和存储的？
回答：在 requests/cookies.py 的 RequestsCookieJar 类中。它继承自 MutableMapping 和 CookieJar，提供字典式接口操作 Cookie。
```


#### B 跨文件依赖

**示例 1**
```
查询：调用 requests.get() 时底层的完整调用链是什么？
回答：完整调用链：requests/api.py 的 get() → requests/sessions.py 的 Session.request() → Session.send() → requests/adapters.py 的 HTTPAdapter.send() → urllib3.PoolManager.urlopen()。api.py 入口创建临时 Session，再由 Adapter 调用底层 urllib3。
```

**示例 2**
```
查询：Session 如何在多次请求之间保持 Cookie？
回答：涉及 requests/sessions.py 和 requests/cookies.py。Session.cookies 是 RequestsCookieJar 实例，每次请求通过 merge_cookies() 合并 session 级和 request 级 cookie，响应后通过 extract_cookies_to_jar() 回写。
```

**示例 3**
```
查询：重定向是怎么被处理的？
回答：在 requests/sessions.py 的 Session.resolve_redirects() 中。这是一个生成器函数，检测 301/302/303/307/308 状态码，从 Location 头取新 URL，循环发起请求并追加到 response.history。
```

**示例 4**
```
查询：HTTPAdapter 怎么和 urllib3 交互发送实际请求？
回答：在 requests/adapters.py 的 HTTPAdapter.send() 中。它通过 self.poolmanager（urllib3 的 PoolManager）调用 urlopen() 发送 HTTP 请求，再把 urllib3.HTTPResponse 转换为 requests.Response 对象。
```


#### C 模糊语义

**示例 1**
```
查询：我想让 requests 记住我登录的状态？
回答：用 requests/sessions.py 的 Session 类。Session 会自动维护 cookies 和 headers，在多次请求之间保持登录态。
```

**示例 2**
```
查询：网络请求卡住了怎么让它自动停止？
回答：在请求时设置 timeout 参数，比如 requests.get(url, timeout=5)。requests/sessions.py 的 Session.request() 接收 timeout，最终在 requests/adapters.py 的 HTTPAdapter.send() 中传给 urllib3，超时会抛出 Timeout 异常。
```

**示例 3**
```
查询：怎么让请求失败时自动重试？
回答：用法：session.mount('http://', HTTPAdapter(max_retries=3))。requests/adapters.py 的 HTTPAdapter 构造函数接收 max_retries 参数，内部由 urllib3 的 Retry 机制实现。
```

**示例 4**
```
查询：怎么忽略 HTTPS 证书错误？
回答：传入 verify=False，如 requests.get(url, verify=False)。在 requests/adapters.py 的 HTTPAdapter.send() 中处理 verify 参数，传给 urllib3，同时触发 InsecureRequestWarning 警告。
```


#### D 边界/不支持

**示例 1**
```
查询：requests 支持 HTTP/2 吗？
回答：requests 不支持 HTTP/2。它底层使用 urllib3，仅支持 HTTP/1.1。如需 HTTP/2 请用 httpx 库。
```

**示例 2**
```
查询：requests 能做异步请求吗？
回答：requests 不支持原生异步，它是同步阻塞库。异步场景请用 httpx 或 aiohttp。
```

**示例 3**
```
查询：requests.get() 和 Session.get() 有什么区别？
回答：requests/api.py 的 get() 每次都创建临时 Session，不保留 cookies 和连接；而 requests/sessions.py 的 Session.get() 复用同一 Session，保持连接池和 cookies，适合多次请求同一服务的场景。
```


#### 冷门函数（utils/exceptions/structures）

**示例 1**
```
查询：如何判断一个字符串是不是合法的 IPv4 地址？
回答：用 requests/utils.py 的 is_ipv4_address(string_ip) 函数。这是 requests 内部的工具函数，判断字符串是否为合法 IPv4。
```

**示例 2**
```
查询：怎么从 HTTP 响应头里提取出字符编码信息？
回答：用 requests/utils.py 的 get_encoding_from_headers(headers) 函数。它从 Content-Type 头部解析 charset 参数，失败返回默认编码。
```

**示例 3**
```
查询：我在 requests 库里遇到连接失败，怎么捕获这种异常？
回答：捕获 requests/exceptions.py 的 ConnectionError 异常。它继承自 RequestException，所有连接层面的错误都会抛出此异常。
```

**示例 4**
```
查询：怎么把字典格式的 cookie 数据添加到 CookieJar 对象里？
回答：用 requests/cookies.py 的 add_dict_to_cookiejar(cj, cookie_dict) 函数。它将字典中的键值对作为 cookie 添加到现有 CookieJar。
```

**示例 5**
```
查询：如何创建一个不区分大小写的字典来存储 HTTP 请求头？
回答：用 requests/structures.py 的 CaseInsensitiveDict 类。它是一个特殊字典，键的大小写不影响访问，专门用于 HTTP 头部存储。
```


---

## 四、输出后处理规则

后处理流水线作用于模型输出，用于结构化提取关键信息。**对评分不直接加分，但显著提升输出可读性和下游可用性**。

### 4.1 处理步骤

1. **剥离 `<thinking>...</thinking>` 思考块**
2. **提取并标准化文件路径**（统一为 `requests/xxx.py` 格式）
3. **提取函数/类名**（启发式正则匹配，过滤常见停用词）
4. **检测"不支持"类回答**（关键词：不支持/无法/doesn't support 等）
5. **清理 Markdown 噪声**（代码块、空 bullet、多余空行）

### 4.2 后处理函数实现

```python
import re

def post_process(raw_response: str) -> dict:
    cleaned = raw_response
    had_thinking = "<thinking>" in cleaned
    
    # 1. 剥离思考过程
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()
    
    # 2. 提取文件路径并标准化
    file_matches = re.findall(r'(?:requests/)?(\w+)\.py', cleaned)
    normalized_files = list(dict.fromkeys(
        [f"requests/{f}.py" for f in file_matches]
    ))
    
    # 3. 提取函数/类名
    func_pattern = r'\b([A-Z]\w+|[a-z]\w*(?=\(\)))'
    func_matches = re.findall(func_pattern, cleaned)
    stopwords = {"HTTP","URL","API","Python","GET","POST","PUT","DELETE",
                 "OPTIONS","PATCH","HEAD","JSON","SSL","TLS"}
    extracted_funcs = list(dict.fromkeys(
        [f for f in func_matches if f not in stopwords and len(f) >= 3]
    ))[:5]
    
    # 4. 不支持类检测
    not_support = bool(re.search(
        r"(requests\s*(?:库)?(?:本身)?不支持|无法\s*(?:直接|原生)|"
        r"doesn't\s+support|does\s+not\s+support)",
        cleaned, re.IGNORECASE))
    
    # 5. 清理 Markdown
    cleaned = re.sub(r'```python.*?```', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return {
        "cleaned_text": cleaned,
        "files": normalized_files,
        "functions": extracted_funcs,
        "is_not_supported": not_support,
        "had_thinking": had_thinking
    }
```

---

## 五、迁移到其他代码库的指南

如需把本方案应用到其他开源库（如 Flask、FastAPI），只需修改 System Prompt 中的三处：

1. **库名描述**：把"requests"替换为目标库
2. **核心文件列表**：列出目标库的主要模块及职责
3. **架构层次**：描述目标库的调用层次

CoT 思考链和后处理规则**可直接复用**，无需修改。

---

*文档版本：v1.0 | 实验日期：2025-06 | 评测集：147 条*
