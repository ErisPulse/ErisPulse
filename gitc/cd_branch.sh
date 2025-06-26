# 自动检测参数或使用当前目录名作为分支名
if [ $# -eq 0 ]; then
    branch_name=$(basename "$PWD")
else
    branch_name="$1"
fi

# 检查分支是否存在
if ! git show-ref --quiet refs/heads/feature/"$branch_name"; then
    echo "错误：分支 feature/$branch_name 不存在"
    echo "可用特性分支:"
    git branch -a | grep 'feature/' | sed 's/^..//; s/feature\///' | sort | uniq
    exit 1
fi

git checkout "feature/$branch_name"
echo "✅ 已切换到分支 feature/$branch_name"
