<template>
  <div
    v-if="loading"
    class="page-loading"
  >
    <div class="loading-container">
      <div class="loading-spinner">
        <div class="spinner-ring" />
        <div class="spinner-ring" />
        <div class="spinner-ring" />
      </div>
      <p class="loading-text">
        {{ text }}
      </p>
    </div>
  </div>
  <div
    v-else
    class="page-content"
  >
    <slot />
  </div>
</template>

<script setup>
  defineProps({
    loading: {
      type: Boolean,
      default: false,
    },
    text: {
      type: String,
      default: '加载中...',
    },
  })
</script>

<style lang="scss" scoped>
  .page-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    width: 100%;
  }

  .loading-container {
    text-align: center;
  }

  .loading-spinner {
    position: relative;
    width: 80px;
    height: 80px;
    margin: 0 auto 16px;
  }

  .spinner-ring {
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 3px solid transparent;
    border-top-color: #005aa0;
    animation: spin 1.5s linear infinite;

    &:nth-child(2) {
      width: 80%;
      height: 80%;
      top: 10%;
      left: 10%;
      border-top-color: #667eea;
      animation-duration: 1.2s;
      animation-direction: reverse;
    }

    &:nth-child(3) {
      width: 60%;
      height: 60%;
      top: 20%;
      left: 20%;
      border-top-color: #764ba2;
      animation-duration: 0.9s;
    }
  }

  .loading-text {
    color: #999;
    font-size: 14px;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .page-content {
    width: 100%;
  }
</style>
