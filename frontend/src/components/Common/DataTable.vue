<template>
  <div class="data-table">
    <div
      v-if="searchable || exportable || refreshable"
      class="table-header"
    >
      <div class="header-left">
        <el-input
          v-if="searchable"
          v-model="searchKeyword"
          :placeholder="searchPlaceholder"
          prefix-icon="Search"
          clearable
          style="width: 240px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </div>
      <div class="header-right">
        <el-button
          v-if="exportable"
          type="primary"
          :icon="Download"
          @click="handleExport"
        >
          导出
        </el-button>
        <el-button
          v-if="refreshable"
          :icon="Refresh"
          @click="handleRefresh"
        >
          刷新
        </el-button>
      </div>
    </div>

    <el-table
      :data="tableData"
      :loading="loading"
      :stripe="stripe"
      :border="border"
      :row-key="rowKey"
      :default-sort="defaultSort"
      v-bind="$attrs"
      @sort-change="handleSortChange"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        v-if="selection"
        type="selection"
        width="55"
      />
      <template
        v-for="column in columns"
        :key="column.prop"
      >
        <el-table-column v-bind="column">
          <template
            v-if="column.slots"
            #default="{ row }"
          >
            <slot
              :name="column.slots.default"
              :row="row"
              :column="column"
            />
          </template>
        </el-table-column>
      </template>

      <el-table-column
        v-if="$slots.operation"
        label="操作"
        :width="operationWidth"
        fixed="right"
      >
        <template #default="{ row }">
          <slot
            name="operation"
            :row="row"
          />
        </template>
      </el-table-column>
    </el-table>

    <div
      v-if="pagination"
      class="pagination-wrapper"
    >
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
  import { ref, watch, computed } from 'vue'
  import { Download, Refresh } from '@element-plus/icons-vue'

  const props = defineProps({
    data: {
      type: Array,
      default: () => [],
    },
    columns: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    pagination: {
      type: Boolean,
      default: true,
    },
    total: {
      type: Number,
      default: 0,
    },
    searchable: {
      type: Boolean,
      default: true,
    },
    exportable: {
      type: Boolean,
      default: false,
    },
    refreshable: {
      type: Boolean,
      default: true,
    },
    selection: {
      type: Boolean,
      default: false,
    },
    stripe: {
      type: Boolean,
      default: true,
    },
    border: {
      type: Boolean,
      default: false, // Turn off by default for clean look
    },
    rowKey: {
      type: String,
      default: 'id',
    },
    defaultSort: {
      type: Object,
      default: () => ({ prop: '', order: '' }),
    },
    pageSizes: {
      type: Array,
      default: () => [10, 20, 50, 100],
    },
    operationWidth: {
      type: Number,
      default: 150,
    },
  })

  const emit = defineEmits([
    'search',
    'refresh',
    'export',
    'sort-change',
    'selection-change',
    'page-change',
    'size-change',
  ])

  const searchKeyword = ref('')
  const currentPage = ref(1)
  const pageSize = ref(10)
  const searchPlaceholder = computed(() => '搜索关键字')

  const tableData = computed(() => props.data)

  const handleSearch = () => {
    emit('search', searchKeyword.value)
  }

  const handleRefresh = () => {
    emit('refresh')
  }

  const handleExport = () => {
    emit('export')
  }

  const handleSortChange = ({ prop, order }) => {
    emit('sort-change', { prop, order })
  }

  const handleSelectionChange = (selection) => {
    emit('selection-change', selection)
  }

  const handlePageChange = (page) => {
    currentPage.value = page
    emit('page-change', page)
  }

  const handleSizeChange = (size) => {
    pageSize.value = size
    emit('size-change', size)
  }
</script>

<style lang="scss" scoped>
  .data-table {
    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }

    .pagination-wrapper {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }
  }
</style>
