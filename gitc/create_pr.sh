# 参数校验
if [ $# -eq 0 ]; then
    echo "用法: $0 <分支名>"
    exit 1
fi

# 确保在特性分支
current_branch=$(git symbolic-ref --short HEAD)
if [ "$current_branch" != "feature/$1" ]; then
    echo "错误：请先切换到 feature/$1 分支"
    exit 1
fi

# 更新分支
git pull origin "feature/$1"

# 使用 GitHub CLI 创建 PR
gh pr create \
    --base develop \
    --head "feature/$1" \
    --title "合并 $1 到 develop" \
    --body "合并 $1 到 develop"

echo "已创建从 feature/$1 到 develop 的 PR，请等待审核"
