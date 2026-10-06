import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useTabsStore } from '@/stores/tabs'
import {
  clearSessionState,
  getAuthToken,
  getCachedCurrentUser,
  setCachedUser,
  setCachedCurrentUser,
} from '@/utils/authSession'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册', public: true },
  },
  {
    path: '/',
    component: () => import('@/components/Layout/index.vue'),
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/home/index.vue'),
        meta: { title: '话题分析', icon: 'HomeFilled', group: 'analysis' },
      },
      {
        path: 'sentiment-analysis',
        name: 'SentimentAnalysis',
        component: () => import('@/views/analysis/sentiment.vue'),
        meta: { title: '趋势/情感', icon: 'TrendCharts', group: 'analysis' },
      },
      {
        path: 'article-analysis',
        name: 'ArticleAnalysis',
        component: () => import('@/views/analysis/article.vue'),
        meta: { title: '文章分析', icon: 'Document', group: 'analysis' },
      },
      {
        path: 'comment-analysis',
        name: 'CommentAnalysis',
        component: () => import('@/views/analysis/comment.vue'),
        meta: { title: '评论分析', icon: 'ChatDotRound', group: 'analysis' },
      },
      {
        path: 'propagation',
        name: 'PropagationAnalysis',
        component: () => import('@/views/analysis/propagation.vue'),
        meta: { title: '传播分析', icon: 'Share', group: 'analysis' },
      },
      {
        path: 'report',
        name: 'ReportGenerator',
        component: () => import('@/views/system/report.vue'),
        meta: { title: '报告导出', icon: 'Document', group: 'analysis' },
      },
      // === 实验/运维功能 (lab) ===
      {
        path: 'hot-words',
        name: 'HotWords',
        component: () => import('@/views/analysis/hotWords.vue'),
        meta: { title: '热词统计', icon: 'DataAnalysis', group: 'lab' },
      },
      {
        path: 'weibo-stats',
        name: 'WeiboStats',
        component: () => import('@/views/analysis/weiboStats.vue'),
        meta: { title: '微博舆情统计', icon: 'ChatLineRound', group: 'lab' },
      },
      {
        path: 'ip-analysis',
        name: 'IPAnalysis',
        component: () => import('@/views/analysis/ip.vue'),
        meta: { title: 'IP分析', icon: 'Location', group: 'lab' },
      },
      {
        path: 'predict',
        name: 'ContentPredict',
        component: () => import('@/views/analysis/predict.vue'),
        meta: { title: '内容预测', icon: 'Cpu', group: 'lab' },
      },
      {
        path: 'word-cloud',
        name: 'WordCloud',
        component: () => import('@/views/analysis/wordCloud.vue'),
        meta: { title: '词云图', icon: 'Cloudy', group: 'lab' },
      },
      {
        path: 'spider',
        name: 'SpiderManager',
        component: () => import('@/views/analysis/spider.vue'),
        meta: { title: '爬虫管理', icon: 'Monitor', adminOnly: true, group: 'lab' },
      },
      {
        path: 'alert-center',
        name: 'AlertCenter',
        component: () => import('@/views/alert/center.vue'),
        meta: { title: '预警中心', icon: 'Bell', group: 'lab' },
      },
      {
        path: 'big-screen',
        name: 'BigScreen',
        component: () => import('@/views/dashboard/BigScreen.vue'),
        meta: { title: '数据大屏', icon: 'Monitor', group: 'lab' },
      },
      {
        path: 'platform-monitor',
        name: 'PlatformMonitor',
        component: () => import('@/views/analysis/platform.vue'),
        meta: { title: '多平台监测', icon: 'Connection', group: 'lab' },
      },
      {
        path: 'tasks',
        name: 'TaskCenter',
        component: () => import('@/views/system/tasks.vue'),
        meta: { title: '任务中心', icon: 'Tickets', adminOnly: true, group: 'lab' },
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/user/Profile.vue'),
        meta: { title: '个人中心', icon: 'User' },
      },
      {
        path: 'favorites',
        name: 'UserFavorites',
        component: () => import('@/views/user/Favorites.vue'),
        meta: { title: '我的收藏', icon: 'Star' },
      },
      {
        path: 'help',
        name: 'Help',
        component: () => import('@/views/system/Help.vue'),
        meta: { title: '帮助中心', icon: 'QuestionFilled' },
      },
    ],
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403.vue'),
    meta: { title: '403 - 访问被拒绝', public: true },
  },
  {
    path: '/500',
    name: 'ServerError',
    component: () => import('@/views/error/500.vue'),
    meta: { title: '500 - 服务器错误', public: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '404', public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫专用 axios 实例：不复用 @/api/request——后者 import 了本 router
// 模块（401 跳转用），会形成环。这里只做 me 查询：带超时与 Authorization，
// 401/网络错误统一按异常 → null（守卫按未登录处理）。
const meClient = axios.create({
  timeout: 8000,
  withCredentials: true,
})

const fetchCurrentUser = async () => {
  try {
    const headers = { Accept: 'application/json' }
    const token = getAuthToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const response = await meClient.get('/api/auth/me', { headers })
    const payload = response.data
    if (!payload || payload.code !== 200) {
      return null
    }

    return payload.data || null
  } catch {
    return null
  }
}

// /api/auth/me 结果的短 TTL：此前每次 beforeEach 都真实发请求，路由间
// 快速切换会放大 QPS（#19）。登出/401 走 clearSessionState 统一失效缓存。
const ME_CACHE_TTL_MS = 60 * 1000

router.beforeEach(async (to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 微博舆情分析系统`
  }

  // 404 是 catch-all 路由，to.path 是原始未匹配路径（如 /no-such-page），
  // 白名单 includes('/404') 永不命中——改为以 meta.public 判定，登录页与
  // 错误页（均标 public）一律放行，不再要求先登录才能看 404/403/500（#19）。
  const whiteList = ['/login', '/register', '/404', '/403', '/500']
  if (to.meta?.public || whiteList.includes(to.path)) {
    next()
    return
  }

  const cachedUser = getCachedCurrentUser(ME_CACHE_TTL_MS)
  const user = cachedUser || (await fetchCurrentUser())
  if (!user) {
    clearSessionState()
    next(`/login?redirect=${to.fullPath}`)
    return
  }
  if (!cachedUser) {
    setCachedCurrentUser(user)
    setCachedUser(user)
  }

  if (to.meta.adminOnly) {
    if (user?.is_admin !== true) {
      ElMessage.warning('没有权限访问该页面')
      // 跳 /403 而不是 /home：/home 对非管理员可进，用户会误以为权限没问题，
      // 403 页面从此成为死页面（#19）
      next('/403')
      return
    }
  }

  // Register tab for authenticated, non-error routes
  if (!to.meta?.public) {
    const tabsStore = useTabsStore()
    tabsStore.addTab(to)
  }
  next()
})

export default router
