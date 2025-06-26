# 自动获取当前分支
current_branch=$(git symbolic-ref --short HEAD)

# 检查是否在特性分支上
if [[ ! "$current_branch" =~ ^feature/ ]]; then
    echo "错误：当前不在特性分支上（当前分支: $current_branch）"
    echo "请在特性分支上执行此操作"
    exit 1
fi

# 提取分支名（去掉feature/前缀）
branch_name=${current_branch#feature/}

echo "🔄 正在将 develop 分支的最新代码同步到 $current_branch..."

# 保存当前工作状态
stashed=false
if ! git diff-index --quiet HEAD --; then
    echo "检测到未提交的更改，正在暂存工作..."
    git stash push -u -m "自动暂存: $branch_name $(date +'%Y%m%d-%H%M%S')"
    stashed=true
fi

# 获取 develop 分支的最新代码
git fetch origin develop

# 合并 develop 到当前分支
merge_success=true
if ! git merge --no-ff --no-commit origin/develop; then
    merge_success=false
fi

# 处理合并结果
if $merge_success; then
    git commit -m "同步 develop 分支到 $current_branch [自动提交]"
    echo "✅ 成功同步 develop 最新代码到 $current_branch"
else
    echo "⚠️ 检测到合并冲突，请手动解决:"
    echo "   1. 查看冲突: git status"
    echo "   2. 解决冲突后: git add <文件>"
    echo "   3. 完成合并: git commit"
    echo "   4. 推送更改: git push"
fi

# 恢复之前的工作状态
if $stashed; then
    echo "恢复暂存的工作..."
    git stash pop
fi

# 显示最终状态
echo -e "\n当前分支状态:"
git status --short

exit $([ $merge_success = true ] && echo 0 || echo 1)
