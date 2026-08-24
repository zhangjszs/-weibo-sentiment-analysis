<template>
  <div class="alert-center-container">
    <AlertChart :stats="stats" />

    <el-row :gutter="24">
      <el-col
        :xs="24"
        :lg="16"
      >
        <AlertList
          :alerts="alerts"
          :loading="loading"
          :filter-level="filterLevel"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          :stats="stats"
          @update:filter-level="val => { filterLevel = val; fetchAlerts() }"
          @update:current-page="val => currentPage = val"
          @page-change="fetchAlerts"
          @mark-all-read="handleMarkAllRead"
          @show-detail="showAlertDetail"
        />
      </el-col>

      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="rules-card">
          <template #header>
            <div class="card-header">
              <span>预警规则</span>
              <el-button
                type="primary"
                size="small"
                @click="showRuleDialog = true"
              >
                新增规则
              </el-button>
            </div>
          </template>

          <div class="rules-list">
            <div
              v-for="rule in rules"
              :key="rule.id"
              class="rule-item"
            >
              <div class="rule-info">
                <div class="rule-name">
                  {{ rule.name }}
                </div>
                <div class="rule-type">
                  {{ getTypeLabel(rule.alert_type) }}
                </div>
              </div>
              <div class="rule-actions">
                <el-switch
                  v-model="rule.enabled"
                  @change="handleToggleRule(rule)"
                />
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="test-card mt-4">
          <template #header>
            <span>测试预警</span>
          </template>
          <el-form
            :model="testForm"
            label-position="top"
          >
            <el-form-item label="预警级别">
              <el-select
                v-model="testForm.level"
                style="width: 100%"
              >
                <el-option
                  label="信息"
                  value="info"
                />
                <el-option
                  label="警告"
                  value="warning"
                />
                <el-option
                  label="危险"
                  value="danger"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="消息内容">
              <el-input
                v-model="testForm.message"
                type="textarea"
                :rows="2"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="testing"
                @click="handleTestAlert"
              >
                发送测试预警
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="showDetailDialog"
      title="预警详情"
      width="500px"
    >
      <el-descriptions
        v-if="selectedAlert"
        :column="1"
        border
      >
        <el-descriptions-item label="预警标题">
          {{ selectedAlert.title }}
        </el-descriptions-item>
        <el-descriptions-item label="预警级别">
          <el-tag :type="getLevelTagType(selectedAlert.level)">
            {{ getLevelLabel(selectedAlert.level) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="预警类型">
          {{
            getTypeLabel(selectedAlert.alert_type)
          }}
        </el-descriptions-item>
        <el-descriptions-item label="预警内容">
          {{ selectedAlert.message }}
        </el-descriptions-item>
        <el-descriptions-item label="触发时间">
          {{
            formatTime(selectedAlert.created_at)
          }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="selectedAlert.data"
          label="附加数据"
        >
          <pre class="data-json">{{ JSON.stringify(selectedAlert.data, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="showRuleDialog"
      title="新增预警规则"
      width="500px"
    >
      <el-form
        :model="ruleForm"
        label-position="top"
      >
        <el-form-item label="规则ID">
          <el-input
            v-model="ruleForm.id"
            placeholder="唯一标识符"
          />
        </el-form-item>
        <el-form-item label="规则名称">
          <el-input
            v-model="ruleForm.name"
            placeholder="规则显示名称"
          />
        </el-form-item>
        <el-form-item label="预警类型">
          <el-select
            v-model="ruleForm.alert_type"
            style="width: 100%"
          >
            <el-option
              label="讨论量激增"
              value="volume_spike"
            />
            <el-option
              label="负面舆情激增"
              value="negative_surge"
            />
            <el-option
              label="情感突变"
              value="sentiment_shift"
            />
            <el-option
              label="热点话题"
              value="hot_topic"
            />
            <el-option
              label="关键词匹配"
              value="keyword_match"
            />
            <el-option
              label="自定义"
              value="custom"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预警级别">
          <el-select
            v-model="ruleForm.level"
            style="width: 100%"
          >
            <el-option
              label="信息"
              value="info"
            />
            <el-option
              label="警告"
              value="warning"
            />
            <el-option
              label="危险"
              value="danger"
            />
            <el-option
              label="严重"
              value="critical"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="冷却时间(分钟)">
          <el-input-number
            v-model="ruleForm.cooldown_minutes"
            :min="1"
            :max="1440"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRuleDialog = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="creating"
          @click="handleCreateRule"
        >
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import AlertChart from '@/components/alert/AlertChart.vue'
import AlertList from '@/components/alert/AlertList.vue'
import { useAlert } from '@/composables/useAlert'
const { loading, alerts, stats, rules, filterLevel, currentPage, pageSize, total, showDetailDialog, selectedAlert, showRuleDialog, testing, creating, testForm, ruleForm, getLevelTagType, getLevelLabel, getTypeLabel, formatTime, fetchAlerts, showAlertDetail, handleMarkAllRead, handleToggleRule, handleTestAlert, handleCreateRule } = useAlert()
</script>

<style lang="scss" scoped src="./center.scss"></style>
