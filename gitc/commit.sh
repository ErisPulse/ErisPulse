# 参数校验
if [ $# -lt 2 ]; then
    echo "用法: $0 <分支名> \"<提交信息>\""
    exit 1
fi

# 检查是否在正确的分支上
current_branch=$(git symbolic-ref --short HEAD)
expected_branch="feature/$1"

if [ "$current_branch" != "$expected_branch" ]; then
    echo "错误：当前在分支 $current_branch，不在目标分支 $expected_branch"
    echo "请先切换到目标分支"
    exit 1
fi

# 执行提交
git add .
git commit -m "$2"
git push -u origin "feature/$1"
