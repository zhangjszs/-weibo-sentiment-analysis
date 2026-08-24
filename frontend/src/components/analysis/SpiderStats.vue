<template>
  <el-row
    :gutter="20"
    class="stats-row"
  >
    <el-col
      :xs="24"
      :sm="12"
      :md="6"
    >
      <div class="stat-card card-articles">
        <div class="stat-icon">
          <el-icon :size="28">
            <Document />
          </el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ overview.articleCount || 0 }}
          </div><div class="stat-label">
            文章总数
          </div>
        </div>
      </div>
    </el-col>
    <el-col
      :xs="24"
      :sm="12"
      :md="6"
    >
      <div class="stat-card card-comments">
        <div class="stat-icon">
          <el-icon :size="28">
            <ChatDotRound />
          </el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ overview.commentCount || 0 }}
          </div><div class="stat-label">
            评论总数
          </div>
        </div>
      </div>
    </el-col>
    <el-col
      :xs="24"
      :sm="12"
      :md="6"
    >
      <div class="stat-card card-users">
        <div class="stat-icon">
          <el-icon :size="28">
            <User />
          </el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ overview.userCount || 0 }}
          </div><div class="stat-label">
            用户总数
          </div>
        </div>
      </div>
    </el-col>
    <el-col
      :xs="24"
      :sm="12"
      :md="6"
    >
      <div class="stat-card card-time">
        <div class="stat-icon">
          <el-icon :size="28">
            <Timer />
          </el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value stat-time-value">
            {{ overview.latestArticleTime || '暂无' }}
          </div><div class="stat-label">
            最近采集
          </div>
        </div>
      </div>
    </el-col>
  </el-row>
</template>

<script setup>
import { Document, ChatDotRound, User, Timer } from '@element-plus/icons-vue'
defineProps({ overview: { type: Object, required: true } })
</script>
