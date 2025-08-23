# AntSK-FileChunk Docker 部署指南

本文档提供了 AntSK-FileChunk 项目的 Docker 容器化部署方案。

## 📁 Docker 相关文件

本项目包含以下 Docker 相关文件：

| 文件名 | 用途 | 说明 |
|--------|------|------|
| `Dockerfile` | Docker 镜像构建文件 | 定义了容器环境和依赖 |
| `.dockerignore` | Docker 构建忽略文件 | 排除不必要的文件，减小镜像大小 |
| `docker-compose.yml` | Docker Compose 配置 | 定义服务编排和网络配置 |
| `docker-start.sh` | Linux/Mac 启动脚本 | 自动化 Docker 部署脚本 |
| `docker-start.bat` | Windows 启动脚本 | Windows 环境下的部署脚本 |
| `examples/docker_test.py` | 部署测试脚本 | 验证 Docker 部署是否成功 |
| `docs/DOCKER_DEPLOYMENT.md` | 详细部署文档 | 完整的部署指南和故障排除 |

## 🚀 快速开始


### 方式一：使用 Docker Compose

```bash
# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f antsk-filechunk
```

### 方式二：直接使用 Docker

```bash
# 构建镜像
docker build -t antsk-filechunk:latest .

# 运行容器
docker run -d \
  --name antsk-filechunk \
  -p 8000:8000 \
  -v $(pwd)/temp:/app/temp \
  antsk-filechunk:latest
```

## 🔧 服务管理

### 启动脚本命令

```bash
# 查看帮助
./docker-start.sh --help

# 查看服务状态
./docker-start.sh --status

# 查看日志
./docker-start.sh --logs

# 重启服务
./docker-start.sh --restart

# 停止服务
./docker-start.sh --stop

# 重新构建并启动
./docker-start.sh --build
```

### Docker Compose 命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 重新构建
docker-compose build --no-cache
```

## 🧪 部署测试

部署完成后，运行测试脚本验证服务是否正常：

```bash
# 运行测试脚本
python examples/docker_test.py

# 或指定自定义服务地址
python examples/docker_test.py http://your-server:8000
```

测试脚本会验证以下功能：
- ✅ 健康检查接口
- ✅ 默认配置获取
- ✅ 文本处理功能
- ✅ 文件上传处理
- ✅ Web 界面访问

## 🌐 访问服务

服务启动后，可以通过以下地址访问：

- **Web 界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📊 容器配置

### 默认配置

- **端口映射**: 8000:8000
- **工作目录**: /app
- **Python 版本**: 3.9
- **基础镜像**: python:3.9-slim

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PYTHONPATH` | `/app` | Python 路径 |
| `PYTHONUNBUFFERED` | `1` | 禁用 Python 输出缓冲 |
| `LOG_LEVEL` | `info` | 日志级别 |

### 卷挂载

| 容器路径 | 主机路径 | 用途 |
|----------|----------|------|
| `/app/temp` | `./temp` | 临时文件存储 |
| `/app/config` | `./config` | 配置文件 |
| `/app/static` | `./static` | 静态文件 |

## 🛠️ 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep 8000
   # 或使用其他端口
   docker run -p 8080:8000 antsk-filechunk:latest
   ```

2. **容器启动失败**
   ```bash
   # 查看容器日志
   docker logs antsk-filechunk
   # 或
   docker-compose logs antsk-filechunk
   ```

3. **服务无法访问**
   ```bash
   # 检查容器状态
   docker ps
   # 检查健康状态
   curl http://localhost:8000/health
   ```

4. **内存不足**
   ```bash
   # 限制容器内存使用
   docker run -m 4g antsk-filechunk:latest
   ```

### 调试模式

```bash
# 以交互模式启动容器
docker run -it --rm -p 8000:8000 antsk-filechunk:latest /bin/bash

# 进入运行中的容器
docker exec -it antsk-filechunk /bin/bash
```

## 📈 生产环境建议

1. **使用 Nginx 反向代理**
   ```bash
   docker-compose --profile with-nginx up -d
   ```

2. **配置资源限制**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ```

3. **启用健康检查**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

4. **数据持久化**
   ```bash
   # 使用命名卷
   docker volume create antsk-data
   docker run -v antsk-data:/app/temp antsk-filechunk:latest
   ```

## 📞 获取帮助

如果遇到问题，请：

1. 查看 [详细部署文档](docs/DOCKER_DEPLOYMENT.md)
2. 运行测试脚本诊断问题
3. 检查容器日志
4. 提交 [GitHub Issue](https://github.com/xuzeyu91/AntSK-FileChunk/issues)

---

**注意**: 首次启动可能需要下载模型文件，请耐心等待。建议在生产环境中预先构建包含模型的镜像。
