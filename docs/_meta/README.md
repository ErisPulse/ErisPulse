# ErisPulse 文档索引使用指南

本目录包含 ErisPulse 文档的自动生成索引文件，用于第三方文档网站的文档集成。

## 索引文件说明

### docs-mapping.json
文档映射索引，按分类组织所有文档，用于生成文档网站的结构和导航。

**结构示例：**
```json
{
  "version": "1.0",
  "generated_at": "2025-02-24T10:00:00Z",
  "total_categories": 10,
  "categories": {
    "快速开始": {
      "description": "ErisPulse 快速入门指南",
      "count": 1,
      "documents": [
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
- `generated_at`: 生成时间（ISO 8601 格式）
- `total_categories`: 分类总数
- `categories`: 分类字典
  - `description`: 分类描述
  - `count`: 该分类下的文档数量
  - `documents`: 文档列表
    - `title`: 文档标题（第一个一级标题）
    - `path`: 文档相对路径（统一使用 `/` 作为分隔符）
    - `level`: 文档等级（预留字段）

### docs-search-index.json
文档搜索索引，包含所有标题关键词及其在文档中的位置。

**结构示例：**
```json
{
  "version": "1.0",
  "generated_at": "2025-02-24T10:00:00Z",
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
- `generated_at`: 生成时间（ISO 8601 格式）
- `total_keywords`: 关键词总数
- `keywords`: 关键词字典，键为标题文本
  - `document`: 文档路径
  - `line`: 标题所在行号（从 1 开始）
  - `level`: 标题级别（1-6）
  - `title`: 标题文本

## 使用指南

### 1. 文档分类和导航

使用 `docs-mapping.json` 构建文档网站的分类结构和导航菜单。

#### Python 示例代码

```python
import json
import requests

# 获取索引
response = requests.get("https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/_meta/docs-mapping.json")
mapping = response.json()

# 构建侧边栏导航
def build_sidebar(mapping):
    sidebar = []
    for category_name, category_data in mapping["categories"].items():
        category_item = {
            "title": category_name,
            "description": category_data["description"],
            "items": []
        }
        
        for doc in category_data["documents"]:
            category_item["items"].append({
                "title": doc["title"],
                "path": f"/docs/{doc['path']}"  # 根据需要调整路径前缀
            })
        
        sidebar.append(category_item)
    
    return sidebar

sidebar = build_sidebar(mapping)
```

#### JavaScript 示例代码

```javascript
// 构建文档分类导航
function buildSidebar(mapping) {
    const sidebar = [];
    
    for (const [categoryName, categoryData] of Object.entries(mapping.categories)) {
        const categoryItem = {
            title: categoryName,
            description: categoryData.description,
            items: []
        };
        
        for (const doc of categoryData.documents) {
            categoryItem.items.push({
                title: doc.title,
                path: `/docs/${doc.path}`
            });
        }
        
        sidebar.push(categoryItem);
    }
    
    return sidebar;
}

// 使用示例
fetch('/docs/_meta/docs-mapping.json')
    .then(response => response.json())
    .then(mapping => {
        const sidebar = buildSidebar(mapping);
        // 渲染侧边栏...
    });
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

所有文档路径都使用 `/` 作为分隔符，确保跨平台兼容性：

- Windows 路径：`getting-started\README.md` → 索引中：`getting-started/README.md`
- Unix/Linux 路径：`getting-started/README.md` → 索引中：`getting-started/README.md`

在构建文档网站时，根据服务器配置添加适当的基础路径前缀：

```javascript
// 如果文档托管在 https://example.com/docs/
const docsBasePath = '/docs/';
const fullDocumentPath = docsBasePath + documentPath;
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