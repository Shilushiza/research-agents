# research-agents

Готовый стек для **Claude Code**, чтобы автоматизировать доменные исследования: скиллы, MCP-серверы,
CLI-утилиты для экономии контекста и рабочий цикл «разведка → формализация → реализация → проверка».

Стек собран по докладу **Даниила Сухорукова (AIRI) «Терминальные агенты в задачах автоматизации
доменных исследований»**. В PDF доклада были только названия инструментов, ссылки на них найдены и
проверены отдельно.

В репозитории также лежит пример исследования, выполненного на этом стеке: **защищённая агрегация
в федеративном обучении парка роботов** (отчёты в `research/`, реализация в `implementation/`).

---

## Быстрый старт

```bash
git clone --recurse-submodules https://github.com/Shilushiza/research-agents.git
cd research-agents
claude
```

При запуске из этой папки Claude Code автоматически подхватывает:

- **скиллы** из `.claude/skills/` (индекс: [`.claude/skills/README.md`](.claude/skills/README.md));
- **MCP-серверы** из `.mcp.json`, которые автоматически включает `.claude/settings.json`;
- **памятку по рабочему циклу** из [`CLAUDE.md`](CLAUDE.md).

Чтобы скиллы были доступны **из любой папки**, подключите репозиторий как плагин:

```
/plugin marketplace add <путь-к-research-agents>
/plugin install research-agents@research-agents
```

> [!NOTE]
> В `.mcp.json` прописаны абсолютные пути вида `D:\research-agents\...`. Если вы клонировали репозиторий
> в другое место, поправьте их.

---

## Инструменты

| Инструмент | Какую проблему решает | Источник | Где в репо |
|---|---|---|---|
| **RTK** (Rust Token Killer) | вывод CLI не влезает в контекст, RTK оставляет только важное | [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | `bin/rtk.exe` (v0.47.0) |
| **Sentrux** | непонятно, как устроена кодовая база: даёт живой граф архитектуры и оценку A–F | [sentrux/sentrux](https://github.com/sentrux/sentrux) | `bin/sentrux.exe` (v0.5.7) + MCP |
| **Caveman** | ответы агента многословны, Caveman их сжимает | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | скиллы `caveman*` |
| **Skill Creator** | инструкции приходится писать заново, а скилл превращает их в процедуру | [anthropics/skills](https://github.com/anthropics/skills) | `.claude/skills/skill-creator` |
| **deep-research** | нужна широкая внешняя разведка по задаче | локальный скилл | `.claude/skills/deep-research` |
| **arXiv MCP** | нужны первичные публикации: версии, методы, метрики | [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) | pip `arxiv-mcp-server` + скилл |
| **Google Drive MCP** | нужны внутренние документы и отчёты | [isaacphi/mcp-gdrive](https://github.com/isaacphi/mcp-gdrive) | `.mcp.json`, нужны OAuth-ключи |
| **Outline MCP** | нужна общая база идей, гипотез и статусов лаборатории | [Vortiago/mcp-outline](https://github.com/Vortiago/mcp-outline) | pip `mcp-outline`, нужен API-токен |

Исходники всех сторонних инструментов подключены как **git-сабмодули** в `repos/`.

### Скиллы (`.claude/skills/`, 24 шт.)

| Группа | Скиллы |
|---|---|
| Ресёрч | `deep-research`, `arxiv-mcp-server` |
| Сжатие контекста | `caveman`, `caveman-compress`, `caveman-explore`, `cavecrew`, `caveman-stats`, `caveman-learn` |
| Качество кода | `investigate-first`, `lean-build`, `surgical-patch`, `safe-refactor`, `migration`, `verify-and-stop`, `caveman-review`, `caveman-commit` |
| Свои инструменты | `skill-creator`, `mcp-builder` |
| Только с Caveman Cloud | `caveman-discover`, `caveman-setup`, `caveman-manage`, `caveman-optimize`, `caveman-evidence-review`, `caveman-help` |

---

## Структура

```
research-agents/
├─ .mcp.json              # MCP-серверы: arxiv, sentrux, outline, gdrive
├─ .claude/
│  ├─ settings.json       # автовключение MCP этого проекта
│  └─ skills/             # 24 скилла + README.md (индекс)
├─ .claude-plugin/        # marketplace.json + plugin.json для /plugin
├─ CLAUDE.md              # рабочий цикл и правила для агента
├─ bin/                   # rtk.exe, sentrux.exe (Windows)
├─ repos/                 # сабмодули: исходники инструментов
├─ research/              # отчёты deep-research (.md) и формализация в LaTeX (tex/)
├─ implementation/        # Python-реализация протоколов из research/ + тесты
└─ data/                  # (в .gitignore) скачанные статьи arXiv, креды gdrive
```

---

## Настройка

### 1. MCP-серверы

Проверить состояние серверов можно командой `/mcp` в Claude Code.

| Сервер | Что нужно |
|---|---|
| `arxiv` | `pip install arxiv-mcp-server` |
| `sentrux` | ничего, бинарник уже в `bin/` |
| `outline` | `pip install mcp-outline`; впишите `OUTLINE_API_KEY` в `.mcp.json` (Outline → Settings → API Keys). Для self-hosted Outline поправьте `OUTLINE_API_URL` |
| `gdrive` | Node.js; проект в Google Cloud с включённым Drive API → OAuth client (Desktop) → впишите `CLIENT_ID` и `CLIENT_SECRET`. При первом запуске откроется браузер для авторизации |

> [!WARNING]
> Не коммитьте настоящие ключи. Держите их в локальной копии `.mcp.json` или в переменных окружения.

### 2. RTK (хук на вызовы Bash)

Эта команда меняет глобальный `~/.claude/settings.json`, поэтому запускайте её сознательно:

```bash
bin/rtk.exe init -g
```

Посмотреть экономию: `rtk gain`.

### 3. Sentrux (по желанию, помимо MCP)

```bash
bin/sentrux.exe <путь-к-проекту>   # GUI-треемап
bin/sentrux.exe gate --save .      # сохранить базовую линию перед сессией агента
bin/sentrux.exe gate .             # сравнить с ней после сессии
```

---

## Рабочий цикл

1. `sentrux gate --save .` перед правками кода, `sentrux gate .` после. Так видно, если архитектура деградировала.
2. Внешняя разведка: `/deep-research` для широкого обзора и arXiv MCP для первичных публикаций.
3. Внутренняя память: Outline для гипотез и отрицательных результатов, Google Drive для оформленных отчётов.
4. Контекст: `caveman` для ответов, `caveman-compress` для CLAUDE.md, `caveman-explore`/`cavecrew` вместо тяжёлого чтения репозитория.
5. Удачную последовательность шагов стоит оформить в скилл через `skill-creator`.

---

## Пример: защищённая агрегация для парка роботов

Это исследование целиком сделано на стеке: от обзора литературы до формальных протоколов и
протестированного кода.

### Отчёты (`research/`)

| Отчёт | Тема |
|---|---|
| `federated-learning-basics` | основы федеративного обучения и его применение к парку роботов |
| `robot-fleet-brain-architecture` | где находится «мозг» робота при обучении флотом |
| `multi-robot-communication-topology` | топологии взаимодействия между роботами |
| `federated-aggregation-methods` | методы агрегации обновлений в FL |
| `shamir-secret-sharing-mpc` | разделение секрета по Шамиру и MPC |
| `federated-mpc-formalization` | формализация MPC-слоя: PRSS, threshold-HE, compartmented secret sharing |
| `nlp-people-analysis-negotiation` | отдельная тема: НЛП и «чтение людей» для переговорного тренажёра |

В `research/tex/` лежат формализации в LaTeX с собранными PDF, от `00_project_summary_report` до
`07_threat_model`.

### Реализация (`implementation/`)

| Модуль | Что реализует |
|---|---|
| `shamir.py` | (t, n)-пороговое разделение секрета Шамира над простым полем |
| `prss.py` | PRSS-маскирование с нулевой суммой (как в Bonawitz et al.) и восстановление после выпадения участников через Шамира |
| `paillier.py` | аддитивно-гомоморфное шифрование Paillier |
| `threshold_paillier.py` | распределённая N-of-N расшифровка Paillier |
| `masked_paillier.py` | комбинация PRSS-масок и Paillier (key-homomorphic masking) |
| `three_server_secret_sharing.py` | аддитивное разделение на 3 сервера (Prio/ABY3), 3-of-3 |
| `replicated_3server.py` | реплицированное 2-of-3 разделение (ABY3), выдерживает выпадение одного сервера |
| `compartmented_secret_sharing.py` | разделение с учётом «семей» роботов (Simmons, Brickell) |
| `group_testing.py` | неадаптивное групповое тестирование для поиска вредоносных клиентов (FedGT) |

Каждый модуль ссылается на раздел LaTeX-формализации, где описан протокол.

> [!CAUTION]
> Размеры ключей здесь демонстрационные. Код иллюстрирует протоколы и не предназначен для продакшена.

Запуск тестов:

```bash
cd implementation
pip install -r requirements.txt
python -m pytest -q
```

---

## Обновление инструментов

```bash
git submodule update --remote
pip install -U arxiv-mcp-server mcp-outline
# rtk и sentrux: скачайте свежий бинарник из GitHub Releases
```

## Каналы автора доклада

[airi.net](https://airi.net) · Telegram `@airi_research_institute` · Telegram `@weatherpapers` · VK «AIRI Institute»
