# CDN 静态资源加速配置指南

## 一、CDN 概述

CDN（Content Delivery Network）内容分发网络可以加速静态资源的访问速度，提升用户体验。

### 适用场景
- 前端静态资源（JS、CSS、图片、字体）
- 用户上传的文件
- 公共资源库

---

## 二、推荐 CDN 服务商

| 服务商 | 适用场景 | 免费额度 |
|--------|---------|---------|
| 阿里云 CDN | 国内用户 | 按量付费 |
| 腾讯云 CDN | 国内用户 | 按量付费 |
| 七牛云 | 静态资源 | 每月 10GB |
| 又拍云 | 静态资源 | 按量付费 |
| Cloudflare | 海外用户 | 免费套餐 |

---

## 三、前端配置

### 3.1 Vite 配置（推荐）

修改 `frontend/vite.config.js`：

```javascript
export default defineConfig({
  base: 'https://your-cdn-domain.com/',
  build: {
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        assetFileNames: 'assets/[name]-[hash][extname]',
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js'
      }
    }
  }
})
```

### 3.2 Vue Router 配置

修改 `frontend/src/router/index.js`：

```javascript
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  // ... 其他配置
})
```

### 3.3 静态资源引用

```javascript
// 使用 CDN 加载第三方库
// 在 index.html 中添加：
<script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>
<script src="https://cdn.jsdelivr.net/npm/element-plus/dist/index.full.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
```

---

## 四、Nginx 配置

### 4.1 静态资源缓存

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options "nosniff";
    }
    
    # HTML 不缓存
    location ~* \.html$ {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
```

### 4.2 CDN 回源配置

```nginx
# 配置 CDN 回源
location / {
    proxy_pass http://backend_server;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    
    # 静态资源走 CDN
    if ($request_uri ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$) {
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

---

## 五、阿里云 CDN 配置示例

### 5.1 控制台配置

1. 登录阿里云控制台
2. 进入 CDN 服务
3. 添加域名：
   - 加速域名：`cdn.your-domain.com`
   - 源站地址：`your-origin-server.com`
   - 业务类型：`图片小文件`

### 5.2 缓存规则配置

| 文件类型 | 缓存时间 |
|---------|---------|
| .js, .css | 30 天 |
| .png, .jpg, .gif, .ico | 30 天 |
| .woff, .woff2, .ttf | 365 天 |
| .html | 不缓存 |

### 5.3 HTTPS 配置

1. 上传 SSL 证书
2. 开启 HTTPS 加速
3. 开启 HTTP/2
4. 开启强制 HTTPS

---

## 六、Cloudflare 配置示例

### 6.1 基础配置

1. 添加站点到 Cloudflare
2. 更新域名 DNS 服务器
3. 开启 CDN 代理（橙色云朵）

### 6.2 Page Rules 配置

```
规则 1: *your-domain.com/assets/*
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 month

规则 2: *your-domain.com/*.html
- Cache Level: Bypass
```

### 6.3 Workers 脚本（可选）

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const cache = caches.default
  let response = await cache.match(request)
  
  if (!response) {
    response = await fetch(request)
    const headers = new Headers(response.headers)
    headers.set('Cache-Control', 'public, max-age=2592000')
    response = new Response(response.body, { ...response, headers })
    event.waitUntil(cache.put(request, response.clone()))
  }
  
  return response
}
```

---

## 七、性能监控

### 7.1 关键指标

| 指标 | 目标值 |
|------|--------|
| 首字节时间 (TTFB) | < 200ms |
| 资源加载时间 | < 500ms |
| 缓存命中率 | > 90% |
| 可用性 | > 99.9% |

### 7.2 监控工具

- 阿里云 CDN 监控
- Cloudflare Analytics
- Google PageSpeed Insights
- WebPageTest

---

## 八、注意事项

1. **缓存更新**：发布新版本时需要刷新 CDN 缓存
2. **版本控制**：使用文件哈希命名避免缓存问题
3. **HTTPS**：确保 CDN 支持 HTTPS
4. **跨域**：配置 CORS 头允许跨域访问
5. **回源**：合理配置回源策略避免源站压力

---

*文档版本：v1.0*
*创建日期：2026-02-21*
