# research-agents

Мультиагентный ресёрч-стек. Полное описание — в `README.md`.

## Доступно из этой папки
- **MCP** (`.mcp.json`): `arxiv` (поиск/чтение статей), `sentrux` (архитектурный сенсор кода),
  `outline` (база знаний лаборатории — нужен токен), `gdrive` (нужны OAuth-ключи).
- **Скиллы** (`.claude/skills/`): `skill-creator`, `mcp-builder`, `caveman`, `caveman-compress`,
  `caveman-explore`, `arxiv-mcp-server`.
- **Бинари** (`bin/`): `rtk.exe` (сжатие вывода CLI), `sentrux.exe` (`gate --save` / `gate` вокруг сессии).

## Рабочий цикл (по докладу AIRI)
1. `sentrux gate --save .` перед правками кода, `sentrux gate .` после — ловит деградацию архитектуры.
2. Внешняя разведка: arXiv MCP для первичных публикаций, `/deep-research` для широкого обзора.
3. Внутренняя память: Outline (гипотезы, отрицательные результаты), Google Drive (оформленные отчёты).
4. Удачные последовательности шагов оформляй скиллом через `skill-creator`.
