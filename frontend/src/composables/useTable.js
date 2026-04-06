/**
 * 表格相关组合式函数
 * 提供分页、搜索、排序等通用表格逻辑
 */

import { ref, reactive, computed, watch } from 'vue'

/**
 * 使用分页表格
 * @param {Function} fetchData - 获取数据的函数
 * @param {Object} options - 配置选项
 */
export function useTable(fetchData, options = {}) {
  const { defaultPageSize = 10, defaultSort = { prop: '', order: '' }, immediate = true } = options

  // 数据状态
  const tableData = ref([])
  const loading = ref(false)
  const total = ref(0)

  // 分页状态
  const pagination = reactive({
    page: 1,
    pageSize: defaultPageSize,
  })

  // 搜索状态
  const searchParams = reactive({})

  // 排序状态
  const sortParams = reactive({ ...defaultSort })

  // 计算请求参数
  const queryParams = computed(() => ({
    page: pagination.page,
    pageSize: pagination.pageSize,
    ...searchParams,
    sortProp: sortParams.prop,
    sortOrder: sortParams.order,
  }))

  // 加载数据
  const loadData = async () => {
    if (!fetchData) return

    loading.value = true
    try {
      const result = await fetchData(queryParams.value)
      if (result.code === 200) {
        tableData.value = result.data?.list || result.data || []
        total.value = result.data?.total || tableData.value.length
      }
    } catch (error) {
      console.error('加载表格数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 刷新数据
  const refresh = () => {
    loadData()
  }

  // 重置并刷新
  const reset = () => {
    pagination.page = 1
    Object.keys(searchParams).forEach((key) => {
      delete searchParams[key]
    })
    loadData()
  }

  // 搜索
  const search = (params) => {
    Object.assign(searchParams, params)
    pagination.page = 1
    loadData()
  }

  // 处理分页变化
  const handlePageChange = (page) => {
    pagination.page = page
    loadData()
  }

  // 处理每页数量变化
  const handleSizeChange = (size) => {
    pagination.pageSize = size
    pagination.page = 1
    loadData()
  }

  // 处理排序变化
  const handleSortChange = ({ prop, order }) => {
    sortParams.prop = prop
    sortParams.order = order
    loadData()
  }

  // 选择状态
  const selectedRows = ref([])

  const handleSelectionChange = (selection) => {
    selectedRows.value = selection
  }

  // 立即加载
  if (immediate) {
    loadData()
  }

  return {
    tableData,
    loading,
    total,
    pagination,
    searchParams,
    sortParams,
    selectedRows,
    loadData,
    refresh,
    reset,
    search,
    handlePageChange,
    handleSizeChange,
    handleSortChange,
    handleSelectionChange,
  }
}

/**
 * 使用表格选择
 */
export function useTableSelection() {
  const selectedRows = ref([])
  const isAllSelected = computed(() => selectedRows.value.length > 0)

  const handleSelectionChange = (selection) => {
    selectedRows.value = selection
  }

  const clearSelection = () => {
    selectedRows.value = []
  }

  const getSelectedIds = (key = 'id') => {
    return selectedRows.value.map((row) => row[key])
  }

  return {
    selectedRows,
    isAllSelected,
    handleSelectionChange,
    clearSelection,
    getSelectedIds,
  }
}
