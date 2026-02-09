# Fix Failed CI PR

## 描述

自动分析 GitCode 上 CI 失败的 Pull Request，诊断失败原因并实施修复，最后创建新的修复 PR。适用于任何基于 GitCode/GitHub 托管的、使用 Docker 镜像构建 CI 的项目。

## 使用场景

- 场景1：自动升级机器人创建的 PR 因上游依赖变更导致 CI 失败
- 场景2：Docker 镜像构建失败（RPM/二进制包不存在、依赖冲突等）
- 场景3：需要快速分析和修复 CI 失败，避免手动逐步调试

## 前置要求

### 环境要求
- 已克隆目标仓库到本地
- Git remotes 已配置：
  - `origin`: 你的 fork 仓库
  - `upstream`: 主仓库（目标合并仓库）

### 凭证配置
- GitCode/GitHub token 存储在 `~/.git-credentials` 中
- 格式：`https://username:token@gitcode.com` 或 `https://username:token@github.com`

### 工具依赖
- `curl`: API 请求
- `python3`: JSON 解析和 API 调用
- `docker`: 验证镜像（可选）
- `git`: 版本控制

## 参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| PR URL 或编号 | string | 是 | - | GitCode PR 链接或纯编号 |

参数格式支持：
- 完整 URL：`https://gitcode.com/{owner}/{repo}/pull/{number}`
- 仅编号：`{number}`（将使用当前仓库信息）

## 使用方法

### 基本用法

```bash
/fix-pr https://gitcode.com/openeuler/openeuler-docker-images/pull/1838
```

### 简化用法（仅 PR 编号）

```bash
/fix-pr 1838
```

## 执行流程

### 步骤1：解析输入并提取仓库信息

从参数 `$ARGUMENTS` 中提取：
- PR 编号
- 仓库所有者（owner）
- 仓库名称（repo）
- Git 平台（GitCode/GitHub）

如果仅提供编号，从当前 git remote 推断仓库信息：
```bash
# 提取 upstream remote 的 owner 和 repo
git remote get-url upstream
# 示例输出: https://gitcode.com/openeuler/openeuler-docker-images.git
# 解析得到: owner=openeuler, repo=openeuler-docker-images
```

### 步骤2：获取 PR 详细信息

使用平台 API 获取 PR 元数据：

**GitCode API:**
```bash
TOKEN=$(python3 -c "import urllib.parse; line=[l for l in open('/root/.git-credentials') if 'gitcode' in l][0]; token=urllib.parse.urlparse(line.strip()).password; print(token)")
curl -s "https://gitcode.com/api/v5/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}?access_token=$TOKEN"
```

**GitHub API:**
```bash
TOKEN=$(python3 -c "import urllib.parse; line=[l for l in open('/root/.git-credentials') if 'github' in l][0]; token=urllib.parse.urlparse(line.strip()).password; print(token)")
curl -s -H "Authorization: token $TOKEN" "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}"
```

提取关键信息：
- `title`: PR 标题
- `labels`: 确认包含失败标签（`ci_failed`、`failing`等）
- `head.ref`: 源分支名
- `head.repo.full_name`: 源仓库完整路径
- `base.ref`: 目标分支（通常是 `master`/`main`）
- `body`: PR 描述

### 步骤3：获取 PR 变更内容

```bash
# 获取源分支所属的 remote（从 head.repo.full_name 推断）
SOURCE_REMOTE=$(git remote -v | grep "${HEAD_REPO_OWNER}" | head -1 | awk '{print $1}')

# Fetch 源分支
git fetch ${SOURCE_REMOTE} "${HEAD_REF}"

# 查看修改的文件
git diff upstream/${BASE_BRANCH}...FETCH_HEAD --name-only

# 查看完整 diff（关注 Dockerfile）
git diff upstream/${BASE_BRANCH}...FETCH_HEAD
```

### 步骤4：获取 CI 失败日志

从 PR 评论中提取 CI 日志链接：

```bash
# GitCode
curl -s "https://gitcode.com/api/v5/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments?access_token=$TOKEN&per_page=100"

# GitHub
curl -s -H "Authorization: token $TOKEN" "https://api.github.com/repos/${OWNER}/${REPO}/issues/${PR_NUMBER}/comments?per_page=100"
```

查找包含 CI 失败信息的评论：
- 关键词：`FAILED`, `check_build`, `ci_failed`, `Actions failed`
- 提取 Jenkins/GitHub Actions 日志链接

使用 `WebFetch` 读取日志内容，定位错误行。

### 步骤5：分析失败模式并制定修复方案

#### 模式 A：上游停止发布二进制包
- **症状**: `curl`/`wget` 返回 404，日志显示 "Not Found"
- **验证**:
  ```bash
  curl -sI <package_download_url> | grep "HTTP"
  ```
- **修复方案**: 多阶段 Docker 构建，从官方镜像复制
  ```dockerfile
  ARG VERSION=x.y.z
  FROM upstream/official-image:v${VERSION} AS source
  FROM base-image:tag
  COPY --from=source /path/to/binary /path/to/binary
  ```
- **验证步骤**:
  1. 在 DockerHub/Quay 搜索官方镜像
  2. `docker pull` 并 `docker run --rm --entrypoint which <image> <binary>` 定位文件

#### 模式 B：依赖兼容性问题
- **症状**: `ImportError`, `AttributeError`, `ModuleNotFoundError`
- **修复方案**:
  - 锁定依赖版本：`RUN pip install package==x.y.z`
  - Sed 修复配置：`RUN sed -i 's/old/new/' script.sh`
  - 降级/升级工具链

#### 模式 C：CI 基础设施问题
- **症状**: 错误发生在 CI 脚本阶段，而非 Docker build 阶段
- **判断条件**:
  - 部分架构成功（如 aarch64 ✓, x86_64 ✗）
  - 错误提示 CI 工具本身的问题（如 `eulerpublisher`）
- **修复方案**: 评论 `/retest` 触发重试

#### 模式 D：源码/配置错误
- **症状**: 编译错误、语法错误、配置格式错误
- **修复方案**: 根据日志修改对应文件

**常见子类型**:

**D1: 缺少系统包**
- **症状**: `command not found` 错误（如 `groupadd`, `useradd`, `make`）
- **示例错误**: `/bin/sh: line 1: groupadd: command not found`
- **诊断**: 检查错误日志中缺失的命令
- **修复**: 在 Dockerfile 中安装对应的包
  ```dockerfile
  # 缺少 groupadd/useradd
  RUN yum install -y shadow-utils

  # 缺少 make/gcc
  RUN yum install -y make gcc
  ```

**D2: Shell 语法错误**
- **症状**: 变量展开错误、命令替换错误
- **常见错误**:
  - `$nproc` 应为 `$(nproc)` - 命令替换
  - `$((expr))` vs `$(command)` 混淆
  - 未转义的特殊字符
- **示例**:
  ```dockerfile
  # 错误
  RUN make -j$nproc

  # 正确
  RUN make -j$(nproc)
  ```

**D3: Dockerfile 语法/逻辑错误**
- **症状**: 构建步骤顺序错误、路径错误、ARG/ENV 使用不当
- **常见问题**:
  - 在使用工具前未安装
  - 工作目录（WORKDIR）设置错误
  - 多阶段构建中 COPY 路径错误
- **修复**: 重新组织 Dockerfile 结构

### 步骤6：实施修复

1. **创建修复分支**:
   ```bash
   # 基于目标分支创建
   git checkout -b fix/<component>-<version> upstream/${BASE_BRANCH}
   ```

2. **修改文件** (Docker 镜像仓库常见结构):
   - `<Category>/<component>/<version>/<base-version>/Dockerfile`
   - `<Category>/<component>/<version>/<base-version>/*.yaml` (配置文件)
   - `<Category>/<component>/meta.yml` (版本元数据)
   - `<Category>/<component>/README.md` (文档)
   - `<Category>/<component>/doc/image-info.yml` (镜像信息)

3. **保持格式一致**: 参考同目录其他版本的文件

### 步骤7：提交并推送

```bash
git add <modified_files>

git commit -m "Fix <component> <version> build failure

Fix PR #${ORIGINAL_PR_NUMBER} CI failure: <brief_reason>.

<detailed_fix_description>

git push origin fix/<component>-<version>
```

### 步骤8：创建新 PR

通过平台 API 创建：

```python
import urllib.request, urllib.parse, json

# 读取 token
with open("/root/.git-credentials") as f:
    for line in f:
        if "gitcode" in line or "github" in line:
            token = urllib.parse.urlparse(line.strip()).password
            platform = "gitcode" if "gitcode" in line else "github"
            break

# 获取当前用户
current_user = $(git config --get user.name)

# 构造 API 请求
if platform == "gitcode":
    api_url = f"https://gitcode.com/api/v5/repos/{owner}/{repo}/pulls"
    data = {
        "access_token": token,
        "title": f"Fix {component} {version} build (fix #{original_pr})",
        "head": f"{current_user}:fix/{component}-{version}",
        "base": base_branch,
        "body": f"{original_body}\n\n## Fix\n{fix_description}"
    }
    headers = {"Content-Type": "application/json", "PRIVATE-TOKEN": token}
else:  # GitHub
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    data = {
        "title": f"Fix {component} {version} build (fix #{original_pr})",
        "head": f"{current_user}:fix/{component}-{version}",
        "base": base_branch,
        "body": f"{original_body}\n\n## Fix\n{fix_description}"
    }
    headers = {"Content-Type": "application/json", "Authorization": f"token {token}"}

req = urllib.request.Request(api_url, data=json.dumps(data).encode(), headers=headers, method="POST")
```

### 步骤9：验证新 PR 的 CI

1. 等待 2-3 分钟让 CI 启动
2. 轮询 PR 评论获取 CI 状态
3. 如果仍失败：
   - **CI 基础设施问题**: 评论 `/retest`
   - **代码问题**: 返回步骤5重新分析

## 示例

### 示例1：修复 RPM 包不存在的问题

```bash
/fix-pr https://gitcode.com/openeuler/openeuler-docker-images/pull/1838
```

**场景**: grafana-agent v0.44.7 不再发布 RPM 包

**执行过程**:
1. 提取 PR #1838 信息
2. 发现 Dockerfile 尝试下载 `grafana-agent-0.44.7-1.amd64.rpm`
3. 验证 URL 返回 404
4. 检测到 DockerHub 存在 `grafana/agent:v0.44.7`
5. 修改 Dockerfile 为多阶段构建
6. 创建新 PR #1857

**修复内容**:
```dockerfile
FROM grafana/agent:v0.44.7 AS source
FROM openeuler/openeuler:24.03-lts-sp3
COPY --from=source /usr/bin/grafana-agent /usr/bin/grafana-agent
```

### 示例2：修复缺少系统包问题

```bash
/fix-pr 1837
```

**场景**: mlflow 3.9.0 构建失败，双架构都报 `groupadd: command not found`

**执行过程**:
1. 提取 PR #1837 信息
2. 查看 CI 日志发现 `groupadd: command not found`
3. 诊断：Dockerfile 使用 `groupadd`/`useradd` 但基础镜像缺少 `shadow-utils`
4. 修复：在 yum install 中添加 `shadow-utils`
5. 创建新 PR #1858

**修复内容**:
```dockerfile
# 修复前
RUN yum install -y python3-pip && yum clean all

# 修复后
RUN yum install -y python3-pip shadow-utils && yum clean all
```

### 示例3：修复 Shell 语法错误

```bash
/fix-pr 1835
```

**场景**: snort3 3.10.2.0 编译时 make 并行化失败

**执行过程**:
1. 提取 PR #1835 信息
2. 查看 aarch64 日志提示 `$nproc` 语法问题
3. 诊断：`make -j$nproc` 应该是 `make -j$(nproc)`
4. 修复：修正命令替换语法
5. 创建新 PR #1859

**修复内容**:
```dockerfile
# 修复前
RUN make -j$nproc && make install

# 修复后
RUN make -j$(nproc) && make install
```

### 示例4：修复依赖兼容性问题

```bash
/fix-pr 1839
```

**场景**: pip 26.0 移除了 `PackageFinder.allow_all_prereleases` API

**修复内容**:
```dockerfile
RUN sed -i 's/--upgrade-deps //' scripts/pkgdep/rhel.sh
```

## 输出格式

完成后输出以下信息：

```
✅ PR 修复完成

📋 原始 PR: #<number> - <title>
🔍 失败原因: <root_cause>
🛠️ 修复方案: <fix_strategy>

🔗 新 PR: #<new_number>
   链接: <pr_url>

⏳ CI 状态: <ci_status>
   - x86_64: <status>
   - aarch64: <status>

💡 建议: <next_steps_if_needed>
```

## 快速参考

### 错误信息速查表

| 错误信息 | 失败模式 | 典型修复 |
|---------|---------|---------|
| `404 Not Found` (下载失败) | A | 多阶段构建从官方镜像复制 |
| `command not found: groupadd` | D1 | `yum install -y shadow-utils` |
| `command not found: make` | D1 | `yum install -y make` |
| `ImportError: cannot import` | B 或 C | 检查是否 eulerpublisher 问题；否则修复依赖 |
| `$nproc` 未展开 | D2 | 改为 `$(nproc)` |
| `pip install` 兼容性错误 | B | 锁定版本或 sed 修复脚本 |
| 单架构失败 + eulerpublisher | C | `/retest` |
| `autoreconf: command not found` | D1 | `yum install -y autoconf automake` |

### 修复模式决策树

```
CI 失败
├─ 错误在 CI 脚本阶段？
│  ├─ 是 → 模式 C (基础设施) → /retest
│  └─ 否 → 继续
│
├─ 下载文件返回 404？
│  ├─ 是 → 模式 A (包不存在) → 多阶段构建
│  └─ 否 → 继续
│
├─ "command not found"？
│  ├─ 是 → 模式 D1 (缺包) → yum install
│  └─ 否 → 继续
│
├─ Shell 变量/语法问题？
│  ├─ 是 → 模式 D2 (语法) → 修正语法
│  └─ 否 → 继续
│
└─ ImportError / 依赖错误？
   └─ 是 → 模式 B (兼容性) → 锁定版本/sed 修复
```

## 故障诊断技巧

### 快速定位错误类型

1. **检查错误发生阶段**:
   - CI 脚本阶段（eulerpublisher 错误）→ 模式 C（基础设施问题）
   - Docker build 阶段 → 继续诊断

2. **检查架构失败模式**:
   - 双架构都失败 → 代码/依赖问题
   - 单架构失败 → 可能是 CI 基础设施问题

3. **查找关键错误信息**:
   ```
   command not found     → 缺少系统包（模式 D1）
   HTTP 404             → 上游包不存在（模式 A）
   ImportError          → 依赖兼容性（模式 B）
   syntax error         → Shell/Dockerfile 语法（模式 D2）
   $variable 未展开      → 命令替换语法错误（模式 D2）
   ```

4. **WebFetch 日志时的技巧**:
   - 如果日志被截断，关注 "Content truncated" 前的最后几行
   - 搜索关键词：`Error`, `error`, `FAILED`, `命令未找到`
   - 注意编译警告（warnings）可能导致后续失败

### 常见陷阱

1. **不要仅看最后一行错误**:
   - 真正的错误可能在更早的位置
   - 查找第一个 `Error:` 或 `error:` 出现的位置

2. **注意日志截断**:
   - Jenkins 日志可能因过长被截断
   - 使用 WebFetch 获取关键部分
   - 关注 aarch64 和 x86_64 的不同错误信息

3. **Shell 变量展开**:
   - `$var` 是变量引用
   - `$(cmd)` 是命令替换
   - `${var}` 是变量展开（推荐，更明确）

4. **验证修复前先本地测试**（可选）:
   ```bash
   # 构建测试（需要 Docker）
   cd <Dockerfile目录>
   docker build -t test:local .
   ```

## 注意事项

- **权限要求**: 需要对 fork 仓库有 push 权限
- **Token 安全**: 确保 `~/.git-credentials` 权限为 600
- **并行构建**: 不同架构可能有不同结果，需分别检查
- **自动化限制**: 复杂错误可能需要人工介入
- **日志分析**: 优先查看失败的架构日志，两个架构都失败时对比差异

## 相关 Skills

- `/commit`: 创建标准化的 Git 提交
- `/review-pr`: 审查 Pull Request

## 成功案例

| PR # | 应用 | 问题类型 | 修复 PR | 状态 |
|------|------|----------|---------|------|
| #1838 | grafana-agent 0.44.7 | 模式 A - RPM 包不存在 | #1857 | ✅ 成功 (aarch64 ✓, x86_64 需 retest) |
| #1837 | mlflow 3.9.0 | 模式 D1 - 缺少 shadow-utils | #1858 | ⏳ CI 中 |
| #1835 | snort3 3.10.2.0 | 模式 D2 - Shell 语法错误 | #1859 | ⏳ CI 中 |

## 相关 Skills

- `/commit`: 创建标准化的 Git 提交
- `/review-pr`: 审查 Pull Request

## 更新日志

### v1.2.0 (2026-02-08)
- 新增模式 D 的详细子分类（D1/D2/D3）
- 添加故障诊断技巧章节
- 新增 3 个实际修复案例
- 完善常见陷阱说明

### v1.1.0 (2026-02-08)
- 重构为通用 skill，支持任意 GitCode/GitHub 仓库
- 添加标准模板格式
- 新增自动推断仓库信息功能

### v1.0.0 (2026-02-08)
- 初始版本，仅支持 openeuler-docker-images

## 作者

@sunshuang1866

## 最后更新

2026-02-08
