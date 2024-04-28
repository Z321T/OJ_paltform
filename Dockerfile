# 使用包含g++编译器的基础镜像
FROM gcc:latest

# 创建一个目录来存放用户代码
WORKDIR /usercode

# 默认命令
CMD ["bash"]
