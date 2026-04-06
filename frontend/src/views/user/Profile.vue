<template>
  <div class="profile-page">
    <!-- 顶部资料卡片 -->
    <div class="profile-card">
      <div class="profile-card-bg" />
      <div class="profile-card-content">
        <div
          class="avatar"
          :style="{ backgroundColor: profileData.avatar_color || '#2563EB' }"
        >
          {{ avatarLetter }}
        </div>
        <div class="profile-info">
          <h2 class="display-name">
            {{ displayName }}
          </h2>
          <p class="username">
            @{{ profileData.username }}
          </p>
          <p
            v-if="profileData.bio"
            class="bio"
          >
            {{ profileData.bio }}
          </p>
          <div class="meta-tags">
            <el-tag
              v-if="profileData.is_admin"
              type="danger"
              size="small"
              effect="dark"
            >
              <el-icon><Star /></el-icon> 管理员
            </el-tag>
            <el-tag
              type="info"
              size="small"
              effect="plain"
            >
              <el-icon><Calendar /></el-icon> {{ profileData.create_time || '未知' }} 加入
            </el-tag>
            <el-tag
              v-if="profileData.email"
              type="info"
              size="small"
              effect="plain"
            >
              <el-icon><Message /></el-icon> {{ profileData.email }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab区域 -->
    <el-card class="settings-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane
          label="编辑资料"
          name="profile"
        >
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-position="top"
            class="settings-form"
          >
            <el-form-item
              label="昵称"
              prop="nickname"
            >
              <el-input
                v-model="profileForm.nickname"
                placeholder="设置你的昵称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>

            <el-form-item
              label="邮箱"
              prop="email"
            >
              <el-input
                v-model="profileForm.email"
                placeholder="your@email.com"
                maxlength="100"
              />
            </el-form-item>

            <el-form-item
              label="个人简介"
              prop="bio"
            >
              <el-input
                v-model="profileForm.bio"
                type="textarea"
                placeholder="介绍一下自己..."
                maxlength="200"
                show-word-limit
                :autosize="{ minRows: 3, maxRows: 5 }"
              />
            </el-form-item>

            <el-form-item label="头像颜色">
              <div class="color-picker">
                <div
                  v-for="color in colorOptions"
                  :key="color"
                  class="color-option"
                  :class="{ active: profileForm.avatar_color === color }"
                  :style="{ backgroundColor: color }"
                  @click="profileForm.avatar_color = color"
                >
                  <el-icon v-if="profileForm.avatar_color === color">
                    <Check />
                  </el-icon>
                </div>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="profileSaving"
                @click="saveProfile"
              >
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane
          label="修改密码"
          name="password"
        >
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-position="top"
            class="settings-form"
          >
            <el-form-item
              label="当前密码"
              prop="oldPassword"
            >
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>

            <el-form-item
              label="新密码"
              prop="newPassword"
            >
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
              />
            </el-form-item>

            <el-form-item
              label="确认新密码"
              prop="confirmPassword"
            >
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="passwordSaving"
                @click="savePassword"
              >
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Star, Calendar, Message, Check } from '@element-plus/icons-vue'
  import { getProfile, updateProfile, changePassword } from '@/api/user'
  import { useUserStore } from '@/stores/user'

  const userStore = useUserStore()

  const activeTab = ref('profile')
  const profileSaving = ref(false)
  const passwordSaving = ref(false)
  const profileFormRef = ref(null)
  const passwordFormRef = ref(null)

  const profileData = ref({
    username: '',
    nickname: '',
    email: '',
    bio: '',
    avatar_color: '#2563EB',
    create_time: '',
    is_admin: false,
  })

  const profileForm = reactive({
    nickname: '',
    email: '',
    bio: '',
    avatar_color: '#2563EB',
  })

  const passwordForm = reactive({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  })

  const colorOptions = [
    '#2563EB',
    '#7C3AED',
    '#DB2777',
    '#DC2626',
    '#EA580C',
    '#D97706',
    '#65A30D',
    '#059669',
    '#0891B2',
    '#4F46E5',
    '#6D28D9',
    '#0F172A',
  ]

  const displayName = computed(() => {
    return profileData.value.nickname || profileData.value.username || '用户'
  })

  const avatarLetter = computed(() => {
    const name = profileData.value.nickname || profileData.value.username || '?'
    return name.charAt(0).toUpperCase()
  })

  const validateEmail = (rule, value, callback) => {
    if (value && !value.includes('@')) {
      callback(new Error('请输入有效的邮箱地址'))
    } else {
      callback()
    }
  }

  const validateConfirmPassword = (rule, value, callback) => {
    if (value !== passwordForm.newPassword) {
      callback(new Error('两次输入的密码不一致'))
    } else {
      callback()
    }
  }

  const profileRules = {
    nickname: [{ max: 50, message: '昵称最多50个字符', trigger: 'blur' }],
    email: [{ validator: validateEmail, trigger: 'blur' }],
    bio: [{ max: 200, message: '简介最多200个字符', trigger: 'blur' }],
  }

  const passwordRules = {
    oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
    newPassword: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 6, max: 32, message: '密码长度为6-32个字符', trigger: 'blur' },
    ],
    confirmPassword: [
      { required: true, message: '请确认新密码', trigger: 'blur' },
      { validator: validateConfirmPassword, trigger: 'blur' },
    ],
  }

  const loadProfile = async () => {
    try {
      const res = await getProfile()
      if (res.code === 200) {
        profileData.value = res.data
        profileForm.nickname = res.data.nickname || ''
        profileForm.email = res.data.email || ''
        profileForm.bio = res.data.bio || ''
        profileForm.avatar_color = res.data.avatar_color || '#2563EB'
      }
    } catch (error) {
      ElMessage.error('加载个人资料失败')
    }
  }

  const saveProfile = async () => {
    if (!profileFormRef.value) return

    try {
      await profileFormRef.value.validate()
    } catch {
      return
    }

    profileSaving.value = true
    try {
      const res = await updateProfile({
        nickname: profileForm.nickname,
        email: profileForm.email,
        bio: profileForm.bio,
        avatar_color: profileForm.avatar_color,
      })

      if (res.code === 200) {
        ElMessage.success('资料更新成功')
        // Update local display
        profileData.value.nickname = profileForm.nickname
        profileData.value.email = profileForm.email
        profileData.value.bio = profileForm.bio
        profileData.value.avatar_color = profileForm.avatar_color
        // Update user store
        userStore.updateUserInfo({
          nickname: profileForm.nickname,
          avatar_color: profileForm.avatar_color,
        })
      } else {
        ElMessage.error(res.msg || '更新失败')
      }
    } catch (error) {
      ElMessage.error('更新失败')
    } finally {
      profileSaving.value = false
    }
  }

  const savePassword = async () => {
    if (!passwordFormRef.value) return

    try {
      await passwordFormRef.value.validate()
    } catch {
      return
    }

    passwordSaving.value = true
    try {
      const res = await changePassword({
        oldPassword: passwordForm.oldPassword,
        newPassword: passwordForm.newPassword,
        confirmPassword: passwordForm.confirmPassword,
      })

      if (res.code === 200) {
        ElMessage.success('密码修改成功')
        passwordForm.oldPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
      } else {
        ElMessage.error(res.msg || '修改失败')
      }
    } catch (error) {
      ElMessage.error('修改失败')
    } finally {
      passwordSaving.value = false
    }
  }

  onMounted(() => {
    loadProfile()
  })
</script>

<style lang="scss" scoped>
  .profile-page {
    max-width: 800px;
    margin: 0 auto;
  }

  .profile-card {
    position: relative;
    border-radius: $border-radius-large;
    overflow: hidden;
    background: $surface-color;
    box-shadow: $box-shadow-base;
    margin-bottom: 24px;

    .profile-card-bg {
      height: 120px;
      background: linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #db2777 100%);
    }

    .profile-card-content {
      display: flex;
      align-items: flex-end;
      gap: 24px;
      padding: 0 32px 28px;
      margin-top: -48px;
      position: relative;
    }

    .avatar {
      width: 96px;
      height: 96px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 36px;
      font-weight: 700;
      color: #fff;
      border: 4px solid $surface-color;
      box-shadow: $box-shadow-base;
      flex-shrink: 0;
      transition: transform 0.3s ease;

      &:hover {
        transform: scale(1.05);
      }
    }

    .profile-info {
      flex: 1;
      padding-top: 52px;

      .display-name {
        font-size: 24px;
        font-weight: 700;
        color: $text-primary;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
      }

      .username {
        font-size: 14px;
        color: $text-secondary;
        margin-bottom: 8px;
      }

      .bio {
        font-size: 14px;
        color: $text-regular;
        line-height: 1.6;
        margin-bottom: 12px;
      }

      .meta-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .el-tag {
          display: flex;
          align-items: center;
          gap: 4px;
        }
      }
    }
  }

  .settings-card {
    border: none !important;

    :deep(.el-tabs__header) {
      margin-bottom: 24px;
    }

    :deep(.el-tabs__item) {
      font-size: 15px;
      font-weight: 500;
    }
  }

  .settings-form {
    max-width: 500px;

    :deep(.el-form-item__label) {
      font-weight: 600;
      color: $text-primary;
      margin-bottom: 4px;
    }
  }

  .color-picker {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;

    .color-option {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
      border: 3px solid transparent;

      &:hover {
        transform: scale(1.15);
      }

      &.active {
        border-color: $text-primary;
        box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
      }

      .el-icon {
        color: #fff;
        font-size: 16px;
      }
    }
  }

  // Mobile adjustments
  @media (max-width: 640px) {
    .profile-card {
      .profile-card-content {
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 0 20px 24px;
      }

      .profile-info {
        padding-top: 12px;

        .meta-tags {
          justify-content: center;
        }
      }
    }
  }
</style>
