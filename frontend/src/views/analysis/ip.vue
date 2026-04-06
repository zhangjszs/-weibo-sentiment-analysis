<template>
  <div class="ip-analysis-container">
    <el-row :gutter="20">
      <el-col
        :xs="24"
        :lg="16"
      >
        <el-card class="chart-card">
          <template #header>
            <span>IP地理位置分布</span>
          </template>
          <BaseChart
            ref="mapChartRef"
            :options="mapChartOptions"
            height="500px"
            @click="handleRegionSelect"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="chart-card">
          <template #header>
            <span>Top 10 地区分布</span>
          </template>
          <BaseChart
            ref="regionChartRef"
            :options="regionChartOptions"
            height="500px"
            @click="handleRegionSelect"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>IP分析详细数据</span>
              <div class="actions">
                <el-tag
                  v-if="selectedRegion"
                  closable
                  effect="plain"
                  @close="clearRegion"
                >
                  地区：{{ selectedRegion }}
                </el-tag>
                <el-button
                  type="primary"
                  @click="loadData"
                >
                  刷新数据
                </el-button>
              </div>
            </div>
          </template>
          <el-table
            :data="displayIpList"
            :loading="loading"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column
              prop="ip"
              label="IP地址"
              width="180"
            />
            <el-table-column
              prop="location"
              label="地理位置"
              width="200"
            />
            <el-table-column
              prop="count"
              label="出现次数"
              width="120"
              align="center"
              sortable
            />
            <el-table-column
              prop="lastTime"
              label="最后活跃时间"
              width="200"
            />
            <el-table-column
              prop="user"
              label="相关用户"
              min-width="200"
              show-overflow-tooltip
            />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { getIPData } from '@/api/stats'
  import chinaMap from '@/assets/china.json'
  import echarts from '@/utils/echarts'

  const loading = ref(false)
  const ipDataList = ref([])
  const mapData = ref([])
  const regionData = ref([])
  const mapReady = ref(false)
  const selectedRegion = ref('')

  const mapChartRef = ref(null)
  const regionChartRef = ref(null)

  const displayIpList = computed(() => {
    if (!selectedRegion.value) return ipDataList.value
    return (ipDataList.value || []).filter((x) => (x.location || '').includes(selectedRegion.value))
  })

  // 注册中国地图
  const registerChinaMap = () => {
    try {
      echarts.registerMap('china', chinaMap)
      mapReady.value = true
    } catch (error) {
      console.error('Failed to load China map data:', error)
      ElMessage.warning('地图数据加载失败，地图功能不可用')
    }
  }

  const mapChartOptions = computed(() => ({
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `${params.name}: ${params.value || 0} 次`
      },
    },
    visualMap: {
      min: 0,
      max: Math.max(...mapData.value.map((item) => item.value || 0), 100),
      left: 'left',
      top: 'bottom',
      text: ['高', '低'],
      calculable: true,
      inRange: {
        color: ['#e0f3f8', '#005AA0'],
      },
    },
    series: [
      {
        name: 'IP分布',
        type: 'map',
        map: 'china',
        roam: true,
        label: {
          show: false,
        },
        data: mapData.value,
      },
    ],
  }))

  const regionChartOptions = computed(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: regionData.value.map((item) => item.name),
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: regionData.value.map((item) => item.value),
        itemStyle: {
          color: '#005AA0',
        },
      },
    ],
  }))

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getIPData()
      if (res.code === 200) {
        const data = res.data
        ipDataList.value = data.ipList || []
        mapData.value = data.mapData || []
        regionData.value = data.regionData?.slice(0, 10) || []
      }
    } catch (error) {
      ElMessage.error('加载数据失败')
    } finally {
      loading.value = false
    }
  }

  const handleRegionSelect = (params) => {
    const name = params?.name
    if (!name || typeof name !== 'string') return
    selectedRegion.value = name
  }

  const clearRegion = () => {
    selectedRegion.value = ''
  }

  onMounted(() => {
    registerChinaMap()
    loadData()
  })
</script>

<style lang="scss" scoped>
  .ip-analysis-container {
    .chart-card {
      margin-bottom: 20px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .actions {
        display: flex;
        align-items: center;
        gap: 10px;
      }
    }
  }
</style>
