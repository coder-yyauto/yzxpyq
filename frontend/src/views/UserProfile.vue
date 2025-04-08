<template>
  <div class="user-profile-container">
    <h1>个人资料</h1>
    
    <el-card class="profile-card">
      <div class="profile-info">
        <div class="field">
          <label>登录账号:</label>
          <span>{{ user.username }}</span>
        </div>
        <div class="field">
          <label>姓名昵称:</label>
          <span :class="{'teacher-name': user.is_teacher}">{{ user.real_name }}</span>
        </div>
        <div class="field" v-if="!user.is_teacher">
          <label>班级:</label>
          <span>{{ user.grade }}年{{ user.class_name }}班</span>
        </div>
        <div class="field">
          <label>身份:</label>
          <span>{{ user.is_teacher ? '教师' : '学生' }}</span>
        </div>
      </div>
    </el-card>
    
    <el-card class="password-card">
      <div slot="header">
        <span>修改密码</span>
      </div>
      
      <el-form ref="passwordForm" :model="passwordForm" :rules="passwordRules" label-width="100px">
        <el-form-item label="当前密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password></el-input>
        </el-form-item>
        
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password></el-input>
        </el-form-item>
        
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitPasswordChange" :loading="loading">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <div class="actions">
      <el-button @click="$router.push('/moments')">返回首页</el-button>
    </div>
  </div>
</template>

<script>
import api from '@/api'

export default {
  name: 'UserProfile',
  data() {
    // 密码验证规则
    const validatePassword = (rule, value, callback) => {
      if (value.length < 7) {
        callback(new Error('密码长度不能少于7位'))
      } else if (!/[a-zA-Z]/.test(value) || !/[0-9]/.test(value)) {
        callback(new Error('密码必须包含字母和数字'))
      } else {
        callback()
      }
    }
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.passwordForm.newPassword) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }
    
    return {
      user: {},
      loading: false,
      passwordForm: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      passwordRules: {
        oldPassword: [
          { required: true, message: '请输入当前密码', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { validator: validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    const storedUser = localStorage.getItem('user')
    
    if (!storedUser) {
      this.$message.error('请先登录')
      this.$router.push('/login')
      return
    }
    
    try {
      this.user = JSON.parse(storedUser)
      
      if (!this.user || !this.user.id) {
        this.$message.error('登录信息无效，请重新登录')
        localStorage.removeItem('user')
        this.$router.push('/login')
      }
    } catch (error) {
      this.$message.error('登录信息无效，请重新登录')
      localStorage.removeItem('user')
      this.$router.push('/login')
    }
  },
  methods: {
    submitPasswordChange() {
      this.$refs.passwordForm.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        this.loading = true
        
        try {
          const response = await api.put('/change-password', {
            user_id: this.user.id,
            old_password: this.passwordForm.oldPassword,
            new_password: this.passwordForm.newPassword
          })
          
          this.$message.success('密码修改成功')
          this.passwordForm.oldPassword = ''
          this.passwordForm.newPassword = ''
          this.passwordForm.confirmPassword = ''
          this.$refs.passwordForm.resetFields()
        } catch (error) {
          if (error.response && error.response.data && error.response.data.error) {
            this.$message.error(error.response.data.error)
          } else {
            this.$message.error('密码修改失败，请稍后重试')
          }
          console.error('密码修改失败:', error)
        } finally {
          this.loading = false
        }
      })
    }
  }
}
</script>

<style scoped>
.user-profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-card,
.password-card {
  margin-bottom: 20px;
}

.profile-info {
  margin-bottom: 20px;
}

.field {
  margin-bottom: 10px;
  display: flex;
}

.field label {
  font-weight: bold;
  width: 100px;
}

.teacher-name {
  color: #409EFF;
  font-weight: bold;
}

.actions {
  margin-top: 20px;
  text-align: center;
}
</style> 