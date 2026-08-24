<template>
  <div class="tasks-page">
    <TaskProgress
      :spider-overview="spiderOverview"
      :startup-status="startupStatus"
      :startup-warmup="startupWarmup"
      :warmup-progress="warmupProgress"
      :warmup-progress-status="warmupProgressStatus"
      :warmup-tag-type="warmupTagType"
      :warmup-status-text="warmupStatusText"
      :admin-bootstrap-type="adminBootstrapType"
      :admin-bootstrap-text="adminBootstrapText"
      :spider-loading="spiderLoading"
      :startup-loading="startupLoading"
      @refresh-spider="refreshSpider"
      @refresh-startup="refreshStartup"
    />

    <TaskList
      :spider-history="spiderHistory"
      :logs="logs"
      :logs-loading="logsLoading"
      :log-lines="logLines"
      :startup-warmup-results="startupWarmupResults"
      :task-id="taskId"
      :task-loading="taskLoading"
      :task-result="taskResult"
      :recent-tasks="recentTasks"
      @update:log-lines="val => logLines = val"
      @update:task-id="val => taskId = val"
      @refresh-logs="refreshLogs"
      @query-task="queryTask"
      @clear-recent="clearRecent"
      @remove-recent="removeRecent"
      @select-recent="selectRecent"
    />
  </div>
</template>

<script setup>
import TaskProgress from '@/components/system/TaskProgress.vue'
import TaskList from '@/components/system/TaskList.vue'
import { useTasks } from '@/composables/useTasks'
const { spiderLoading, startupLoading, logsLoading, taskLoading, spiderOverview, startupStatus, logs, logLines, taskId, taskResult, recentTasks, spiderHistory, startupWarmup, startupWarmupResults, warmupProgress, warmupProgressStatus, warmupTagType, warmupStatusText, adminBootstrapType, adminBootstrapText, refreshSpider, refreshLogs, refreshStartup, removeRecent, clearRecent, selectRecent, queryTask } = useTasks()
</script>

<style lang="scss" scoped src="./tasks.scss"></style>
