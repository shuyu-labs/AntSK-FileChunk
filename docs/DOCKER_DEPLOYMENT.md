# 🐳 Docker 部署指南

本文档详细介绍如何使用 Docker 部署 AntSK 语义文本切片服务。

## 📑 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [构建选项](#构建选项)
- [部署方式](#部署方式)
- [配置说明](#配置说明)
- [数据持久化](#数据持久化)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)

## 🔧 环境要求

### 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

### 推荐配置
- 8GB+ 内存（用于加载语义模型）
- SSD 存储（提升 I/O 性能）
- 多核 CPU（加速文档处理）

## 🚀 快速开始

### 1. 拉取源码
```bash
git clone https://github.com/xuzeyu91/AntSK-FileChunk.git
cd AntSK-FileChunk
```

### 2. 使用 Docker Compose（推荐）
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 直接使用 Docker
```bash
# 构建镜像
docker build -t antsk/filechunk:latest .

# 运行容器
docker run -d \
  --name antsk-filechunk \
  -p 8000:8000 \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/logs:/app/logs \
  antsk/filechunk:latest
```

### 4. 验证部署
```bash
# 健康检查
curl http://localhost:8000/health

# 访问 Web 界面
# http://localhost:8000

# 查看 API 文档
# http://localhost:8000/docs
```

## 🏗️ 构建选项

### 基础镜像构建
```bash
# 构建生产镜像
docker build -t antsk/filechunk:latest .

# 构建并指定标签
docker build -t antsk/filechunk:v1.0.0 .

# 查看镜像大小
docker images antsk/filechunk
```

### 多阶段构建（优化大小）
```dockerfile
# 在 Dockerfile 中可以添加多阶段构建
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "api_server.py"]
```

### 构建参数
```bash
# 使用构建参数
docker build \
  --build-arg PYTHON_VERSION=3.9 \
  --build-arg APP_ENV=production \
  -t antsk/filechunk:latest .
```

## 🚀 部署方式

### 1. 开发环境部署

使用开发版 compose 文件，支持代码热重载：

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看开发日志
docker-compose -f docker-compose.dev.yml logs -f antsk-filechunk-dev
```

### 2. 生产环境部署

#### 基础生产部署
```bash
# 使用生产配置启动
docker-compose --profile production up -d

# 包含 Nginx 反向代理
docker-compose --profile production up -d nginx antsk-filechunk
```

#### Kubernetes 部署
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: antsk-filechunk
  labels:
    app: antsk-filechunk
spec:
  replicas: 3
  selector:
    matchLabels:
      app: antsk-filechunk
  template:
    metadata:
      labels:
        app: antsk-filechunk
    spec:
      containers:
      - name: antsk-filechunk
        image: antsk/filechunk:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "info"
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: antsk-filechunk-service
spec:
  selector:
    app: antsk-filechunk
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Docker Swarm 部署
```yaml
# docker-stack.yml
version: '3.8'

services:
  antsk-filechunk:
    image: antsk/filechunk:latest
    ports:
      - "8000:8000"
    networks:
      - antsk-network
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

networks:
  antsk-network:
    driver: overlay
```

部署命令：
```bash
docker stack deploy -c docker-stack.yml antsk
```

### 3. 云平台部署

#### AWS ECS
```json
{
  "family": "antsk-filechunk",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "antsk-filechunk",
      "image": "antsk/filechunk:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "info"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/antsk-filechunk",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Azure Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name antsk-filechunk \
  --image antsk/filechunk:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables LOG_LEVEL=info \
  --restart-policy OnFailure
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_HOST` | `0.0.0.0` | 服务监听地址 |
| `APP_PORT` | `8000` | 服务监听端口 |
| `LOG_LEVEL` | `info` | 日志级别 |
| `PYTHONPATH` | `/app` | Python 路径 |
| `PYTHONUNBUFFERED` | `1` | 禁用 Python 输出缓冲 |
| `MAX_UPLOAD_SIZE` | `100MB` | 最大上传文件大小 |
| `WORKER_PROCESSES` | `1` | 工作进程数 |

### Docker Compose 配置示例

```yaml
version: '3.8'

services:
  antsk-filechunk:
    image: antsk/filechunk:latest
    container_name: antsk-filechunk
    ports:
      - "${APP_PORT:-8000}:8000"
    volumes:
      - "./temp:/app/temp"
      - "./logs:/app/logs"
      - "./config:/app/config:ro"
    environment:
      - APP_HOST=${APP_HOST:-0.0.0.0}
      - APP_PORT=${APP_PORT:-8000}
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - MAX_UPLOAD_SIZE=${MAX_UPLOAD_SIZE:-100MB}
      - WORKER_PROCESSES=${WORKER_PROCESSES:-1}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 配置文件挂载

```bash
# 创建配置目录
mkdir -p config

# 创建自定义配置文件
cat > config/app.conf << EOF
[server]
host = 0.0.0.0
port = 8000
workers = 2

[chunking]
default_chunk_size = 1000
default_overlap = 0.1
default_threshold = 0.7

[logging]
level = info
format = json
EOF

# 挂载配置文件
docker run -v $(pwd)/config:/app/config:ro antsk/filechunk:latest
```

## 💾 数据持久化

### 卷挂载策略

```yaml
services:
  antsk-filechunk:
    volumes:
      # 临时文件目录（处理上传文件）
      - "./temp:/app/temp"
      
      # 日志目录
      - "./logs:/app/logs"
      
      # 配置目录（只读）
      - "./config:/app/config:ro"
      
      # 模型缓存目录（可选）
      - "./models:/app/models"
      
      # 用户数据目录（如果需要）
      - "./data:/app/data"
```

### 数据备份

```bash
# 备份脚本
#!/bin/bash
BACKUP_DIR="/backup/antsk-filechunk/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份配置和数据
docker cp antsk-filechunk:/app/config "$BACKUP_DIR/"
docker cp antsk-filechunk:/app/logs "$BACKUP_DIR/"
docker cp antsk-filechunk:/app/data "$BACKUP_DIR/" 2>/dev/null || true

# 压缩备份
tar -czf "$BACKUP_DIR.tar.gz" -C "$BACKUP_DIR" .
rm -rf "$BACKUP_DIR"

echo "备份完成: $BACKUP_DIR.tar.gz"
```

### 数据恢复

```bash
# 恢复脚本
#!/bin/bash
BACKUP_FILE="$1"
TEMP_DIR="/tmp/antsk-restore"

# 解压备份
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# 停止服务
docker-compose down

# 恢复数据
cp -r "$TEMP_DIR/config" ./
cp -r "$TEMP_DIR/logs" ./
cp -r "$TEMP_DIR/data" ./ 2>/dev/null || true

# 启动服务
docker-compose up -d

# 清理临时文件
rm -rf "$TEMP_DIR"

echo "恢复完成"
```

## 📊 监控和日志

### 日志管理

#### 日志配置
```yaml
services:
  antsk-filechunk:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
        labels: "service=antsk-filechunk"
```

#### 查看日志
```bash
# 查看实时日志
docker-compose logs -f antsk-filechunk

# 查看最近日志
docker-compose logs --tail=100 antsk-filechunk

# 查看特定时间段日志
docker logs --since="2024-01-01T00:00:00" --until="2024-01-02T00:00:00" antsk-filechunk
```

#### 日志轮转
```bash
# 配置 logrotate
cat > /etc/logrotate.d/docker-antsk << EOF
/var/lib/docker/containers/*/*-json.log {
    rotate 7
    daily
    compress
    size=100M
    missingok
    delaycompress
    copytruncate
}
EOF
```

### 监控集成

#### Prometheus 监控
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'antsk-filechunk'
    static_configs:
      - targets: ['antsk-filechunk:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

#### Grafana 仪表板
```json
{
  "dashboard": {
    "title": "AntSK FileChunk Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 健康检查

#### 内置健康检查
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

#### 自定义健康检查
```python
# health_check.py
import requests
import sys

def check_health():
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                return 0
    except Exception as e:
        print(f"Health check failed: {e}")
    return 1

if __name__ == "__main__":
    sys.exit(check_health())
```

## 🛠️ 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 查看容器日志
docker logs antsk-filechunk

# 常见原因：
# - 端口被占用
# - 内存不足
# - 依赖包安装失败
```

#### 2. 服务无法访问
```bash
# 检查端口映射
docker port antsk-filechunk

# 检查防火墙设置
sudo ufw status
sudo iptables -L

# 检查服务状态
curl -v http://localhost:8000/health
```

#### 3. 文件上传失败
```bash
# 检查磁盘空间
df -h

# 检查临时目录权限
ls -la temp/

# 检查文件大小限制
# 修改 docker-compose.yml 中的环境变量
```

#### 4. 内存不足
```bash
# 查看容器资源使用
docker stats antsk-filechunk

# 调整内存限制
docker-compose up -d --memory=4g antsk-filechunk
```

### 调试技巧

#### 进入容器调试
```bash
# 进入运行中的容器
docker exec -it antsk-filechunk bash

# 查看进程状态
ps aux

# 查看文件系统
ls -la /app/

# 测试网络连接
curl localhost:8000/health
```

#### 开启调试模式
```yaml
services:
  antsk-filechunk:
    environment:
      - LOG_LEVEL=debug
      - PYTHONUNBUFFERED=1
    command: ["python", "-u", "api_server.py"]
```

### 性能优化

#### 资源限制
```yaml
services:
  antsk-filechunk:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### 多副本部署
```yaml
services:
  antsk-filechunk:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
```

#### 负载均衡
```nginx
# nginx.conf
upstream antsk_backend {
    server antsk-filechunk-1:8000;
    server antsk-filechunk-2:8000;
    server antsk-filechunk-3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://antsk_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📚 相关文档

- [API 使用文档](API_README.md)
- [部署优化建议](优化建议.md)
- [语义切片算法详解](语义切片逻辑详解.md)
- [项目主文档](../README.md)

## 🆘 获取帮助

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查 [GitHub Issues](https://github.com/xuzeyu91/AntSK-FileChunk/issues)
3. 提交新的 Issue 并提供详细信息：
   - Docker 版本
   - 操作系统
   - 错误日志
   - 复现步骤

---

**祝您部署顺利！** 🚀
