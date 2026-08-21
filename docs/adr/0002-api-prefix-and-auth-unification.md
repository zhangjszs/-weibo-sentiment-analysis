# API 前缀与认证单轨化

` /getAllData/*`（legacy 数据直出）与 `/api/*` 双轨并存，且 `before_request` 对 `/page/*` 用 session、其余用 JWT+Origin 双层校验，导致三套前缀与双轨认证并存且 `frontend/src/api/*` 直连 legacy 前缀。决定一次性收敛到 `/api/*` 单前缀（过渡期保留 `/getAllData` 307 别名一版本），认证统一为 JWT 单轨（Bearer/cookie），`/page/*` 仅保留登录/注册页直出，其余鉴权交前端路由；并合并 `spider_api`/`spider_routes` 等同名蓝图为 `api` 单蓝图。
