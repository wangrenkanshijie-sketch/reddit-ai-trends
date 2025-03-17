FROM python:3.9-slim

WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建报告目录
RUN mkdir -p reports

# 设置时区为美国中部时间
ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行报告生成脚本
CMD ["python", "report_generation.py", "--schedule", "--interval", "24"]
