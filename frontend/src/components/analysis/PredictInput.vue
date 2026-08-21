<template>
  <el-card class="input-card">
    <template #header>
      <div class="card-header">
        <span class="header-title">内容情感预测</span>
        <el-radio-group :model-value="predictMode" size="small" @update:model-value="emit('update:predictMode', $event)">
          <el-radio-button label="custom">自定义模型</el-radio-button>
          <el-radio-button label="smart">智能分析</el-radio-button>
          <el-radio-button label="simple">快速分析</el-radio-button>
        </el-radio-group>
      </div>
    </template>
    <el-form :model="predictForm" label-position="top">
      <el-form-item label="输入文本">
        <el-input :model-value="predictForm.text" type="textarea" :rows="4" placeholder="请输入需要分析的微博内容或评论文本..." maxlength="1000" show-word-limit @update:model-value="emit('update:predictForm', { ...predictForm, text: $event })" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="predicting" :disabled="!predictForm.text.trim()" @click="emit('predict')">
          <el-icon class="mr-1"><TrendCharts /></el-icon>开始预测
        </el-button>
        <el-button @click="emit('clear')">清空</el-button>
        <el-button type="success" plain @click="emit('openBatch')"><el-icon class="mr-1"><Upload /></el-icon>批量预测</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>
<script setup>
import { TrendCharts, Upload } from '@element-plus/icons-vue'
defineProps({ predictMode: String, predictForm: Object, predicting: Boolean })
const emit = defineEmits(['update:predictMode', 'update:predictForm', 'predict', 'clear', 'openBatch'])
</script>
