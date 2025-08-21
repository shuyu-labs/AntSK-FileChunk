# 🐳 Docker 快速开始指南

本指南帮助您快速使用 Docker 运行 AntSK 语义文本切片服务。

## 🚀 一键启动

### 使用 Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/xuzeyu91/AntSK-FileChunk.git
cd AntSK-FileChunk

# 2. 一键启动
docker-compose up -d

# 3. 访问服务
# Web界面: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 使用 Makefile（更简单）

```bash
# 构建并启动
make start-docker

# 查看状态
make docker-status

# 查看日志
make docker-logs

# 停止服务
make docker-stop
```

## 🔧 开发环境

```bash
# 启动开发环境（支持代码热重载）
make docker-dev

# 或者使用 docker-compose
docker-compose -f docker-compose.dev.yml up -d
```

## 📊 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
{
  "status": "healthy",
  "service": "AntSK文件切片服务"
}
```

## 🛠️ 常用命令

```bash
# 查看所有可用命令
make help

# Docker 相关命令
make docker-build    # 构建镜像
make docker-run      # 启动生产环境
make docker-dev      # 启动开发环境
make docker-logs     # 查看日志
make docker-shell    # 进入容器
make docker-clean    # 清理资源
```

## 🔍 故障排除

### 端口被占用
```bash
# 查看端口占用
netstat -tlnp | grep :8000

# 修改端口
# 编辑 docker-compose.yml，将 "8000:8000" 改为 "8080:8000"
```

### 内存不足
```bash
# 查看容器资源使用
docker stats antsk-filechunk

# 如果内存不足，减少其他应用的使用或增加系统内存
```

### 容器启动失败
```bash
# 查看详细日志
docker logs antsk-filechunk

# 重新构建镜像
make docker-rebuild
```

## 📚 更多信息

- [完整 Docker 部署文档](docs/DOCKER_DEPLOYMENT.md)
- [API 使用文档](docs/API_README.md)
- [项目主文档](README.md)

## 🆘 获取帮助

遇到问题？
1. 查看 [故障排除文档](docs/DOCKER_DEPLOYMENT.md#故障排除)
2. 提交 [GitHub Issue](https://github.com/xuzeyu91/AntSK-FileChunk/issues)

---

**现在就开始使用 Docker 体验 AntSK 语义切片服务吧！** 🚀
