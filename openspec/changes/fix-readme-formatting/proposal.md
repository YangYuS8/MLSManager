# Change: Fix README Markdown Formatting

## Why
README.md 中的代码块使用了转义的反引号 (`\`\`\``) 而不是普通的三个反引号，导致 GitHub 上代码块无法正确渲染。

## What Changes
- 移除代码块标记中的反斜杠转义
- 确保所有代码块能在 GitHub 上正确显示

## Impact
- Affected files: `README.md`
- No code changes, documentation only
- Improves project presentation on GitHub
