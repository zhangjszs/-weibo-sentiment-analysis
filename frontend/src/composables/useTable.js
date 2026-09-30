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
  // 失败态：区分「真无数据」与「加载失败」。失败时保留旧数据（避免瞬时
  // 错误清空视图），但显式标记，供视图提示重试，而不是静默用旧数据误导（#19）。
  const loadError = ref(false)
  // 请求序号：慢的旧响应不得覆盖新响应（快速翻页/连续搜索场景）
  let loadSeq = 0

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

    const seq = ++loadSeq
    loading.value = true
    try {
      const result = await fetchData(queryParams.value)
      if (seq !== loadSeq) return
      if (result.code === 200) {
        tableData.value = result.data?.list || result.data || []
        total.value = result.data?.total || tableData.value.length
        loadError.value = false
      }
    } catch (error) {
      if (seq !== loadSeq) return
      loadError.value = true
      console.error('加载表格数据失败:', error)
    } finally {
      if (seq === loadSeq) {
        loading.value = false
      }
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
    loadError,
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
