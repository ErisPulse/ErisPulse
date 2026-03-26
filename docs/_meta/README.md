# ErisPulse 文档索引使用指南

本目录包含 ErisPulse 文档的自动生成索引文件，用于第三方文档网站的文档集成。

## 索引文件结构

```
docs/_meta/
├── docs-mapping.json           # 语言索引（主索引）
├── en/
│   ├── docs-mapping.json       # 英文文档映射
│   └── docs-search-index.json  # 英文搜索索引
├── zh-CN/
│   ├── docs-mapping.json       # 简体中文文档映射
│   └── docs-search-index.json  # 简体中文搜索索引
└── zh-TW/
    ├── docs-mapping.json       # 繁体中文文档映射
    └── docs-search-index.json  # 繁体中文搜索索引
```

## 主索引：docs-mapping.json

语言索引，包含所有可用语言及其文档映射索引的路径。

**结构示例：**
```json
{
  "version": "1.0",
  "total_languages": 3,
  "languages": {
    "en": {
      "docs_count": 46,
      "mapping_path": "_meta/en/docs-mapping.json"
    },
    "zh-CN": {
      "docs_count": 46,
      "mapping_path": "_meta/zh-CN/docs-mapping.json"
    },
    "zh-TW": {
      "docs_count": 46,
      "mapping_path": "_meta/zh-TW/docs-mapping.json"
    }
  }
}
```

**字段说明：**
- `version`: 索引版本号
- `total_languages`: 语言总数
- `languages`: 语言字典
  - `docs_count`: 该语言的文档数量
  - `mapping_path`: 该语言的文档映射索引路径（相对于 `docs/` 目录）

## 语言特定索引

每个语言目录下包含两个索引文件：
- `docs-mapping.json`: 文档映射索引
- `docs-search-index.json`: 文档搜索索引

### docs-mapping.json（语言特定）

文档映射索引，按分类组织该语言的所有文档。

**结构示例：**
```json
{
  "version": "1.0",
  "total_categories": 10,
  "categories": {
    "快速开始": {
      "description": "ErisPulse 快速入门指南",
      "count": 4,
      "documents": [
        {
          "title": "ErisPulse 文档",
          "path": "README.md",
          "level": 1
        },
        {
          "title": "快速开始",
          "path": "quick-start.md",
          "level": 1
        }
      ]
    },
    "入门指南": {
      "description": "ErisPulse 基础概念和使用教程",
      "count": 5,
      "documents": [...]
    }
  }
}
```

**字段说明：**
- `version`: 索引版本号
- `total_categories`: 分类总数
- `categories`: 分类字典
  - `description`: 分类描述
  - `count`: 该分类下的文档数量
  - `documents`: 文档列表
    - `title`: 文档标题（第一个一级标题）
    - `path`: 文档相对路径（相对于语言目录，统一使用 `/` 作为分隔符）
    - `level`: 文档等级（预留字段）

### docs-search-index.json（语言特定）

文档搜索索引，包含该语言所有标题关键词及其在文档中的位置。

**结构示例：**
```json
{
  "version": "1.0",
  "total_keywords": 1000,
  "keywords": {
    "快速开始": [
      {
        "document": "quick-start.md",
        "line": 1,
        "level": 1,
        "title": "快速开始"
      }
    ],
    "安装 ErisPulse": [
      {
        "document": "quick-start.md",
        "line": 3,
        "level": 2,
        "title": "安装 ErisPulse"
      }
    ]
  }
}
```

**字段说明：**
- `version`: 索引版本号
- `total_keywords`: 关键词总数
- `keywords`: 关键词字典，键为标题文本
  - `document`: 文档路径（相对于语言目录）
  - `line`: 标题所在行号（从 1 开始）
  - `level`: 标题级别（1-6）
  - `title`: 标题文本

## 使用指南

### 1. 获取可用语言

首先获取语言索引，了解所有可用的语言：

```python
import json
import requests

# 获取语言索引
response = requests.get("https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/_meta/docs-mapping.json")
language_index = response.json()

# 打印所有可用语言
for lang_code, lang_info in language_index["languages"].items():
    print(f"{lang_code}: {lang_info['docs_count']} 个文档")
```

```javascript
// 获取语言索引
fetch('https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/_meta/docs-mapping.json')
    .then(response => response.json())
    .then(languageIndex => {
        // 打印所有可用语言
        for (const [langCode, langInfo] of Object.entries(languageIndex.languages)) {
            console.log(`${langCode}: ${langInfo.docs_count} 个文档`);
        }
    });
```

### 2. 获取特定语言的文档映射

选择语言后，获取该语言的文档映射索引：

```python
def get_language_mapping(lang_code):
    """
    获取指定语言的文档映射
    
    :param lang_code: 语言代码（如: zh-CN, en, zh-TW）
    :return: 语言映射数据
    """
    # 首先获取语言索引
    response = requests.get("https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/_meta/docs-mapping.json")
    language_index = response.json()
    
    # 检查语言是否存在
    if lang_code not in language_index["languages"]:
        raise ValueError(f"不支持的语言: {lang_code}")
    
    # 获取语言映射
    mapping_path = language_index["languages"][lang_code]["mapping_path"]
    full_url = f"https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/{mapping_path}"
    
    response = requests.get(full_url)
    return response.json()

# 使用示例
zh_mapping = get_language_mapping("zh-CN")
print(f"简体中文文档共 {zh_mapping['total_categories']} 个分类")
```

```javascript
// 获取特定语言的文档映射
async function getLanguageMapping(langCode) {
    // 首先获取语言索引
    const languageIndex = await fetch('https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/_meta/docs-mapping.json')
        .then(response => response.json());
    
    // 检查语言是否存在
    if (!languageIndex.languages[langCode]) {
        throw new Error(`不支持的语言: ${langCode}`);
    }
    
    // 获取语言映射
    const mappingPath = languageIndex.languages[langCode].mapping_path;
    const fullUrl = `https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/${mappingPath}`;
    
    return await fetch(fullUrl).then(response => response.json());
}

// 使用示例
getLanguageMapping('zh-CN').then(mapping => {
    console.log(`简体中文文档共 ${mapping.total_categories} 个分类`);
});
```

### 3. 构建文档导航和路径

构建完整的文档路径（语言目录 + 文档路径）：

```python
def build_document_nav(lang_code):
    """
    构建文档导航
    
    :param lang_code: 语言代码
    :return: 导航结构
    """
    mapping = get_language_mapping(lang_code)
    nav = []
    
    for category_name, category_data in mapping["categories"].items():
        category_item = {
            "title": category_name,
            "description": category_data["description"],
            "items": []
        }
        
        for doc in category_data["documents"]:
            # 构建完整路径: docs/{lang}/{doc_path}
            full_path = f"docs/{lang_code}/{doc['path']}"
            category_item["items"].append({
                "title": doc["title"],
                "path": full_path
            })
        
        nav.append(category_item)
    
    return nav

# 使用示例
zh_nav = build_document_nav("zh-CN")
for category in zh_nav:
    print(f"\n{category['title']}:")
    for item in category["items"]:
        print(f"  - {item['title']}: {item['path']}")
```

```javascript
// 构建文档导航
async function buildDocumentNav(langCode) {
    const mapping = await getLanguageMapping(langCode);
    const nav = [];
    
    for (const [categoryName, categoryData] of Object.entries(mapping.categories)) {
        const categoryItem = {
            title: categoryName,
            description: categoryData.description,
            items: []
        };
        
        for (const doc of categoryData.documents) {
            // 构建完整路径: docs/{lang}/{doc_path}
            const fullPath = `docs/${langCode}/${doc.path}`;
            categoryItem.items.push({
                title: doc.title,
                path: fullPath
            });
        }
        
        nav.push(categoryItem);
    }
    
    return nav;
}

// 使用示例
buildDocumentNav('zh-CN').then(nav => {
    nav.forEach(category => {
        console.log(`\n${category.title}:`);
        category.items.forEach(item => {
            console.log(`  - ${item.title}: ${item.path}`);
        });
    });
});
```

### 4. 文档分类和导航（完整示例）

```python
def build_sidebar(lang_code):
    """
    构建侧边栏导航
    
    :param lang_code: 语言代码
    :return: 侧边栏数据
    """
    mapping = get_language_mapping(lang_code)
    sidebar = []
    
    for category_name, category_data in mapping["categories"].items():
        category_item = {
            "title": category_name,
            "description": category_data["description"],
            "items": []
        }
        
        for doc in category_data["documents"]:
            # 完整路径: /docs/{lang}/{doc_path}
            full_path = f"/docs/{lang_code}/{doc['path']}"
            category_item["items"].append({
                "title": doc["title"],
                "path": full_path
            })
        
        sidebar.append(category_item)
    
    return sidebar

# 使用示例
sidebar = build_sidebar("zh-CN")
```

### 2. 文档内容跳转（锚点导航）

使用 `docs-search-index.json` 实现文档内标题的锚点导航。

#### 实现步骤

1. **读取文档内容**
   ```python
   def read_document(path):
       with open(path, 'r', encoding='utf-8') as f:
           return f.readlines()
   ```

2. **定位标题行号**
   ```python
   def find_heading_position(document_path, heading_text):
       # 使用搜索索引查找标题
       results = search_index["keywords"].get(heading_text, [])
       
       for result in results:
           if result["document"] == document_path:
               return result["line"], result["level"]
       
       return None, None
   ```

3. **生成锚点链接**
   ```python
   def generate_anchor_id(heading_text):
       # 将标题转换为 URL 友好的锚点 ID
       import re
       return re.sub(r'[^\w\s-]', '', heading_text.lower()).strip().replace(' ', '-')
   
   # 示例：生成锚点链接
   anchor_id = generate_anchor_id("安装 ErisPulse")
   # 输出: "安装-erispulse" 或 "安装-erispulse"
   ```

4. **渲染文档目录**
   ```python
   def render_toc(document_path):
       # 获取文档的所有标题
       headings = []
       for keyword, results in search_index["keywords"].items():
           for result in results:
               if result["document"] == document_path:
                   headings.append({
                       "text": result["title"],
                       "line": result["line"],
                       "level": result["level"],
                       "anchor": generate_anchor_id(result["title"])
                   })
       
       # 按行号排序
       headings.sort(key=lambda x: x["line"])
       
       return headings
   ```

#### JavaScript 示例

```javascript
// 生成锚点 ID
function generateAnchorId(text) {
    return text
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .trim()
        .replace(/\s+/g, '-');
}

// 渲染文档目录
function renderTableOfContents(documentPath) {
    const headings = [];
    
    for (const [keyword, results] of Object.entries(searchIndex.keywords)) {
        for (const result of results) {
            if (result.document === documentPath) {
                headings.push({
                    text: result.title,
                    line: result.line,
                    level: result.level,
                    anchor: generateAnchorId(result.title)
                });
            }
        }
    }
    
    // 按行号排序
    headings.sort((a, b) => a.line - b.line);
    
    return headings;
}

// 生成目录 HTML
function generateTocHtml(headings) {
    let html = '<ul class="toc">';
    
    headings.forEach(heading => {
        const padding = (heading.level - 1) * 20;
        html += `<li style="padding-left: ${padding}px;">`;
        html += `<a href="#${heading.anchor}">${heading.text}</a>`;
        html += '</li>';
    });
    
    html += '</ul>';
    return html;
}
```

### 3. 全文搜索功能

使用 `docs-search-index.json` 实现文档站点的全文搜索。

#### Python 示例

```python
def search_documents(query, limit=10):
    """
    搜索文档
    
    :param query: 搜索关键词
    :param limit: 返回结果数量限制
    :return: 搜索结果列表
    """
    results = []
    query = query.lower()
    
    for keyword, occurrences in search_index["keywords"].items():
        if query in keyword.lower():
            for occurrence in occurrences:
                results.append({
                    "document": occurrence["document"],
                    "title": occurrence["title"],
                    "line": occurrence["line"],
                    "level": occurrence["level"],
                    "snippet": keyword  # 可以扩展为获取上下文
                })
    
    # 按相关性排序（这里简化为按标题匹配度）
    results.sort(key=lambda x: (
        query in x["title"].lower(),
        len(x["title"])
    ), reverse=True)
    
    return results[:limit]

# 使用示例
results = search_documents("事件系统")
for result in results:
    print(f"{result['title']} - {result['document']} (行 {result['line']})")
```

#### JavaScript 示例

```javascript
// 搜索文档
function searchDocuments(query, limit = 10) {
    const results = [];
    const lowerQuery = query.toLowerCase();
    
    for (const [keyword, occurrences] of Object.entries(searchIndex.keywords)) {
        if (lowerQuery in keyword.toLowerCase()) {
            for (const occurrence of occurrences) {
                results.push({
                    document: occurrence.document,
                    title: occurrence.title,
                    line: occurrence.line,
                    level: occurrence.level,
                    relevance: calculateRelevance(lowerQuery, keyword)
                });
            }
        }
    }
    
    // 按相关性排序
    results.sort((a, b) => b.relevance - a.relevance);
    
    return results.slice(0, limit);
}

// 计算相关性（简单实现）
function calculateRelevance(query, keyword) {
    const lowerKeyword = keyword.toLowerCase();
    
    // 精确匹配得分最高
    if (lowerKeyword === query) {
        return 100;
    }
    
    // 开头匹配得分较高
    if (lowerKeyword.startsWith(query)) {
        return 80;
    }
    
    // 包含匹配
    if (lowerKeyword.includes(query)) {
        return 60;
    }
    
    return 0;
}

// 搜索 UI 集成
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    
    searchInput.addEventListener('input', debounce(async (e) => {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            searchResults.innerHTML = '';
            return;
        }
        
        const results = searchDocuments(query);
        displaySearchResults(results);
    }, 300));
}

function displaySearchResults(results) {
    const html = results.map(result => `
        <div class="search-result">
            <a href="/docs/${result.document}#L${result.line}">
                <h3>${result.title}</h3>
                <p>${result.document} - 第 ${result.line} 行</p>
            </a>
        </div>
    `).join('');
    
    document.getElementById('search-results').innerHTML = html;
}
```

## 路径说明

### 语言特定索引中的路径

在语言特定的 `docs-mapping.json` 和 `docs-search-index.json` 中，所有文档路径都**相对于语言目录**，并使用 `/` 作为分隔符：

- 索引中的路径：`getting-started/README.md`
- 实际完整路径：`docs/zh-CN/getting-started/README.md`

### 构建完整文档路径

在第三方文档网站中使用时，需要将语言代码和文档路径组合：

```python
def get_full_document_path(lang_code, doc_path):
    """
    构建完整的文档路径
    
    :param lang_code: 语言代码（如: zh-CN, en, zh-TW）
    :param doc_path: 索引中的文档路径（相对于语言目录）
    :return: 完整的文档路径
    """
    return f"docs/{lang_code}/{doc_path}"

# 示例
full_path = get_full_document_path("zh-CN", "getting-started/README.md")
# 输出: docs/zh-CN/getting-started/README.md
```

```javascript
// 构建完整的文档路径
function getFullDocumentPath(langCode, docPath) {
    return `docs/${langCode}/${docPath}`;
}

// 示例
const fullPath = getFullDocumentPath('zh-CN', 'getting-started/README.md');
// 输出: docs/zh-CN/getting-started/README.md
```

### URL 路径构建

对于 Web URL，需要根据文档网站的基础路径进行调整：

```javascript
// 如果文档托管在 https://example.com/docs/
const docsBaseUrl = 'https://example.com/docs/';
const langCode = 'zh-CN';
const docPath = 'getting-started/README.md';

// 完整 URL
const fullUrl = `${docsBaseUrl}${langCode}/${docPath}`;
// 输出: https://example.com/docs/zh-CN/getting-started/README.md

// 或者使用相对路径
const relativePath = `/docs/${langCode}/${docPath}`;
// 输出: /docs/zh-CN/getting-started/README.md
```

### 从 GitHub 获取文档内容

```python
import requests

def get_document_content(lang_code, doc_path):
    """
    从 GitHub 获取文档内容
    
    :param lang_code: 语言代码
    :param doc_path: 文档路径（相对于语言目录）
    :return: 文档内容
    """
    full_path = f"docs/{lang_code}/{doc_path}"
    url = f"https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/{full_path}"
    response = requests.get(url)
    return response.text

# 使用示例
content = get_document_content("zh-CN", "getting-started/README.md")
```

```javascript
// 从 GitHub 获取文档内容
async function getDocumentContent(langCode, docPath) {
    const fullPath = `docs/${langCode}/${docPath}`;
    const url = `https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/${fullPath}`;
    const response = await fetch(url);
    return await response.text();
}

// 使用示例
getDocumentContent('zh-CN', 'getting-started/README.md').then(content => {
    console.log(content);
});
```

## 分类映射

文档按以下分类组织：

| 目录名 | 分类名 | 描述 |
|--------|--------|------|
| (根目录) | 快速开始 | ErisPulse 快速入门指南 |
| getting-started/ | 入门指南 | ErisPulse 基础概念和使用教程 |
| user-guide/ | 用户使用指南 | ErisPulse 配置和命令参考 |
| developer-guide/ | 开发者指南 | 模块和适配器开发指南 |
| platform-guide/ | 平台特性指南 | 各平台特性和适配器说明 |
| api-reference/ | API 参考 | 核心 API 和接口文档 |
| advanced/ | 高级主题 | 深入理解框架的高级特性 |
| ai-support/ | AI 辅助开发 | 使用 AI 辅助开发 ErisPulse |
| standards/ | 技术标准 | 框架的技术规范和标准 |
| styleguide/ | 风格指南 | 代码和文档风格规范 |

## 忽略的目录

以下目录在生成索引时被忽略：

- `_meta/` - 索引文件目录
- `ai-support/prompts/` - AI 提示词目录（合并文档）

## 自动更新

索引文件会在以下情况自动更新：

1. 文档内容发生变化时，通过 GitHub Actions 自动重新生成
2. 手动运行 `python scripts/tools/generate-docs-index.py`

**注意：** 不要手动编辑索引文件，所有更改会在下次自动生成时被覆盖。

## API 版本

当前索引版本：`v1.0`

版本变更说明：
- `1.0`: 初始版本，支持基本映射和搜索索引

## 常见问题

### Q: 如何获取文档的实际内容？

A: 使用文档路径从 GitHub 仓库或其他文档源获取原始 Markdown 文件：

```python
import requests

def get_document_content(path):
    url = f"https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/{path}"
    response = requests.get(url)
    return response.text
```

### Q: 如何处理文档中的图片和资源链接？

A: 文档中的相对路径应该相对于文档所在目录解析。建议使用完整的绝对路径：

```javascript
// 文档路径: getting-started/first-bot.md
// 图片链接: images/screenshot.png
// 完整路径: getting-started/images/screenshot.png
```

### Q: 如何实现文档的高亮跳转？

A: 结合行号和标题锚点：

```javascript
// 跳转到特定行
function jumpToLine(documentPath, lineNumber) {
    // 1. 获取文档内容
    const content = getDocumentContent(documentPath);
    
    // 2. 提取目标行周围的上下文
    const lines = content.split('\n');
    const contextLines = lines.slice(lineNumber - 5, lineNumber + 5);
    
    // 3. 高亮目标行
    const highlighted = contextLines.map((line, index) => {
        if (index === 4) { // 第 5 行是目标行
            return `<mark>${line}</mark>`;
        }
        return line;
    }).join('\n');
    
    // 4. 渲染内容
    return highlighted;
}
```

## 技术支持

如有问题或建议，请提交 Issue 到 [ErisPulse 仓库](https://github.com/ErisPulse/ErisPulse/issues)。