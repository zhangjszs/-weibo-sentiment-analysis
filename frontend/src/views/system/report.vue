<template>
  <div class="report-container">
    <el-row :gutter="24" class="mb-4">
      <el-col :xs="24" :lg="16">
        <el-card class="generator-card">
          <template #header>
            <div class="card-header">
              <span>报告生成</span>
            </div>
          </template>

          <el-form :model="reportForm" label-position="top">
            <el-row :gutter="20">
              <el-col :xs="24" :md="12">
                <el-form-item label="报告标题">
                  <el-input v-model="reportForm.title" placeholder="请输入报告标题" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :md="12">
                <el-form-item label="报告格式">
                  <el-radio-group v-model="reportForm.format">
                    <el-radio-button value="pdf"> PDF </el-radio-button>
                    <el-radio-button value="ppt"> PPT </el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="报告模板">
              <div v-if="templatesLoading" class="region-loading templates-loading">
                模板加载中...
              </div>
              <div v-if="templatesError" class="region-error templates-error">
                <span>{{ templatesError }}</span>
                <el-button
                  link
                  type="primary"
                  size="small"
                  :loading="templatesLoading"
                  @click="retryTemplates"
                >
                  重试
                </el-button>
              </div>
              <el-radio-group v-model="reportForm.template">
                <el-radio-button v-for="t in templates" :key="t.id" :value="t.id">
                  {{ t.name }}
                </el-radio-button>
              </el-radio-group>
              <el-empty
                v-if="!templatesLoading && !templatesError && templates.length === 0"
                description="暂无可用模板"
                :image-size="60"
                class="templates-empty"
              />
            </el-form-item>

            <el-form-item label="数据来源">
              <el-switch
                v-model="useDemoData"
                active-text="演示数据"
                inactive-text="真实数据"
                inline-prompt
              />
            </el-form-item>

            <el-form-item label="报告内容">
              <el-checkbox-group v-model="reportForm.sections">
                <el-checkbox value="summary"> 数据概览 </el-checkbox>
                <el-checkbox value="sentiment"> 情感分析 </el-checkbox>
                <el-checkbox value="topics"> 热门话题 </el-checkbox>
                <el-checkbox value="alerts"> 预警记录 </el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="generating" @click="handleGenerate">
                <el-icon class="mr-1">
                  <Document />
                </el-icon>
                生成报告
              </el-button>
              <el-button :loading="generatingAll" @click="handleGenerateAll">
                生成所有格式
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="preview-card">
          <template #header>
            <div class="card-header">
              <span>数据预览</span>
              <el-tag size="small" type="info">
                {{ dataSourceText }}
              </el-tag>
            </div>
          </template>

          <div v-loading="loadingDemo" class="preview-content">
            <div v-if="reportError" class="region-error preview-error">
              <span>{{ reportError }}</span>
              <el-button
                link
                type="primary"
                size="small"
                :loading="loadingDemo"
                @click="retryReportData"
              >
                重试
              </el-button>
            </div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="总文章数">
                {{ demoData.summary?.total_articles || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="总评论数">
                {{ demoData.summary?.total_comments || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="正面评价">
                {{ demoData.summary?.positive_count || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="中性评价">
                {{ demoData.summary?.neutral_count || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="负面评价">
                {{ demoData.summary?.negative_count || 0 }}
              </el-descriptions-item>
            </el-descriptions>

            <el-divider content-position="left"> 热门话题 </el-divider>

            <el-tag
              v-for="(topic, index) in demoData.hot_topics?.slice(0, 5)"
              :key="index"
              class="topic-tag"
              effect="plain"
            >
              {{ topic.name }} ({{ topic.heat }})
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>生成历史</span>
          <el-button
            type="danger"
            plain
            size="small"
            :disabled="historyList.length === 0"
            @click="clearHistory"
          >
            清空历史
          </el-button>
        </div>
      </template>

      <el-table :data="historyList" style="width: 100%">
        <el-table-column prop="title" label="报告标题" min-width="200" />
        <el-table-column prop="format" label="格式" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.format === 'pdf' ? 'danger' : 'primary'" size="small">
              {{ row.format.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.generated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleDownload(row)">
              下载
            </el-button>
            <el-button
              v-if="row.format === 'pdf'"
              type="success"
              link
              size="small"
              @click="handlePreview(row)"
            >
              预览
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="historyList.length === 0" description="暂无生成历史" />
    </el-card>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Document } from '@element-plus/icons-vue'
  import {
    generateReport,
    generateAllReports,
    getReportTemplates,
    getReportData,
    downloadReport,
    previewReport,
  } from '@/api/report'

  const generating = ref(false)
  const generatingAll = ref(false)
  const loadingDemo = ref(false)
  const useDemoData = ref(import.meta.env.VITE_DEMO_MODE === 'true')

  const reportForm = ref({
    title: '舆情分析报告',
    format: 'pdf',
    template: 'standard',
    sections: ['summary', 'sentiment', 'topics', 'alerts'],
  })

  const templates = ref([])

  // U-6（#69）：两路 fetch 各自的 loading / 错误态（#65 同款语义）。
  // #19：失败只写错误态，从不清空已渲染旧数据、不伪装空态。
  const templatesLoading = ref(false)
  const templatesError = ref('')
  const reportError = ref('')

  const getErrorDetail = (error) => {
    const serverMsg = error?.response?.data?.msg || error?.response?.data?.message
    if (serverMsg) return serverMsg
    if (error?.message) return error.message
    return '网络错误'
  }

  // 模板选择后自动同步 sections
  watch(
    () => reportForm.value.template,
    (templateId) => {
      const tpl = templates.value.find((t) => t.id === templateId)
      if (tpl) {
        reportForm.value.sections = [...tpl.sections]
      }
    }
  )
  const demoData = ref({})
  const historyList = ref([])
  const dataSourceText = computed(() => {
    const source = demoData.value?.data_source
    if (source === 'real') return '真实数据'
    if (source === 'demo') return '演示数据'
    if (source === 'demo_fallback') return '真实数据不可用，已回退演示数据'
    return useDemoData.value ? '演示数据' : '真实数据'
  })

  const formatTime = (timeStr) => {
    if (!timeStr) return ''
    return new Date(timeStr).toLocaleString()
  }

  const fetchTemplates = async () => {
    templatesLoading.value = true
    templatesError.value = ''
    try {
      const res = await getReportTemplates()
      if (res.code === 200) {
        templates.value = res.data.templates
      } else {
        templatesError.value = `获取报告模板失败：${res.msg || '服务端错误'}，请重试`
      }
    } catch (error) {
      console.error('获取模板失败:', error)
      templatesError.value = `获取报告模板失败：${getErrorDetail(error)}，请重试`
    } finally {
      templatesLoading.value = false
    }
  }

  const fetchReportData = async () => {
    loadingDemo.value = true
    reportError.value = ''
    try {
      const res = await getReportData({ demo: useDemoData.value })
      if (res.code === 200) {
        demoData.value = res.data
      } else {
        reportError.value = `获取报告数据失败：${res.msg || '服务端错误'}，请重试`
      }
    } catch (error) {
      console.error('获取报告数据失败:', error)
      reportError.value = `获取报告数据失败：${getErrorDetail(error)}，请重试`
    } finally {
      loadingDemo.value = false
    }
  }

  const retryTemplates = () => fetchTemplates()
  const retryReportData = () => fetchReportData()

  const handleGenerate = async () => {
    // 空导出拦截：报告数据未加载成功（如 fetchReportData 失败只 console.error
    // 时 demoData 仍为空对象）就生成，只会产出一份空报告（#19）
    // U-6（#69）：守卫改为依赖错误状态判断——失败时直接暴露 reportError 根因。
    if (!demoData.value || Object.keys(demoData.value).length === 0) {
      ElMessage.warning(reportError.value || '报告数据未加载，请先等待数据加载成功后再生成')
      return
    }
    generating.value = true
    try {
      const res = await generateReport({
        title: reportForm.value.title,
        format: reportForm.value.format,
        template: reportForm.value.template,
        sections: reportForm.value.sections,
        demo_mode: useDemoData.value,
        data: demoData.value,
      })

      if (res.code === 200) {
        historyList.value.unshift(res.data)
        ElMessage.success('报告生成成功')
      } else {
        ElMessage.error(res.msg || '生成失败')
      }
    } catch {
      ElMessage.error('报告生成失败')
    } finally {
      generating.value = false
    }
  }

  const handleGenerateAll = async () => {
    if (!demoData.value || Object.keys(demoData.value).length === 0) {
      ElMessage.warning(reportError.value || '报告数据未加载，请先等待数据加载成功后再生成')
      return
    }
    generatingAll.value = true
    try {
      const res = await generateAllReports({
        title: reportForm.value.title,
        demo_mode: useDemoData.value,
        data: demoData.value,
      })

      if (res.code === 200) {
        const files = res.data.files
        for (const [format, info] of Object.entries(files)) {
          historyList.value.unshift({
            title: reportForm.value.title,
            format: format,
            generated_at: res.data.generated_at,
            download_url: info.download_url,
          })
        }
        ElMessage.success('所有报告生成成功')
      }
    } catch {
      ElMessage.error('报告生成失败')
    } finally {
      generatingAll.value = false
    }
  }

  const handleDownload = (row) => {
    const filename = row.download_url?.split('/').pop()
    if (filename) {
      window.open(downloadReport(filename), '_blank')
    }
  }

  const handlePreview = (row) => {
    const filename = row.download_url?.split('/').pop()
    if (filename) {
      window.open(previewReport(filename), '_blank')
    }
  }

  const clearHistory = () => {
    historyList.value = []
    ElMessage.success('历史记录已清空')
  }

  onMounted(() => {
    fetchTemplates()
    fetchReportData()
  })

  watch(useDemoData, () => {
    fetchReportData()
  })
</script>

<style lang="scss" scoped>
  .report-container {
    .region-loading {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      margin-bottom: 12px;
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }

    .region-error {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 12px;
      padding: 8px 12px;
      border-radius: 8px;
      background: rgba(239, 68, 68, 0.08);
      border: 1px dashed rgba(239, 68, 68, 0.4);
      color: var(--el-color-danger);
      font-size: 13px;
      line-height: 1.4;
    }

    .templates-empty {
      margin-top: 8px;
    }

    .generator-card {
      .el-radio-group {
        flex-wrap: wrap;
      }
    }

    .preview-card {
      .preview-content {
        .topic-tag {
          margin: 4px;
        }
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .mr-1 {
      margin-right: 4px;
    }
    .mb-4 {
      margin-bottom: 16px;
    }
  }
</style>
