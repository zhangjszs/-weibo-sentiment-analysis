<template>
  <div class="analysis-filters">
    <el-form
      :inline="true"
      :model="form"
      @submit.prevent="emitSearch"
    >
      <el-form-item label="话题关键词">
        <el-input
          v-model="form.topic"
          placeholder="输入微博话题关键词..."
          clearable
          style="width: 240px"
          @keyup.enter="emitSearch"
        />
      </el-form-item>

      <el-form-item label="开始时间">
        <el-date-picker
          v-model="form.startAt"
          type="date"
          placeholder="开始日期"
          value-format="YYYY-MM-DD"
          style="width: 160px"
        />
      </el-form-item>

      <el-form-item label="结束时间">
        <el-date-picker
          v-model="form.endAt"
          type="date"
          placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 160px"
        />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :icon="Search"
          :disabled="!form.topic.trim()"
          @click="emitSearch"
        >
          开始分析
        </el-button>
      </el-form-item>

      <el-form-item v-if="showDemoToggle">
        <el-switch
          v-model="form.demo"
          active-text="演示数据"
          inactive-text="真实数据"
          size="small"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ topic: '', startAt: '', endAt: '', demo: false }),
  },
  showDemoToggle: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['search', 'update:modelValue'])

const form = reactive({
  topic: props.modelValue.topic || '',
  startAt: props.modelValue.startAt || '',
  endAt: props.modelValue.endAt || '',
  demo: props.modelValue.demo || false,
})

watch(() => props.modelValue, (val) => {
  form.topic = val.topic || ''
  form.startAt = val.startAt || ''
  form.endAt = val.endAt || ''
  form.demo = val.demo || false
}, { deep: true })

function emitSearch() {
  const value = { ...form }
  emit('update:modelValue', value)
  emit('search', value)
}

defineExpose({ emitSearch })
</script>

<style lang="scss" scoped>
.analysis-filters {
  padding: 16px 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: var(--el-box-shadow-light);

  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}
</style>