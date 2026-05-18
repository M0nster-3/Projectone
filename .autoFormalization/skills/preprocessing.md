# 数学教材 PDF 预处理 Skill

## 用途

将数学教材 PDF（文本版或扫描版）按语义切分为独立 unit，每个 unit 输出：
- .md 文件：含定理陈述和证明正文
- .json 文件：含结构化元数据（id, type, statement_dependency, proof_dependency 等）

## 关键原则（务必遵守）

### 第一原则：扫描版 PDF 不需要 OCR

本 Skill 明确禁止安装或使用以下工具：
- 禁止 Tesseract / EasyOCR / PaddleOCR
- 禁止 pytesseract / ocrmypdf / pdfplumber 的 OCR 模式

正确做法：用 Claude Code 的 Read 工具直接读取 PDF（自动多模态识别）。

### 第二原则：诊断优先，动手在后

开始任何文件操作前，先诊断：
1. 用 Read 工具读前 3 页，判断 PDF 是否清晰可读
2. PDF 是否加密
3. 总页数和章节范围

把诊断结果告诉用户后，再开始切分。

### 第三原则：诚实标注不确定性

视觉识别遇到模糊、手写、特殊符号时，在 MD 中用 [UNCERTAIN] 标注，不要瞎猜。

### 第四原则：忠实保留原文

提取内容时，必须**逐字逐句**保留原文表述，不得改写、缩写、扩写或调整语序。原文的措辞、符号、编号均须原样保留。即便认为用自己的话“说得更清楚”，也不允许。禁止以自己的知识重组或补充原文内容。原文的章节边界不得擅自合并（例如，不得将 1.1 和 1.2 糊成一个 unit）；原文中未出现的符号不得自行添加（例如原文用粗体 **R**，不得擅自改为 `\mathbb{R}`）。这是形式化项目的输入源，任何偏离原文的表述都会导致后续形式化结果不可靠。

## 标准工作流程

### Phase 1: 直接读取 PDF

用 Read 工具直接读取 `/WillardTopology/<PDF文件名>`(父目录中) 前 3 页：
- 文本清晰可读 → 文本版，继续 Phase 2
- 模糊/乱码/手写 → 扫描版，每页逐一 Read（CC 自动多模态，扫描得到的图片放在/.autoFormalization/tmp/pages目录下），继续 Phase 2

无需安装任何系统包，只依赖 CC 内置的 Read 工具。

### Phase 2: 语义切分

对每一页：
1. 用 Read 工具读取（文本版直接读，扫描版多模态识别）
2. 识别页面上的所有语义单元：
   - Definition X.Y → Def 类型
   - Theorem X.Y → Thm 类型（含 Proof）
   - Lemma X.Y → Lem 类型
   - Example X.Y → Ex 类型
   - Remark → Rem 类型
   - 图表 → Fig 类型
3. 跨页 unit 自动合并：识别编号连续或内容未结束的情况

### Phase 3: 生成 MD + JSON

每个 unit 生成两个文件。

**MD 格式：**

```markdown
# Theorem 4.1 (Tychonoff)

## Statement
<原文定理陈述>

## Proof
<原文证明>
```

**JSON 格式：**

```json
{
  "id": "Thm4_1",
  "chapter": 4,
  "section": 1,
  "type": "Theorem",
  "title": "Tychonoff",
  "page_start": 87,
  "page_end": 88,
  "statement_dependency": ["Def2_3", "Thm3_2"],
  "proof_dependency": ["Lem2_1"]
}
```

字段说明：
- `id`：全局唯一标识，格式为类型缩写（Def/Thm/Lem/Cor/Ex/Rem）+ 章号_节号，如 `Def1_1`、`Thm4_1`
- `section`：小节编号，整数。`chapter` 已含章号，此处不重复（如 Ch4 第 1 节 → `chapter: 4, section: 1`）
- `type`：取值 Definition / Theorem / Proposition / Lemma / Corollary / Example / Remark
- `title`：定理名称，无名称则留空字符串
- `statement_dependency`：接口依赖——只引用了前置命题的陈述（结论）。前置命题 statement_done 即可解锁本条目
- `proof_dependency`：实质依赖——需要前置构造的对象或数据结构（不只是"结论成立"，而是"那个构造本身"）。前置命题必须 done 才能开始本条目的证明

## 文件命名规则

- Def<章号>_<节号>.md，如 Def1_5.md
- Thm<章号>_<节号>.md，如 Thm1_12.md
- Lem<章号>_<节号>[a-z].md，如 Lem1_16a.md（同节多个引理用字母区分）
- Ex<章号>_<节号>.md，如 Ex1_3.md
- Rem<章号>_<节号>.md，如 Rem1_1.md
- Fig<章号>_<节号>.md，如 Fig1_1.md

## 文件输出地址

所有产出文件（`.md` 和 `.json`）必须写入 `.autoFormalization/units/` 目录，按章组织为 `Ch<N>/` 子目录（没有目录可创建）：

```
.autoFormalization/units/
├── Ch1/
│   ├── Def1_1.md
│   ├── Def1_1.json
│   ├── Thm1_5.md
│   ├── Thm1_5.json
│   └── ...
├── Ch2/
│   └── ...
└── ...
```

**约束**：
- 每个 unit 的 `.md` 与 `.json` 必须成对出现在 `units/Ch<N>/` 子目录下
- **禁止**将文件输出到 `units/` 以外的任何目录

## LaTeX 公式规范

- 行内公式用单美元符包围，如 $x \in A$
- 块级公式用双美元符包围，块级公式前后各加空行
- 原文符号保留原样，不擅自替换字体命令
- 禁止使用图片形式的公式

## 章节边界处理

如果 PDF 末尾包含下一章前几节（如 Ch1 PDF 含 Ch2 前 3 节）：
- 一并切分
- 标 chapter 为 N+1

## 产出验收清单

完成后必须确认：
- 每个 unit 有 .md 和 .json 双文件
- LaTeX 公式可被 KaTeX 或 MathJax 渲染
- JSON 字段全部填充（无 null 或空字符串）
- [UNCERTAIN] 标注的位置已在汇报中列出

## 常见误区（来自实战经验）

1. 不要尝试装 Tesseract、OCR 工具或任何外部 PDF 处理包，CC Read 足够
2. 不要跳过诊断阶段，先用 Read 读前几页判断质量再动手
3. 不要一次处理整本书，按章逐个处理便于回查

