/**
 * 表单相关组合式函数
 * 提供表单验证、提交等通用逻辑
 */

import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * 使用表单
 * @param {Object} initialValues - 初始值
 * @param {Object} rules - 验证规则
 */
export function useForm(initialValues = {}, rules = {}) {
  const formRef = ref(null)
  const formData = reactive({ ...initialValues })
  const loading = ref(false)

  // 重置表单
  const resetForm = () => {
    if (formRef.value) {
      formRef.value.resetFields()
    }
    Object.keys(initialValues).forEach((key) => {
      formData[key] = initialValues[key]
    })
  }

  // 验证表单
  const validate = () => {
    return new Promise((resolve, reject) => {
      if (!formRef.value) {
        resolve(true)
        return
      }

      formRef.value.validate((valid, fields) => {
        if (valid) {
          resolve(true)
        } else {
          reject(fields)
        }
      })
    })
  }

  // 验证单个字段
  const validateField = (prop) => {
    return new Promise((resolve) => {
      if (!formRef.value) {
        resolve(true)
        return
      }

      formRef.value.validateField(prop, (errorMessage) => {
        resolve(!errorMessage)
      })
    })
  }

  // 清除验证
  const clearValidate = (props) => {
    if (formRef.value) {
      formRef.value.clearValidate(props)
    }
  }

  // 提交表单
  const submit = async (submitFn) => {
    try {
      await validate()

      loading.value = true
      const result = await submitFn(formData)

      if (result.code === 200) {
        ElMessage.success(result.msg || '提交成功')
        return { success: true, data: result.data }
      } else {
        ElMessage.error(result.msg || '提交失败')
        return { success: false, msg: result.msg }
      }
    } catch (error) {
      if (error && typeof error === 'object' && !error.message) {
        // 验证失败
        ElMessage.warning('请检查表单填写')
      } else {
        ElMessage.error(error.message || '提交失败')
      }
      return { success: false, error }
    } finally {
      loading.value = false
    }
  }

  // 设置字段值
  const setFieldValue = (field, value) => {
    formData[field] = value
  }

  // 设置多个字段值
  const setFieldsValue = (values) => {
    Object.assign(formData, values)
  }

  // 获取字段值
  const getFieldValue = (field) => {
    return formData[field]
  }

  // 获取所有值
  const getFieldsValue = () => {
    return { ...formData }
  }

  return {
    formRef,
    formData,
    loading,
    rules,
    resetForm,
    validate,
    validateField,
    clearValidate,
    submit,
    setFieldValue,
    setFieldsValue,
    getFieldValue,
    getFieldsValue,
  }
}

/**
 * 常用验证规则
 */
export const formRules = {
  required: (message = '此字段为必填项') => ({
    required: true,
    message,
    trigger: 'blur',
  }),

  email: {
    type: 'email',
    message: '请输入有效的邮箱地址',
    trigger: 'blur',
  },

  phone: {
    pattern: /^1[3-9]\d{9}$/,
    message: '请输入有效的手机号码',
    trigger: 'blur',
  },

  minLength: (min, message) => ({
    min,
    message: message || `最少输入 ${min} 个字符`,
    trigger: 'blur',
  }),

  maxLength: (max, message) => ({
    max,
    message: message || `最多输入 ${max} 个字符`,
    trigger: 'blur',
  }),

  range: (min, max, message) => ({
    min,
    max,
    message: message || `长度在 ${min} 到 ${max} 个字符之间`,
    trigger: 'blur',
  }),
}
