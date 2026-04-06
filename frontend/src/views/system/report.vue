<template>
  <div class="report-container">
    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col
        :xs="24"
        :lg="16"
      >
        <el-card class="generator-card">
          <template #header>
            <div class="card-header">
              <span>报告生成</span>
            </div>
          </template>

          <el-form
            :model="reportForm"
            label-position="top"
          >
            <el-row :gutter="20">
              <el-col
                :xs="24"
                :md="12"
              >
                <el-form-item label="报告标题">
                  <el-input
                    v-model="reportForm.title"
                    placeholder="请输入报告标题"
                  />
                </el-form-item>
              </el-col>
              <el-col
                :xs="24"
                :md="12"
              >
                <el-form-item label="报告格式">
                  <el-radio-group v-model="reportForm.format">
                    <el-radio-button label="pdf">
                      PDF
                    </el-radio-button>
                    <el-radio-button label="ppt">
                      PPT
                    </el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="报告模板">
              <el-radio-group v-model="reportForm.template">
                <el-radio-button
                  v-for="t in templates"
                  :key="t.id"
                  :label="t.id"
                >
                  {{ t.name }}
                </el-radio-button>
              </el-radio-group>
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
                <el-checkbox label="summary">
                  数据概览
                </el-checkbox>
                <el-checkbox label="sentiment">
                  情感分析
                </el-checkbox>
                <el-checkbox label="topics">
                  热门话题
                </el-checkbox>
                <el-checkbox label="alerts">
                  预警记录
                </el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="generating"
                @click="handleGenerate"
              >
                <el-icon class="mr-1">
                  <Document />
                </el-icon>
                生成报告
              </el-button>
              <el-button
                :loading="generatingAll"
                @click="handleGenerateAll"
              >
                生成所有格式
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="preview-card">
          <template #header>
            <div class="card-header">
              <span>数据预览</span>
              <el-tag
                size="small"
                type="info"
              >
                {{ dataSourceText }}
              </el-tag>
            </div>
          </template>

          <div
            v-loading="loadingDemo"
            class="preview-content"
          >
            <el-descriptions
              :column="1"
              border
              size="small"
            >
              <el-descriptions-item label="总文章数">
                {{
                  demoData.summary?.total_articles || 0
                }}
              </el-descriptions-item>
              <el-descriptions-item label="总评论数">
                {{
                  demoData.summary?.total_comments || 0
                }}
              </el-descriptions-item>
              <el-descriptions-item label="正面评价">
                {{
                  demoData.summary?.positive_count || 0
                }}
              </el-descriptions-item>
              <el-descriptions-item label="中性评价">
                {{
                  demoData.summary?.neutral_count || 0
                }}
              </el-descriptions-item>
              <el-descriptions-item label="负面评价">
                {{
                  demoData.summary?.negative_count || 0
                }}
              </el-descriptions-item>
            </el-descriptions>

            <el-divider content-position="left">
              热门话题
            </el-divider>

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

      <el-table
        :data="historyList"
        style="width: 100%"
      >
        <el-table-column
          prop="title"
          label="报告标题"
          min-width="200"
        />
        <el-table-column
          prop="format"
          label="格式"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="row.format === 'pdf' ? 'danger' : 'primary'"
              size="small"
            >
              {{ row.format.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="generated_at"
          label="生成时间"
          width="180"
          align="center"
        >
          <template #default="{ row }">
            {{ formatTime(row.generated_at) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="200"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleDownload(row)"
            >
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

      <el-empty
        v-if="historyList.length === 0"
        description="暂无生成历史"
      />
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
    try {
      const res = await getReportTemplates()
      if (res.code === 200) {
        templates.value = res.data.templates
      }
    } catch (error) {
      console.error('获取模板失败:', error)
    }
  }

  const fetchReportData = async () => {
    loadingDemo.value = true
    try {
      const res = await getReportData({ demo: useDemoData.value })
      if (res.code === 200) {
        demoData.value = res.data
      }
    } catch (error) {
      console.error('获取报告数据失败:', error)
    } finally {
      loadingDemo.value = false
    }
  }

  const handleGenerate = async () => {
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
    } catch (error) {
      ElMessage.error('报告生成失败')
    } finally {
      generating.value = false
    }
  }

  const handleGenerateAll = async () => {
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
    } catch (error) {
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
