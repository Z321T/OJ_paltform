#!/bin/bash

# 参数
EXECUTABLE=$1      # 可执行文件名（例如 ./temp）
INPUT_FILE=$2      # 输入文件名（例如 test_input.txt）
OUTPUT_FILE=$3     # 输出文件路径（例如 output.txt）
RESOURCE_FILE=$4   # 资源使用文件路径（例如 resource_usage.txt）

# 编译用户的 C++ 程序
g++ temp.cpp -o $EXECUTABLE

# 启动计时
start_time=$(date +%s%3N)

# 运行用户程序，限制运行时间为 5 秒
timeout 5 /usr/bin/time -v $EXECUTABLE < $INPUT_FILE > $OUTPUT_FILE 2> $RESOURCE_FILE
EXIT_CODE=$?  # 获取程序退出码

# 结束计时
end_time=$(date +%s%3N)

# 计算总的运行时间
elapsed_time=$((end_time - start_time))

# 打印运行时间到 stderr（方便调试或日志记录）
echo "Execution Time: ${elapsed_time} ms" >&2

exit $EXIT_CODE
