# 图片URL配置说明

## 问题说明

当文档中包含图片时,系统会提取图片并保存到 `static/images` 目录,然后在切片结果中生成图片的访问URL。

默认情况下,如果不配置图片URL,系统会使用 `localhost` 作为主机名,这会导致:
- ✅ 在本机访问时可以正常显示图片
- ❌ 在其他设备访问时无法加载图片

## 解决方案

### 方案1: 使用环境变量配置(推荐)

1. 创建 `.env` 文件(如果不存在):
```bash
cp env.template .env
```

2. 编辑 `.env` 文件,设置 `IMAGE_BASE_URL`:

**本地开发:**
```env
IMAGE_BASE_URL=http://localhost:8000
```

**局域网访问:**
```env
IMAGE_BASE_URL=http://192.168.1.100:8000
```
*(将 192.168.1.100 替换为您服务器的实际IP地址)*

**生产环境:**
```env
IMAGE_BASE_URL=https://your-domain.com
```

3. 重启服务

### 方案2: 自动检测(默认)

如果不设置 `IMAGE_BASE_URL` 环境变量,系统会自动从HTTP请求头中获取主机信息。

**工作原理:**
- 系统读取请求的 `Host` 头和 `scheme`(http/https)
- 自动构建图片URL: `{scheme}://{host}/static/images/{filename}`

**优点:**
- ✅ 无需手动配置
- ✅ 自适应不同访问方式(localhost、IP、域名)

**限制:**
- ⚠️ 需要确保客户端能访问到服务器的相应地址
- ⚠️ 反向代理需要正确传递Host头

## 示例

### 示例1: 本地开发

不设置环境变量,访问 `http://localhost:8000`,图片URL会自动生成为:
```
http://localhost:8000/static/images/xxxxx.png
```

### 示例2: 局域网访问

设置环境变量:
```env
IMAGE_BASE_URL=http://192.168.1.100:8000
```

无论从哪里访问,图片URL都会生成为:
```
http://192.168.1.100:8000/static/images/xxxxx.png
```

### 示例3: 生产环境(Nginx反向代理)

设置环境变量:
```env
IMAGE_BASE_URL=https://api.yourdomain.com
```

图片URL会生成为:
```
https://api.yourdomain.com/static/images/xxxxx.png
```

**Nginx配置示例:**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件直接访问
    location /static/ {
        alias /path/to/AntSK-FileChunk/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## 常见问题

### Q1: 图片显示404错误

**原因:** 图片URL指向的地址无法访问

**解决方法:**
1. 检查 `static/images` 目录是否存在且有读取权限
2. 检查防火墙是否允许访问端口
3. 验证 `IMAGE_BASE_URL` 配置是否正确

### Q2: 本地能访问,其他设备不能

**原因:** 使用了 `localhost` 作为主机名

**解决方法:**
设置 `IMAGE_BASE_URL` 为服务器的实际IP或域名

### Q3: Docker容器中如何配置

**docker-compose.yml 示例:**
```yaml
services:
  antsk-filechunk:
    image: antsk-filechunk:latest
    environment:
      - IMAGE_BASE_URL=http://your-server-ip:8000
    ports:
      - "8000:8000"
    volumes:
      - ./static:/app/static
```

### Q4: 使用CDN加速

如果图片较多,可以配置CDN:

1. 将 `static/images` 目录同步到CDN
2. 设置环境变量:
```env
IMAGE_BASE_URL=https://cdn.yourdomain.com
```

## 检查当前配置

启动服务后,查看日志输出:

```
🚀 启动 AntSK 文件切片服务...
============================================================
📖 本地访问: http://localhost:8000
🌐 局域网访问: http://192.168.1.100:8000
📚 API文档: http://192.168.1.100:8000/docs
============================================================
🖼️  图片URL: 自动检测 (当前: http://192.168.1.100:8000)
💡 提示: 如需从外网访问,请在环境变量中设置 IMAGE_BASE_URL
============================================================
```

## 总结

| 场景 | 推荐方案 | 配置示例 |
|------|---------|----------|
| 本地开发 | 自动检测 | 不设置环境变量 |
| 局域网访问 | 环境变量 | `IMAGE_BASE_URL=http://192.168.1.100:8000` |
| 生产环境 | 环境变量 | `IMAGE_BASE_URL=https://yourdomain.com` |
| Docker部署 | 环境变量 | 在docker-compose中配置 |
| CDN加速 | 环境变量 | `IMAGE_BASE_URL=https://cdn.yourdomain.com` |
