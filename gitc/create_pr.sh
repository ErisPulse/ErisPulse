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

# 更新分支
git pull origin "$current_branch"

# 使用 GitHub CLI 创建 PR
pr_title="合并 $branch_name 到 develop"
pr_body="由 $(git config user.name) 于 $(date +'%Y-%m-%d %H:%M') 创建"

gh pr create \
    --base develop \
    --head "$current_branch" \
    --title "$pr_title" \
    --body "$pr_body"

echo "✅ 已创建从 $current_branch 到 develop 的 PR"
echo "标题: \"$pr_title\""
