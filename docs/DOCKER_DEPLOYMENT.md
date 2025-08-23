# Docker 部署指南

本文档详细介绍如何使用 Docker 部署 AntSK-FileChunk 语义文本切片服务。

## 📋 目录

- [快速开始](#快速开始)
- [构建选项](#构建选项)
- [部署方式](#部署方式)
- [配置说明](#配置说明)
- [监控与维护](#监控与维护)
- [故障排除](#故障排除)

## 🚀 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/xuzeyu91/AntSK-FileChunk.git
cd AntSK-FileChunk

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 访问服务
# Web界面: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 方式二：直接使用 Docker

```bash
# 1. 构建镜像
docker build -t antsk-filechunk:latest .

# 2. 运行容器
docker run -d \
  --name antsk-filechunk \
  -p 8000:8000 \
  -v $(pwd)/temp:/app/temp \
  antsk-filechunk:latest

# 3. 查看容器状态
docker ps
```

## 🔧 构建选项

### 基础构建

```bash
# 构建基础镜像
docker build -t antsk-filechunk:latest .
```

### 自定义构建参数

```bash
# 指定 Python 版本
docker build --build-arg PYTHON_VERSION=3.9 -t antsk-filechunk:python39 .

# 构建开发版本（包含开发工具）
docker build --target development -t antsk-filechunk:dev .
```

### 多阶段构建优化

```dockerfile
# 在 Dockerfile 中添加多阶段构建
FROM python:3.9-slim as base
# ... 基础配置

FROM base as development
# 安装开发依赖
RUN pip install pytest black flake8 mypy

FROM base as production
# 生产环境配置
```

## 🚢 部署方式

### 1. 单容器部署

适用于开发环境和小规模部署：

```bash
docker run -d \
  --name antsk-filechunk \
  --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/config:/app/config \
  -e LOG_LEVEL=info \
  antsk-filechunk:latest
```

### 2. Docker Compose 部署

适用于生产环境，支持服务编排：

```yaml
# docker-compose.yml
version: '3.8'
services:
  antsk-filechunk:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./temp:/app/temp
      - ./config:/app/config
    environment:
      - LOG_LEVEL=info
    restart: unless-stopped
```

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f antsk-filechunk

# 停止服务
docker-compose down
```

### 3. 带 Nginx 反向代理部署

适用于生产环境，提供负载均衡和 SSL 终止：

```bash
# 启动包含 Nginx 的完整服务
docker-compose --profile with-nginx up -d
```

### 4. 集群部署

使用 Docker Swarm 或 Kubernetes 进行集群部署：

```bash
# Docker Swarm 示例
docker swarm init
docker stack deploy -c docker-compose.yml antsk-stack
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PYTHONPATH` | `/app` | Python 路径 |
| `PYTHONUNBUFFERED` | `1` | Python 输出缓冲 |
| `LOG_LEVEL` | `info` | 日志级别 |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8000` | 服务端口 |

### 卷挂载配置

```bash
# 临时文件目录（必需）
-v $(pwd)/temp:/app/temp

# 配置文件目录（可选）
-v $(pwd)/config:/app/config

# 静态文件目录（可选）
-v $(pwd)/static:/app/static

# 日志目录（可选）
-v $(pwd)/logs:/app/logs
```

### 网络配置

```yaml
# 自定义网络
networks:
  antsk-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 📊 监控与维护

### 健康检查

容器内置健康检查机制：

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' antsk-filechunk

# 手动健康检查
curl -f http://localhost:8000/health
```

### 日志管理

```bash
# 查看实时日志
docker logs -f antsk-filechunk

# 查看最近 100 行日志
docker logs --tail 100 antsk-filechunk

# 使用 docker-compose 查看日志
docker-compose logs -f antsk-filechunk
```

### 性能监控

```bash
# 查看容器资源使用情况
docker stats antsk-filechunk

# 查看容器详细信息
docker inspect antsk-filechunk
```

### 数据备份

```bash
# 备份临时文件
docker run --rm -v antsk_temp:/data -v $(pwd):/backup alpine tar czf /backup/temp_backup.tar.gz -C /data .

# 恢复临时文件
docker run --rm -v antsk_temp:/data -v $(pwd):/backup alpine tar xzf /backup/temp_backup.tar.gz -C /data
```

## 🔄 更新与维护

### 更新镜像

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker build -t antsk-filechunk:latest .

# 3. 停止旧容器
docker-compose down

# 4. 启动新容器
docker-compose up -d

# 5. 清理旧镜像
docker image prune -f
```

### 滚动更新

```bash
# 使用 docker-compose 进行滚动更新
docker-compose up -d --no-deps --build antsk-filechunk
```

## 🛠️ 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看启动日志
docker logs antsk-filechunk

# 检查端口占用
netstat -tlnp | grep 8000

# 检查磁盘空间
df -h
```

#### 2. 服务无法访问

```bash
# 检查容器状态
docker ps -a

# 检查网络连接
docker exec antsk-filechunk curl -f http://localhost:8000/health

# 检查防火墙设置
sudo ufw status
```

#### 3. 内存不足

```bash
# 查看内存使用
docker stats --no-stream

# 限制容器内存使用
docker run -m 4g antsk-filechunk:latest
```

#### 4. 文件权限问题

```bash
# 修复文件权限
sudo chown -R $(id -u):$(id -g) temp/
sudo chmod -R 755 temp/
```

### 调试模式

```bash
# 以调试模式启动容器
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd)/temp:/app/temp \
  -e LOG_LEVEL=debug \
  antsk-filechunk:latest

# 进入容器调试
docker exec -it antsk-filechunk /bin/bash
```

### 性能优化

#### 1. 资源限制

```yaml
# docker-compose.yml
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

#### 2. 缓存优化

```dockerfile
# 在 Dockerfile 中优化缓存
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

#### 3. 多阶段构建

```dockerfile
# 减小镜像大小
FROM python:3.9-slim as builder
# 构建阶段

FROM python:3.9-slim as runtime
# 运行阶段
COPY --from=builder /app /app
```

## 📈 生产环境建议

### 安全配置

1. **使用非 root 用户运行**
```dockerfile
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

2. **限制容器权限**
```bash
docker run --user 1000:1000 --read-only antsk-filechunk:latest
```

3. **使用 secrets 管理敏感信息**
```yaml
secrets:
  api_key:
    file: ./secrets/api_key.txt
```

### 高可用配置

1. **多实例部署**
```yaml
services:
  antsk-filechunk:
    deploy:
      replicas: 3
```

2. **负载均衡**
```nginx
upstream antsk_backend {
    server antsk-filechunk-1:8000;
    server antsk-filechunk-2:8000;
    server antsk-filechunk-3:8000;
}
```

3. **健康检查和自动重启**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
restart: unless-stopped
```

## 📞 支持与反馈

如果在 Docker 部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查 [GitHub Issues](https://github.com/xuzeyu91/AntSK-FileChunk/issues)
3. 提交新的 Issue 并提供详细的错误信息和环境描述

---

**注意**：本文档会随着项目更新而持续完善，建议定期查看最新版本。