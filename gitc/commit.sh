# 自动获取当前分支名
current_branch=$(git symbolic-ref --short HEAD)

# 检查是否在特性分支上
if [[ ! "$current_branch" =~ ^feature/ ]]; then
    echo "错误：当前不在特性分支上（当前分支: $current_branch）"
    echo "请在特性分支上执行此操作"
    exit 1
fi

# 提取分支名（去掉feature/前缀）
branch_name=${current_branch#feature/}

# 自动生成提交信息（如果未提供）
if [ $# -eq 0 ]; then
    commit_msg="更新: $(date +'%Y-%m-%d %H:%M')"
    echo "⚠️ 未提供提交信息，使用默认信息: \"$commit_msg\""
else
    commit_msg="$@"
fi

# 执行提交
git add .
git commit -m "$commit_msg"
git push -u origin "$current_branch"

echo "✅ 已提交更改到 $current_branch"
echo "提交信息: \"$commit_msg\""
