import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import router from '@/router'
import { clearSessionState } from '@/utils/authSession'

const errorHandler = (error, vm, info) => {
  console.error('全局错误:', error)
  console.error('组件:', vm)
  console.error('信息:', info)

  if (error.response) {
    const { status, data } = error.response

    switch (status) {
      case 400:
        ElNotification.error({
          title: '请求错误',
          message: data?.msg || '请求参数错误',
        })
        break

      case 401:
        ElMessageBox.confirm('登录已过期，请重新登录', '登录过期', {
          confirmButtonText: '重新登录',
          cancelButtonText: '留在当前页',
          type: 'warning',
        }).then(() => {
          clearSessionState()
          router.push('/login')
        })
        break

      case 403:
        ElNotification.error({
          title: '访问拒绝',
          message: '您没有权限访问该资源',
        })
        break

      case 404:
        ElNotification.error({
          title: '资源未找到',
          message: '请求的资源不存在',
        })
        break

      case 422:
        ElNotification.warning({
          title: '数据验证失败',
          message: data?.msg || '请检查输入数据',
        })
        break

      case 429:
        ElNotification.warning({
          title: '请求过于频繁',
          message: '请稍后再试',
        })
        break

      case 500:
        ElNotification.error({
          title: '服务器错误',
          message: '服务暂时不可用，请稍后重试',
        })
        break

      default:
        ElNotification.error({
          title: '请求失败',
          message: data?.msg || '发生未知错误',
        })
    }
  } else if (error.request) {
    ElMessage.error('网络连接失败，请检查网络')
  } else {
    ElMessage.error('操作失败，请稍后重试')
  }
}

const setupErrorHandler = (app) => {
  app.config.errorHandler = errorHandler
}

export { errorHandler, setupErrorHandler }
