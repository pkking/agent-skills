---
name: release-poster
description: Generate tech-style release announcement posters for software projects. Use when creating promotional long images for version releases, changelogs, or update announcements. Triggers on requests like "create release poster", "make announcement image", "generate changelog graphic", "版本发布海报", or "宣传长图".
---

# Release Poster Generator

Generate professional, tech-style release announcement posters with clean modern aesthetics.

## Design Style

- **Background**: Soft gradient (light blue to white) with subtle tech decorations (circular elements, vertical accent lines, gradient glows)
- **Layout**: Centered title + white rounded card with soft shadow
- **Typography**: Bold blue title, clear section headers, readable body text
- **Icons**: Colored circles categorizing update types

## Quick Start

```python
from scripts.generate_poster import create_release_poster

create_release_poster(
    title="vLLM Ascend",
    version="v0.11.0",
    items=[
        ("party", "本版本共计6个commits，新增1位新开发者！"),
        ("rocket", "DeepSeek 3/3.1 性能显著提升"),
        ("bug", "修复 Qwen3-VL 精度问题"),
        ("refresh", "torch-npu 升级至 2.7.1.post1"),
        ("warning", "废弃预告：旧API将在下版本移除"),
    ],
    footer_text="GitHub: github.com/project/repo",
    output_path="release.png"
)
```

## Icon Types

| Icon | Color | Use For |
|------|-------|---------|
| `star` | Gold | Section headers (亮点更新) |
| `party` | Yellow | Statistics, milestones, contributor counts |
| `rocket` | Red | Performance improvements |
| `fire` | Orange | New features |
| `bug` | Dark red | Bug fixes |
| `refresh` | Blue | Dependency updates |
| `warning` | Yellow △ | Deprecation notices, breaking changes |

## Customization

### Dimensions
Default: 750×1050px. Adjust `WIDTH` and `HEIGHT` in script.

### Colors
Modify color constants at top of script:
```python
TITLE_BLUE = (30, 64, 175)   # Title color
TEXT_DARK = (51, 65, 85)     # Body text
```

### Decorations
Toggle tech elements by commenting out relevant sections:
- Gradient glows (top-right, bottom-left)
- Decorative circles
- Side accent lines

## Workflow

1. Gather release info from GitHub/changelog
2. Categorize updates by type
3. Call `create_release_poster()` with content
4. Output PNG ready for social media

## Font Requirements

Script uses system fonts:
- **Chinese**: DroidSansFallbackFull.ttf
- **English**: DejaVuSans.ttf

If fonts unavailable, install via package manager or modify font paths in script.
