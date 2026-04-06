import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  ChatDotRound,
  ChatLineRound,
  Cloudy,
  Connection,
  Cpu,
  DataAnalysis,
  Document,
  HomeFilled,
  Location,
  Monitor,
  QuestionFilled,
  Share,
  Star,
  Tickets,
  TrendCharts,
  User,
} from '@element-plus/icons-vue'
import { useTabsStore } from '@/stores/tabs'
import { clearSessionState, getAuthToken, setCachedUser } from '@/utils/authSession'

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
        meta: { title: '首页', icon: HomeFilled },
      },
      {
        path: 'hot-words',
        name: 'HotWords',
        component: () => import('@/views/analysis/hotWords.vue'),
        meta: { title: '热词统计', icon: DataAnalysis },
      },
      {
        path: 'weibo-stats',
        name: 'WeiboStats',
        component: () => import('@/views/analysis/weiboStats.vue'),
        meta: { title: '微博舆情统计', icon: ChatLineRound },
      },
      {
        path: 'article-analysis',
        name: 'ArticleAnalysis',
        component: () => import('@/views/analysis/article.vue'),
        meta: { title: '文章分析', icon: Document },
      },
      {
        path: 'ip-analysis',
        name: 'IPAnalysis',
        component: () => import('@/views/analysis/ip.vue'),
        meta: { title: 'IP分析', icon: Location },
      },
      {
        path: 'comment-analysis',
        name: 'CommentAnalysis',
        component: () => import('@/views/analysis/comment.vue'),
        meta: { title: '评论分析', icon: ChatDotRound },
      },
      {
        path: 'sentiment-analysis',
        name: 'SentimentAnalysis',
        component: () => import('@/views/analysis/sentiment.vue'),
        meta: { title: '舆情分析', icon: TrendCharts },
      },
      {
        path: 'predict',
        name: 'ContentPredict',
        component: () => import('@/views/analysis/predict.vue'),
        meta: { title: '内容预测', icon: Cpu },
      },
      {
        path: 'propagation',
        name: 'PropagationAnalysis',
        component: () => import('@/views/analysis/propagation.vue'),
        meta: { title: '传播分析', icon: Share },
      },
      {
        path: 'word-cloud',
        name: 'WordCloud',
        component: () => import('@/views/analysis/wordCloud.vue'),
        meta: { title: '词云图', icon: Cloudy },
      },
      {
        path: 'spider',
        name: 'SpiderManager',
        component: () => import('@/views/analysis/spider.vue'),
        meta: { title: '爬虫管理', icon: Monitor, adminOnly: true },
      },
      {
        path: 'alert-center',
        name: 'AlertCenter',
        component: () => import('@/views/alert/center.vue'),
        meta: { title: '预警中心', icon: Bell },
      },
      {
        path: 'report',
        name: 'ReportGenerator',
        component: () => import('@/views/system/report.vue'),
        meta: { title: '报告生成', icon: Document },
      },
      {
        path: 'big-screen',
        name: 'BigScreen',
        component: () => import('@/views/dashboard/BigScreen.vue'),
        meta: { title: '数据大屏', icon: Monitor },
      },
      {
        path: 'platform-monitor',
        name: 'PlatformMonitor',
        component: () => import('@/views/analysis/platform.vue'),
        meta: { title: '多平台监测', icon: Connection },
      },
      {
        path: 'tasks',
        name: 'TaskCenter',
        component: () => import('@/views/system/tasks.vue'),
        meta: { title: '任务中心', icon: Tickets, adminOnly: true },
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/user/Profile.vue'),
        meta: { title: '个人中心', icon: User },
      },
      {
        path: 'favorites',
        name: 'UserFavorites',
        component: () => import('@/views/user/Favorites.vue'),
        meta: { title: '我的收藏', icon: Star },
      },
      {
        path: 'help',
        name: 'Help',
        component: () => import('@/views/system/Help.vue'),
        meta: { title: '帮助中心', icon: QuestionFilled },
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

const buildAuthHeaders = () => {
  const headers = {
    Accept: 'application/json',
  }

  const token = getAuthToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return headers
}

const fetchCurrentUser = async () => {
  try {
    const response = await fetch('/api/auth/me', {
      method: 'GET',
      credentials: 'include',
      headers: buildAuthHeaders(),
    })

    if (!response.ok) {
      return null
    }

    const payload = await response.json()
    if (!payload || payload.code !== 200) {
      return null
    }

    return payload.data || null
  } catch (error) {
    return null
  }
}

router.beforeEach(async (to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 微博舆情分析系统`
  }

  const whiteList = ['/login', '/register', '/404', '/403', '/500']
  if (whiteList.includes(to.path)) {
    next()
    return
  }

  const user = await fetchCurrentUser()
  if (!user) {
    clearSessionState()
    next(`/login?redirect=${to.fullPath}`)
    return
  }

  setCachedUser(user)

  if (to.meta.adminOnly) {
    if (user?.is_admin !== true) {
      ElMessage.warning('没有权限访问该页面')
      next('/home')
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
