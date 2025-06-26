# 确保在 Git 仓库中
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "错误：不在 Git 仓库中"
    exit 1
fi

# 确保有远程仓库 origin
if ! git remote | grep -q 'origin'; then
    echo "错误：未配置远程仓库 origin"
    exit 1
fi

# 获取当前分支
current_branch=$(git symbolic-ref --short HEAD)

# 确保当前在特性分支上 (feature/*)
if [[ ! "$current_branch" =~ ^feature/ ]]; then
    echo "错误：当前不在特性分支 (feature/*) 上"
    echo "请在特性分支上执行此操作"
    exit 1
fi

# 获取特性分支名称 (去掉 feature/ 前缀)
feature_name=${current_branch#feature/}

echo "正在将 develop 分支的最新代码同步到 $current_branch..."

# 保存当前工作状态
if ! git diff-index --quiet HEAD --; then
    echo "检测到未提交的更改，正在暂存工作..."
    git stash push -u -m "同步前暂存: $feature_name"
    stashed=true
fi

# 获取 develop 分支的最新代码
git fetch origin develop

# 合并 develop 到当前分支
if git merge --no-ff --no-commit origin/develop; then
    # 自动合并成功
    git commit -m "同步 develop 分支的最新代码到 $current_branch"
    echo "✅ 成功同步 develop 最新代码到 $current_branch"
else
    # 自动合并失败，处理冲突
    echo "⚠️ 检测到合并冲突，请手动解决冲突后提交"
    echo "冲突解决步骤:"
    echo "1. 使用 'git status' 查看冲突文件"
    echo "2. 手动编辑标记为冲突的文件"
    echo "3. 使用 'git add <文件>' 标记已解决的冲突"
    echo "4. 使用 'git commit' 完成合并"
    exit_code=1
fi

# 恢复之前的工作状态
if [ "$stashed" = true ]; then
    echo "恢复暂存的工作..."
    git stash pop
fi

exit ${exit_code:-0}
