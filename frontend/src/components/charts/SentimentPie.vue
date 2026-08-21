<template>
  <BaseChart
    :options="options"
    :height="height"
  />
</template>

<script setup>
import BaseChart from '@/components/Charts/BaseChart.vue'
defineProps({ options: { type: Object, required: true }, height: { type: String, default: '220px' } })
</script>
