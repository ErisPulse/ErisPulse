# 检查分支是否存在
if ! git show-ref --quiet refs/heads/feature/"$1"; then
    echo "错误：分支 feature/$1 不存在"
    exit 1
fi

git checkout "feature/$1"
