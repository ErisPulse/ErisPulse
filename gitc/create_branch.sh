# 参数校验
if [ $# -eq 0 ]; then
    echo "用法: $0 <新分支名>"
    exit 1
fi

# 检查分支是否已存在
if git show-ref --quiet refs/heads/feature/"$1"; then
    echo "错误：分支 feature/$1 已存在"
    exit 1
fi

# 创建分支
git checkout develop
git pull origin develop
git checkout -b "feature/$1"
echo "已创建新分支 feature/$1"
