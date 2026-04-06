<template>
  <div class="favorites-page">
    <div class="page-header">
      <h2>
        <el-icon><Star /></el-icon>
        我的收藏
      </h2>
      <span class="total-count">共 {{ total }} 篇</span>
    </div>

    <div
      v-if="loading"
      class="loading-container"
    >
      <el-skeleton
        :rows="5"
        animated
      />
    </div>

    <template v-else>
      <div
        v-if="favorites.length === 0"
        class="empty-state"
      >
        <el-empty description="暂无收藏内容">
          <el-button
            type="primary"
            @click="$router.push('/article-analysis')"
          >
            去浏览文章
          </el-button>
        </el-empty>
      </div>

      <div
        v-else
        class="favorites-list"
      >
        <div
          v-for="item in favorites"
          :key="item.id"
          class="favorite-card"
        >
          <div class="card-content">
            <p class="article-text">
              {{ truncate(item.content, 200) }}
            </p>
            <div class="card-meta">
              <span
                v-if="item.source"
                class="source"
              >
                <el-icon><User /></el-icon> {{ item.source }}
              </span>
              <span class="time">
                <el-icon><Calendar /></el-icon> {{ item.created_at }}
              </span>
              <div class="stats">
                <span><el-icon><Star /></el-icon> {{ item.like_num }}</span>
                <span><el-icon><ChatDotRound /></el-icon> {{ item.comment_num }}</span>
                <span><el-icon><Share /></el-icon> {{ item.forward_num }}</span>
              </div>
            </div>
          </div>
          <div class="card-actions">
            <el-button
              type="danger"
              text
              size="small"
              :loading="removingId === item.article_id"
              @click="handleRemove(item.article_id)"
            >
              <el-icon><Delete /></el-icon> 取消收藏
            </el-button>
          </div>
        </div>
      </div>

      <div
        v-if="total > pageSize"
        class="pagination-container"
      >
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadFavorites"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Star, User, Calendar, ChatDotRound, Share, Delete } from '@element-plus/icons-vue'
  import { getFavorites, removeFavorite } from '@/api/favorites'

  const favorites = ref([])
  const total = ref(0)
  const loading = ref(true)
  const currentPage = ref(1)
  const pageSize = 10
  const removingId = ref(null)

  const truncate = (text, len) => {
    if (!text) return '(无内容)'
    return text.length > len ? text.slice(0, len) + '...' : text
  }

  const loadFavorites = async (page) => {
    if (page) currentPage.value = page
    loading.value = true
    try {
      const res = await getFavorites({ page: currentPage.value, limit: pageSize })
      if (res.code === 200) {
        favorites.value = res.data.items || []
        total.value = res.data.total || 0
      }
    } catch (error) {
      ElMessage.error('加载收藏列表失败')
    } finally {
      loading.value = false
    }
  }

  const handleRemove = async (articleId) => {
    removingId.value = articleId
    try {
      const res = await removeFavorite(articleId)
      if (res.code === 200) {
        ElMessage.success('已取消收藏')
        favorites.value = favorites.value.filter((f) => f.article_id !== articleId)
        total.value = Math.max(0, total.value - 1)
      } else {
        ElMessage.error(res.msg || '操作失败')
      }
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      removingId.value = null
    }
  }

  onMounted(() => {
    loadFavorites()
  })
</script>

<style lang="scss" scoped>
  .favorites-page {
    max-width: 900px;
    margin: 0 auto;
  }

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;

    h2 {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 22px;
      font-weight: 700;
      color: $text-primary;
      margin: 0;
    }

    .total-count {
      font-size: 14px;
      color: $text-secondary;
    }
  }

  .loading-container {
    padding: 24px;
    background: $surface-color;
    border-radius: $border-radius-large;
  }

  .favorites-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .favorite-card {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    padding: 20px 24px;
    background: $surface-color;
    border-radius: $border-radius-large;
    box-shadow: $box-shadow-base;
    transition: all 0.2s ease;

    &:hover {
      box-shadow: $box-shadow-hover;
      transform: translateY(-1px);
    }

    .card-content {
      flex: 1;
      min-width: 0;
    }

    .article-text {
      font-size: 14px;
      line-height: 1.7;
      color: $text-primary;
      margin: 0 0 12px;
      word-break: break-word;
    }

    .card-meta {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      font-size: 12px;
      color: $text-secondary;

      span {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .stats {
        display: flex;
        gap: 12px;
        margin-left: auto;
      }
    }

    .card-actions {
      flex-shrink: 0;
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    margin-top: 24px;
  }

  .empty-state {
    padding: 60px 0;
  }

  @media (max-width: 640px) {
    .favorite-card {
      flex-direction: column;
      gap: 12px;

      .card-meta .stats {
        margin-left: 0;
      }
    }
  }
</style>
