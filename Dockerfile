# 使用包含g++编译器的基础镜像
FROM gcc:latest

# 创建一个目录来存放用户代码
WORKDIR /usercode

# 默认命令
CMD ["bash"]



#打包
FROM python:3.11

# 设置 python 环境变量
ENV PYTHONUNBUFFERED 1

# 创建 django2dockerapp 文件夹并将其设置为工作目录
#RUN mkdir /Software_cup
WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/

#更新pip
#RUN pip install pip -U

#将requirements文件复制到容器的Software_cup
#COPY requirements.txt .
#COPY ./administrator_app ./administrator_app
#COPY ./BERT_app ./BERT_app
#COPY ./CUMT ./CUMT
#COPY ./django_celery ./django_celery
#COPY ./login ./login
#COPY ./node_modules ./node_modules
#COPY ./Spark_app ./Spark_app
#COPY ./static ./static
#COPY ./student_app ./student_app
#COPY ./teacher_app ./teacher_app

#ADD manage.py .


##暴露端口
#EXPOSE 8080
#
##启动项目，这里的路径就是前面基础镜像包的CODE_DIR路径，再加上自己的项目复制到里面的路径，不清楚的可以参考这我给出的结构进行比对
#CMD ["python", "./manage.py", "runserver", "0.0.0.0:8080"]






