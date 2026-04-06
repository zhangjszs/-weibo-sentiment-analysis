<template>
  <div class="propagation-container">
    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col
        :xs="24"
        :sm="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon primary">
              <el-icon><Share /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ summary.path?.total_nodes || 0 }}
              </div>
              <div class="stat-label">
                传播节点
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ summary.path?.total_depth || 0 }}
              </div>
              <div class="stat-label">
                传播深度
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ summary.kol_count || 0 }}
              </div>
              <div class="stat-label">
                KOL节点
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon danger">
              <el-icon><Odometer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ summary.path?.propagation_speed?.toFixed(1) || 0 }}
              </div>
              <div class="stat-label">
                传播速度(节点/时)
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col
        :xs="24"
        :lg="16"
      >
        <el-card class="graph-card">
          <template #header>
            <div class="card-header">
              <span>传播路径图</span>
              <div class="header-actions">
                <el-input
                  v-model="articleId"
                  placeholder="输入文章ID"
                  style="width: 150px"
                  size="small"
                />
                <el-button
                  type="primary"
                  size="small"
                  :loading="loading"
                  @click="loadPropagation"
                >
                  分析
                </el-button>
              </div>
            </div>
          </template>
          <div
            ref="graphContainer"
            v-loading="loading"
            class="graph-container"
          >
            <div
              v-if="!graphData.nodes?.length"
              class="empty-state"
            >
              <el-empty description="输入文章ID开始分析传播路径" />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="info-card">
          <template #header>
            <span>传播路径信息</span>
          </template>
          <el-descriptions
            v-if="summary.path"
            :column="1"
            border
          >
            <el-descriptions-item label="原始发布者">
              {{
                summary.path.origin_user
              }}
            </el-descriptions-item>
            <el-descriptions-item label="总转发量">
              {{
                summary.path.total_reposts
              }}
            </el-descriptions-item>
            <el-descriptions-item label="传播深度">
              {{
                summary.path.total_depth
              }}
            </el-descriptions-item>
            <el-descriptions-item label="传播节点数">
              {{
                summary.path.total_nodes
              }}
            </el-descriptions-item>
            <el-descriptions-item label="传播速度">
              {{ summary.path.propagation_speed?.toFixed(2) }} 节点/小时
            </el-descriptions-item>
          </el-descriptions>
          <el-empty
            v-else
            description="暂无数据"
            :image-size="60"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span>传播深度分布</span>
          </template>
          <BaseChart
            ref="depthChartRef"
            :options="depthChartOptions"
            height="300px"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span>传播时间线</span>
          </template>
          <BaseChart
            ref="timelineChartRef"
            :options="timelineChartOptions"
            height="300px"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="24"
      class="mt-4"
    >
      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="kol-card">
          <template #header>
            <div class="card-header">
              <span>KOL影响力排行</span>
              <el-tag
                type="danger"
                size="small"
              >
                {{ summary.kol_count || 0 }} 个KOL
              </el-tag>
            </div>
          </template>
          <el-table
            :data="kolNodes"
            style="width: 100%"
            max-height="350"
          >
            <el-table-column
              prop="user_name"
              label="用户名"
              min-width="120"
            />
            <el-table-column
              prop="repost_count"
              label="转发"
              width="80"
              align="center"
            />
            <el-table-column
              prop="comment_count"
              label="评论"
              width="80"
              align="center"
            />
            <el-table-column
              prop="like_count"
              label="点赞"
              width="80"
              align="center"
            />
            <el-table-column
              prop="influence_score"
              label="影响力"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <el-progress
                  :percentage="row.influence_score * 100"
                  :stroke-width="8"
                  :show-text="false"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="ranking-card">
          <template #header>
            <span>用户影响力排名</span>
          </template>
          <el-table
            :data="userRanking"
            style="width: 100%"
            max-height="350"
          >
            <el-table-column
              type="index"
              label="#"
              width="50"
              align="center"
            />
            <el-table-column
              prop="user_name"
              label="用户名"
              min-width="120"
            />
            <el-table-column
              prop="node_count"
              label="参与次数"
              width="90"
              align="center"
            />
            <el-table-column
              prop="influence_score"
              label="影响力得分"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <span class="score-value">{{ row.influence_score?.toFixed(3) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, nextTick } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Share, TrendCharts, User, Odometer } from '@element-plus/icons-vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { analyzePropagation, getPropagationGraph } from '@/api/propagation'
  import echarts from '@/utils/echarts'

  const loading = ref(false)
  const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'
  const defaultArticleId = import.meta.env.VITE_DEFAULT_ARTICLE_ID || ''
  const articleId = ref(defaultArticleId || (demoMode ? 'demo_article_001' : ''))
  const summary = ref({})
  const graphData = ref({ nodes: [], edges: [] })
  const kolNodes = ref([])
  const userRanking = ref([])
  const depthDistribution = ref({})
  const timeDistribution = ref([])

  const graphContainer = ref(null)
  const depthChartRef = ref(null)
  const timelineChartRef = ref(null)
  let graphInstance = null

  const depthChartOptions = computed(() => {
    const depthData = depthDistribution.value || {}
    const categories = Object.keys(depthData).map((d) => `第${d}层`)
    const values = Object.values(depthData)

    return {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: categories,
      },
      yAxis: { type: 'value', name: '节点数' },
      series: [
        {
          type: 'bar',
          data: values,
          itemStyle: {
            color: '#2563EB',
          },
          label: {
            show: true,
            position: 'top',
          },
        },
      ],
    }
  })

  const timelineChartOptions = computed(() => {
    const timelineData = timeDistribution.value || []

    return {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: timelineData.map((t) => t.time?.substring(11, 16) || ''),
        axisLabel: { rotate: 45 },
      },
      yAxis: { type: 'value', name: '传播量' },
      series: [
        {
          type: 'line',
          data: timelineData.map((t) => t.count),
          smooth: true,
          areaStyle: { opacity: 0.3 },
          itemStyle: { color: '#10B981' },
        },
      ],
    }
  })

  const loadPropagation = async () => {
    if (!articleId.value) {
      ElMessage.warning('请输入文章ID')
      return
    }

    loading.value = true

    try {
      const [analyzeRes, graphRes] = await Promise.all([
        analyzePropagation(articleId.value, { demo: demoMode, count: 100 }),
        getPropagationGraph(articleId.value, { demo: demoMode, count: 80 }),
      ])

      if (analyzeRes.code === 200) {
        summary.value = analyzeRes.data.summary
        kolNodes.value = analyzeRes.data.summary.kol_nodes || []
        userRanking.value = analyzeRes.data.summary.user_ranking || []
        depthDistribution.value = analyzeRes.data.summary.depth_distribution || {}
        timeDistribution.value = analyzeRes.data.summary.time_distribution || []
      }

      if (graphRes.code === 200) {
        graphData.value = graphRes.data
        await nextTick()
        renderGraph()
      }

      ElMessage.success('传播路径分析完成')
    } catch (error) {
      ElMessage.error('分析失败')
      console.error(error)
    } finally {
      loading.value = false
    }
  }

  const renderGraph = () => {
    if (!graphContainer.value || !graphData.value.nodes?.length) return

    if (graphInstance) {
      graphInstance.dispose()
    }

    graphInstance = echarts.init(graphContainer.value)

      const nodes = graphData.value.nodes.map((node) => ({
        id: node.id,
        name: node.user_name,
        symbolSize: Math.max(10, node.influence_score * 40 + 10),
        category: node.category,
        value: node.influence_score,
        itemStyle: {
          color: node.category === 0 ? '#EF4444' : node.category === 1 ? '#2563EB' : '#64748B',
        },
        label: {
          show: node.is_kol || node.depth === 0,
          fontSize: 10,
        },
      }))

      const edges = graphData.value.edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
        lineStyle: {
          width: Math.max(1, edge.weight),
          curveness: 0.2,
        },
      }))

      const option = {
        tooltip: {
          formatter: (params) => {
            if (params.dataType === 'node') {
              return `${params.data.name}<br/>影响力: ${(params.data.value * 100).toFixed(1)}%`
            }
            return ''
          },
        },
        series: [
          {
            type: 'graph',
            layout: 'force',
            data: nodes,
            links: edges,
            roam: true,
            draggable: true,
            force: {
              repulsion: 200,
              edgeLength: [50, 150],
              gravity: 0.1,
            },
            emphasis: {
              focus: 'adjacency',
              lineStyle: { width: 3 },
            },
            label: {
              position: 'right',
              formatter: '{b}',
            },
            lineStyle: {
              color: 'source',
              curveness: 0.3,
            },
          },
        ],
      }

    graphInstance.setOption(option)
  }

  onMounted(() => {
    if (articleId.value) {
      loadPropagation()
    }
  })
</script>

<style lang="scss" scoped>
  .propagation-container {
    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          margin-right: 16px;

          &.primary {
            background: var(--el-color-primary-light-8);
            color: var(--el-color-primary);
          }
          &.success {
            background: var(--el-color-success-light-8);
            color: var(--el-color-success);
          }
          &.warning {
            background: var(--el-color-warning-light-8);
            color: var(--el-color-warning);
          }
          &.danger {
            background: var(--el-color-danger-light-8);
            color: var(--el-color-danger);
          }
        }

        .stat-info {
          .stat-value {
            font-size: 24px;
            font-weight: 600;
          }
          .stat-label {
            font-size: 14px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }

    .graph-card {
      .graph-container {
        height: 450px;
        position: relative;

        .empty-state {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        }
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }

    .score-value {
      font-weight: 600;
      color: var(--el-color-primary);
    }

    .mt-4 {
      margin-top: 16px;
    }
    .mb-4 {
      margin-bottom: 16px;
    }
  }
</style>
