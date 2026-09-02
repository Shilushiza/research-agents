# research-agents — тяжёлая артиллерия для доменного ресёрча

Мультиагентный стек из доклада **Даниил Сухоруков (AIRI), «Терминальные агенты в задачах
автоматизации доменных исследований»**. В самом PDF ссылок не было — только названия на
слайдах 3 и 7; ссылки ниже восстановлены ресёрчем и проверены.

## TL;DR — достаточно обратиться к этой папке

```
cd /d D:\research-agents
claude
```

При запуске из этой папки Claude Code сам подхватывает:
- **все скиллы** из `.claude\skills\` (индекс — `.claude\skills\README.md`);
- **все MCP-серверы** из `.mcp.json` (авто-включены через `.claude\settings.json`);
- памятку по циклу работы — `CLAUDE.md`.

Осталось только вписать 2 секрета (Outline + Google Drive) — см. ниже.

Нужны скиллы **из любой папки**:
```
/plugin marketplace add D:\research-agents
/plugin install research-agents@research-agents
```

## Что стоит в этой папке

| Инструмент | Роль в докладе | Ссылка | Статус здесь |
|---|---|---|---|
| **RTK (Rust Token Killer)** | вывод CLI не влезает в контекст → фильтр по важности | https://github.com/rtk-ai/rtk | `bin/rtk.exe` v0.47.0 ✅ |
| **Sentrux** | непонятно, как устроена кодовая база → live-граф архитектуры, оценка A–F | https://github.com/sentrux/sentrux | `bin/sentrux.exe` v0.5.7 ✅ + MCP |
| **Caveman** | смысловой контекст многословен → сжатие ответов агента | https://github.com/JuliusBrussee/caveman | скиллы в `.claude/skills/` ✅ |
| **Skill Creator** | инструкции приходится задавать заново → процедура с входами/выходами/проверками | https://github.com/anthropics/skills (skill `skill-creator`) | `.claude/skills/skill-creator` ✅ |
| **/deep-research** | широкая внешняя разведка по задаче | Claude Code plugin marketplace (`/plugin`) — см. ниже | не вендорится, ставится плагином |
| **arXiv MCP** | точные первичные публикации: версии, методы, метрики | https://github.com/blazickjp/arxiv-mcp-server | pip-пакет `arxiv-mcp-server` ✅ + скилл |
| **Google Drive MCP** | внутренние документы и отчёты | офиц.: https://developers.google.com/workspace/drive/api/guides/configure-mcp-server · тут: https://github.com/isaacphi/mcp-gdrive | в `.mcp.json`, нужны OAuth-ключи ⚠️ |
| **Outline** | общая база идей/гипотез/статусов лаборатории | движок: https://github.com/outline/outline · MCP: https://github.com/Vortiago/mcp-outline | pip-пакет `mcp-outline` ✅, нужен API-токен ⚠️ |

Дополнительно скопирован `mcp-builder` (скилл Anthropic для сборки своих MCP-серверов).

## Структура

```
D:\research-agents\
├─ .mcp.json               # 4 MCP-сервера: arxiv, sentrux, outline, gdrive
├─ .claude\
│  ├─ settings.json        # авто-включение MCP этого проекта
│  └─ skills\              # 24 скилла + README.md (индекс по группам)
├─ .claude-plugin\         # marketplace.json + plugin.json — для /plugin из любой папки
├─ bin\                    # rtk.exe, sentrux.exe (Windows, самодостаточные)
├─ repos\                  # исходники всех инструментов (git, depth 1)
├─ data\                   # скачанные статьи arXiv, креды gdrive
└─ research\               # сюда deep-research кладёт отчёты
```

### Скиллы (`.claude\skills\`)

| Группа | Скиллы |
|---|---|
| Ресёрч | `deep-research`, `arxiv-mcp-server` |
| Сжатие контекста | `caveman`, `caveman-compress`, `caveman-explore`, `cavecrew`, `caveman-stats`, `caveman-learn` |
| Качество кода | `investigate-first`, `lean-build`, `surgical-patch`, `safe-refactor`, `migration`, `verify-and-stop`, `caveman-review`, `caveman-commit` |
| Свои инструменты | `skill-creator`, `mcp-builder` |
| Только с Caveman Cloud ⚠️ | `caveman-discover`, `caveman-setup`, `caveman-manage`, `caveman-optimize`, `caveman-evidence-review`, `caveman-help` |

Полный индекс с описаниями — [`.claude/skills/README.md`](.claude/skills/README.md).

## Как запустить

### 1. MCP-серверы
Запускай Claude Code **из этой папки** (`cd /d D:\research-agents`) — `.mcp.json` подхватится
автоматически. Проверка: `/mcp`.

- **arxiv** — работает сразу.
- **sentrux** — работает сразу (`--mcp`).
- **outline** — впиши `OUTLINE_API_KEY` в `.mcp.json` (Outline → Settings → API Keys → New).
  Для облачного Outline `OUTLINE_API_URL` уже верный; для self-hosted поправь.
- **gdrive** — нужен Google Cloud проект: создать проект → включить Drive API →
  OAuth client (Desktop) → вписать `CLIENT_ID` / `CLIENT_SECRET` в `.mcp.json`.
  Первый запуск откроет браузер для авторизации, токен ляжет в `data\gdrive`.

Путь к Python-скриптам (`arxiv-mcp-server`, `mcp-outline`) уже в PATH:
`C:\Users\ydtsv\AppData\Local\Programs\Python\Python312\Scripts`.

### 2. Скиллы
`.claude/skills/` виден Claude Code при запуске из этой папки. Чтобы были доступны глобально —
скопируй нужные в `C:\Users\ydtsv\.claude\skills\`.

### 3. RTK (хук на Bash-вызовы)
RTK работает как хук, который переписывает вывод команд. Ставится в глобальный
`~/.claude/settings.json` — **делать вручную**, это меняет общую конфигурацию:

```
D:\research-agents\bin\rtk.exe init -g
```

Проверка эффекта: `rtk gain` (дашборд экономии). Хук действует только на инструмент Bash;
для Read/Grep/Glob используй `rtk read` / `rtk grep` / `rtk find`.

### 4. Sentrux CLI (по желанию, помимо MCP)
```
D:\research-agents\bin\sentrux.exe D:\path\to\project   # GUI-треемап
D:\research-agents\bin\sentrux.exe gate --save .        # бейзлайн до сессии агента
D:\research-agents\bin\sentrux.exe gate .               # сравнение после
```

### 5. /deep-research
Отдельного публичного репозитория нет — это скилл/команда из маркетплейса плагинов Claude Code.
В Claude Code: `/plugin` → marketplace → поиск `deep-research` (или `research`). Как альтернатива —
встроенный агент `Explore` и community-плагин AutoSearch
(https://github.com/rohitg00/awesome-claude-code-toolkit).

## Каналы автора
- https://airi.net · Telegram `@airi_research_institute` · Telegram `@weatherpapers` · VK «AIRI Institute»

## Обновление инструментов
```
cd D:\research-agents\repos && for d in */; do (cd "$d" && git pull); done
pip install -U arxiv-mcp-server mcp-outline
# rtk / sentrux — перекачать бинарь из GitHub Releases
```
