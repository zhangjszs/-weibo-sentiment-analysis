<template>
  <div
    class="responsive-table"
    :class="{ 'mobile-mode': isMobile }"
  >
    <div
      v-if="isMobile && showCard"
      class="table-cards"
    >
      <div
        v-for="(row, index) in data"
        :key="index"
        class="table-card"
        @click="$emit('row-click', row)"
      >
        <div
          v-for="col in columns"
          :key="col.prop"
          class="card-item"
        >
          <span class="card-label">{{ col.label }}</span>
          <span class="card-value">
            <slot
              :name="'cell-' + col.prop"
              :row="row"
              :value="row[col.prop]"
            >
              {{ row[col.prop] }}
            </slot>
          </span>
        </div>
      </div>
    </div>

    <el-table
      v-else
      :data="data"
      v-bind="$attrs"
      @row-click="$emit('row-click', $event)"
    >
      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :align="col.align || 'left'"
      >
        <template #default="scope">
          <slot
            :name="'cell-' + col.prop"
            :row="scope.row"
            :value="scope.row[col.prop]"
          >
            {{ scope.row[col.prop] }}
          </slot>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
  import { ref, computed } from 'vue'
  import { useResponsive } from '@/composables/useResponsive'

  const props = defineProps({
    data: {
      type: Array,
      default: () => [],
    },
    columns: {
      type: Array,
      required: true,
    },
    showCard: {
      type: Boolean,
      default: true,
    },
  })

  defineEmits(['row-click'])

  const { isMobile } = useResponsive()
</script>

<style lang="scss" scoped>
  .responsive-table {
    &.mobile-mode {
      .table-cards {
        display: flex;
        flex-direction: column;
        gap: 12px;

        .table-card {
          background: var(--el-bg-color);
          border: 1px solid var(--el-border-color-light);
          border-radius: 8px;
          padding: 12px;
          cursor: pointer;
          transition: box-shadow 0.2s;

          &:active {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          }

          .card-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--el-border-color-lighter);

            &:last-child {
              border-bottom: none;
            }

            .card-label {
              font-size: 13px;
              color: var(--el-text-color-secondary);
            }

            .card-value {
              font-size: 14px;
              font-weight: 500;
            }
          }
        }
      }
    }
  }
</style>
