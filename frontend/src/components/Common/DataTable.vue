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
    background: var(--el-gradient-surface);
    border-radius: var(--el-border-radius-base);
    padding: 24px;
    box-shadow: var(--el-box-shadow-light);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      box-shadow: var(--el-box-shadow-dark);
    }

    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--el-border-color-light);

      .header-left {
        .el-input {
          --el-input-bg-color: var(--el-bg-color);
          --el-input-border-radius: var(--el-border-radius-base);
          --el-input-hover-border-color: var(--el-color-primary-light-3);
          --el-input-focus-border-color: var(--el-color-primary);

          .el-input__wrapper {
            box-shadow: 0 0 0 1px var(--el-border-color) inset;
            transition: all 0.3s ease;

            &:hover {
              box-shadow: 0 0 0 1px var(--el-color-primary-light-3) inset;
            }

            &.is-focus {
              box-shadow:
                0 0 0 2px rgba(var(--el-color-primary-rgb), 0.1) inset,
                0 0 0 1px var(--el-color-primary) inset;
            }
          }
        }
      }

      .header-right {
        display: flex;
        gap: 12px;

        .el-button {
          border-radius: var(--el-border-radius-base);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

          &:hover {
            transform: translateY(-2px);
            box-shadow: var(--el-box-shadow-light);
          }

          &--primary {
            background: var(--el-gradient-primary);
            border: none;
            box-shadow: var(--el-box-shadow-light);

            &:hover {
              box-shadow: var(--el-box-shadow-dark);
            }
          }
        }
      }
    }

    :deep(.el-table) {
      border-radius: var(--el-border-radius-base);
      overflow: hidden;
      box-shadow: var(--el-box-shadow-lighter);

      &__header-wrapper {
        background: var(--el-gradient-surface);

        th.el-table__cell {
          background: var(--el-gradient-surface);
          color: var(--el-text-color-primary);
          font-weight: 600;
          font-size: 14px;
          border-bottom: 1px solid var(--el-border-color-light);
          padding: 16px;

          &:hover {
            background: var(--el-color-primary-light-9);
          }
        }
      }

      &__body-wrapper {
        td.el-table__cell {
          padding: 16px;
          border-bottom: 1px solid var(--el-border-color-lighter);
          transition: all 0.2s ease;

          &:hover {
            background: var(--el-color-primary-light-9);
          }
        }

        .el-table__row {
          transition: all 0.3s ease;

          &:hover {
            transform: translateX(4px);
          }
        }
      }
    }

    .pagination-wrapper {
      margin-top: 24px;
      display: flex;
      justify-content: flex-end;
      padding-top: 16px;
      border-top: 1px solid var(--el-border-color-light);

      :deep(.el-pagination) {
        button, li {
          border-radius: var(--el-border-radius-small);
          transition: all 0.3s ease;

          &:hover {
            background-color: var(--el-color-primary-light-9);
            color: var(--el-color-primary);
          }

          &.is-active {
            background-color: var(--el-color-primary-light-9);
            color: var(--el-color-primary);
            font-weight: 600;
            border: 1px solid var(--el-color-primary-light-3);
          }
        }
      }
    }
  }

  /* Dark mode overrides */
  .dark .data-table {
    background: var(--el-gradient-surface);
    box-shadow: var(--el-box-shadow-dark);

    .table-header {
      border-bottom-color: #334155;

      .header-left .el-input {
        --el-input-bg-color: #1e293b;
        --el-input-border-color: #334155;

        .el-input__wrapper {
          box-shadow: 0 0 0 1px #334155 inset;

          &:hover {
            box-shadow: 0 0 0 1px #475569 inset;
          }

          &.is-focus {
            box-shadow:
              0 0 0 2px rgba(var(--el-color-primary-rgb), 0.2) inset,
              0 0 0 1px var(--el-color-primary) inset;
          }
        }
      }
    }

    :deep(.el-table) {
      &__header-wrapper {
        background: var(--el-gradient-surface);

        th.el-table__cell {
          background: var(--el-gradient-surface);
          border-bottom-color: #334155;

          &:hover {
            background: #334155;
          }
        }
      }

      &__body-wrapper {
        td.el-table__cell {
          border-bottom-color: #334155;

          &:hover {
            background: #334155;
          }
        }

        .el-table__row {
          &:hover {
            transform: translateX(4px);
          }
        }
      }
    }

    .pagination-wrapper {
      border-top-color: #334155;

      :deep(.el-pagination) {
        button, li {
          &:hover {
            background-color: #334155;
          }

          &.is-active {
            background-color: #334155;
            border: 1px solid var(--el-color-primary-light-3);
          }
        }
      }
    }
  }
</style>
