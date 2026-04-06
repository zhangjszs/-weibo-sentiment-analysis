<template>
  <div class="breadcrumb-nav">
    <el-breadcrumb :separator-icon="ArrowRight">
      <el-breadcrumb-item :to="{ path: '/' }">
        <el-icon><HomeFilled /></el-icon>
        首页
      </el-breadcrumb-item>
      <el-breadcrumb-item
        v-for="(item, index) in breadcrumbs"
        :key="index"
      >
        <span v-if="item.path">
          <router-link :to="item.path">{{ item.title }}</router-link>
        </span>
        <span v-else>{{ item.title }}</span>
      </el-breadcrumb-item>
    </el-breadcrumb>
  </div>
</template>

<script setup>
  import { ArrowRight, HomeFilled } from '@element-plus/icons-vue'

  defineProps({
    breadcrumbs: {
      type: Array,
      default: () => [],
    },
  })
</script>

<style lang="scss" scoped>
  .breadcrumb-nav {
    margin-bottom: 20px;
    padding: 16px 20px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);

    :deep(.el-breadcrumb) {
      font-size: 14px;

      .el-breadcrumb__inner {
        display: flex;
        align-items: center;
        gap: 4px;

        &.is-link:hover {
          color: #005aa0;
        }
      }

      .el-breadcrumb__item:last-child .el-breadcrumb__inner {
        color: #909399;
      }
    }
  }
</style>
