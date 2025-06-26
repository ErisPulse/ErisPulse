# 自动检测参数或使用当前目录名作为分支名
if [ $# -eq 0 ]; then
    branch_name=$(basename "$PWD")
    echo "⚠️ 未提供分支名，使用当前目录名: $branch_name"
else
    branch_name="$1"
fi

# 检查分支是否已存在
if git show-ref --quiet refs/heads/feature/"$branch_name"; then
    echo "错误：分支 feature/$branch_name 已存在"
    exit 1
fi

# 创建分支
git checkout develop
git pull origin develop
git checkout -b "feature/$branch_name"

echo "✅ 已创建新分支 feature/$branch_name"
