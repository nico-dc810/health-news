# 腾讯云轻量服务器部署

这套部署用于第一版 MVP：一台腾讯云轻量服务器同时运行前端、后端、PostgreSQL 和 HTTPS 入口。

## 服务器要求

- 地域：建议中国香港，前期可免备案验证产品。
- 镜像：Docker CE 应用模板，或 Ubuntu 后自行安装 Docker。
- 防火墙：开放 22、80、443。

## 首次部署

```bash
git clone https://github.com/nico-dc810/health-news.git
cd health-news/deploy/tencent
cp .env.example .env
```

编辑 `.env`：

- `DOMAIN`：你的域名，例如 `example.com`。
- `ACME_EMAIL`：HTTPS 证书通知邮箱。
- `POSTGRES_PASSWORD`：数据库密码。
- `DATABASE_URL`：把其中的数据库密码改成和 `POSTGRES_PASSWORD` 一致。
- `SECRET_KEY`：登录 Token 签名密钥。
- `ADMIN_API_KEY`：管理员手动开通会员的密钥。
- `CORS_ORIGINS`：改成你的正式域名。

启动：

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f app
```

验证：

```bash
curl https://你的域名/api/auth/payment-config
```

## 管理员开通手机号

用户付款后，使用管理员密钥开通：

```bash
curl -X POST https://你的域名/api/auth/demo-activate \
  -H "Content-Type: application/json" \
  -H "X-Admin-Api-Key: 你的_ADMIN_API_KEY" \
  -d '{"phone":"13800138000"}'
```

开通后用户在网页输入手机号即可进入平台。

## 更新代码

```bash
cd health-news
git pull
cd deploy/tencent
docker compose up -d --build
```

## 备份数据库

```bash
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup.sql
```

