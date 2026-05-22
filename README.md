# pos-to-markdown

将 ProcessOn (`.pos`) 文件转换为包含 Mermaid 流程图的 Markdown 文件。

## 快速开始

**Windows:**
```
setup.cmd
run.cmd
```

**Linux/macOS:**
```
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

`setup` 创建 `.venv` 虚拟环境，`run` 激活环境并执行转换。

## 使用方式

1. 将 `.pos` 文件放入 [`input/`](input/) 目录
2. 运行 `run.cmd`（Windows）或 `./run.sh`（Linux/macOS）
3. 生成的 `.md` 文件在 [`output/`](output/) 目录

## 转换说明

### 支持的 ProcessOn 元素

| ProcessOn 元素 | Mermaid 语法 | 说明 |
|---|---|---|
| `start` | `([text])` | 圆角矩形（开始/结束） |
| `rectangle` | `[text]` | 矩形（处理步骤） |
| `diamond` | `{text}` | 菱形（判断分支） |
| `note` | `[text]` | 备注 |
| `linker` | `-->|label|` | 带标签的连线 |

### 泳道/泳池

- `verticalPool` → Mermaid `subgraph`（外层容器）
- `verticalLane` → 嵌套 `subgraph`（泳道），节点按 x 坐标自动分配到所属泳道

### 生成的 Markdown 内容

- 标题及统计摘要
- Mermaid 流程图（按泳池/泳道分组）
- 步骤列表表格（包含序号、名称、类型）

## 项目结构

```
pos-to-markdown/
├── main.py           # 入口，遍历 input/ 目录
├── pos_parser.py     # .pos JSON 解析，构建中间图结构
├── mermaid_gen.py    # 将图转换为 Mermaid 语法
├── md_writer.py      # 生成 Markdown 文件（含表格）
├── input/            # 存放 .pos 文件
├── output/           # 输出 .md 文件
├── setup.cmd/.sh     # 创建虚拟环境
├── run.cmd/.sh       # 运行转换
└── README.md
```

## 依赖

仅使用 Python 标准库，无需安装第三方包。

## License

Apache 2.0