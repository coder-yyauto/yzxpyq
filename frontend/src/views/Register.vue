<template>
  <div class="register-container">
    <h1>用户注册</h1>
    
    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>
    
    <el-steps v-if="registerEnabled" :active="currentStep" finish-status="success" simple style="margin-bottom: 20px;" class="register-steps">
      <el-step title="填写信息"></el-step>
      <el-step title="注册成功"></el-step>
    </el-steps>
    
    <el-form v-if="!loading && currentStep === 0 && registerEnabled" :model="form" :rules="rules" ref="form" label-width="100px" class="register-form">
      <el-form-item label="登录账号" prop="username">
        <el-input v-model="form.username" placeholder="请输入登录账号"></el-input>
      </el-form-item>
      
      <el-form-item label="设置密码" prop="password">
        <el-input type="password" v-model="form.password" placeholder="请输入密码"></el-input>
      </el-form-item>
      
      <el-form-item label="确认密码" prop="confirm_password">
        <el-input type="password" v-model="form.confirm_password" placeholder="请再次输入密码"></el-input>
      </el-form-item>
      
      <el-form-item label="姓名昵称" prop="real_name">
        <el-input v-model="form.real_name" placeholder="请输入姓名昵称"></el-input>
      </el-form-item>
      
      <el-form-item label="身份" prop="is_teacher">
        <el-radio-group v-model="form.is_teacher">
          <el-radio :label="false">学生</el-radio>
          <el-radio :label="true">教师</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 教师注册码 -->
      <el-form-item v-if="form.is_teacher" label="注册码" prop="register_code">
        <el-input v-model="form.register_code" placeholder="请输入教师注册码"></el-input>
      </el-form-item>
      
      <!-- 学生年级班级 -->
      <template v-else>
        <el-form-item label="年级" prop="grade">
          <el-select v-model="form.grade" placeholder="请选择年级">
            <el-option v-for="i in 5" :key="i" :label="`${i}年级`" :value="i"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="班级" prop="class_name">
          <el-select v-model="form.class_name" placeholder="请选择班级">
            <el-option v-for="i in 6" :key="i" :label="`${i}班`" :value="i"></el-option>
          </el-select>
        </el-form-item>
      </template>
      
      <el-form-item>
        <el-button type="primary" @click="submitForm('form')" class="register-btn">注册</el-button>
        <el-button @click="$router.push('/login')" class="back-btn">返回登录</el-button>
      </el-form-item>
    </el-form>
    
    <div v-if="!loading && !registerEnabled" class="register-disabled">
      <i class="el-icon-warning-outline warning-icon"></i>
      <h2>注册功能已关闭</h2>
      <p>管理员已暂时关闭注册功能，请联系管理员老师。</p>
      <el-button type="primary" class="back-btn" @click="$router.push('/login')">返回登录</el-button>
    </div>
    
    <div v-if="!loading && currentStep === 1" class="success-container">
      <i class="el-icon-success success-icon"></i>
      <h2>注册成功</h2>
      <p>即将自动跳转到动态页面...</p>
    </div>
  </div>
</template>

<script>
import api from '@/api'

export default {
  name: 'Register',
  data() {
    // 密码一致性验证
    const validatePass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== this.form.password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }
    
    return {
      currentStep: 0,
      registerEnabled: true,
      loading: true,
      form: {
        username: '',
        password: '',
        confirm_password: '',
        real_name: '',
        is_teacher: false,
        register_code: '',
        grade: '',
        class_name: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入登录账号', trigger: 'blur' },
          { min: 6, max: 16, message: '长度在6到16个字符', trigger: 'blur' },
          { pattern: /^[a-zA-Z]/, message: '必须以字母开头', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 7, max: 20, message: '长度在7到20个字符', trigger: 'blur' },
          { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '必须包含字母和数字', trigger: 'blur' }
        ],
        confirm_password: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: validatePass, trigger: 'blur' }
        ],
        real_name: [
          { required: true, message: '请输入姓名昵称', trigger: 'blur' }
        ],
        register_code: [
          { required: true, message: '请输入教师注册码', trigger: 'blur' }
        ],
        grade: [
          { required: true, message: '请选择年级', trigger: 'change' }
        ],
        class_name: [
          { required: true, message: '请选择班级', trigger: 'change' }
        ]
      }
    }
  },
  created() {
    this.currentStep = 0;
    console.log('Register组件已创建，currentStep =', this.currentStep);
    this.checkRegisterStatus()
  },
  methods: {
    async checkRegisterStatus() {
      this.loading = true
      try {
        const response = await api.get('/system/config', {
          params: { key: 'register_enabled' }
        })
        if (response.data && response.data.register_enabled) {
          this.registerEnabled = response.data.register_enabled.toLowerCase() === 'true'
        }
      } catch (error) {
        console.error('获取注册状态失败:', error)
        // 默认允许注册
        this.registerEnabled = true
      } finally {
        this.loading = false
      }
    },
    submitForm(formName) {
      this.$refs[formName].validate(async (valid) => {
        if (valid) {
          try {
            console.log('注册表单提交:', this.form)
            
            // 检查学生是否提供了班级和年级
            if (!this.form.is_teacher) {
              if (!this.form.grade || !this.form.class_name) {
                this.$message.error('学生需要提供年级和班级信息')
                console.error('学生缺少年级或班级信息', this.form)
                return
              }
            }
            
            // 准备请求数据
            const requestData = {
              username: this.form.username,
              password: this.form.password,
              real_name: this.form.real_name
            }
            
            // 根据用户类型添加不同的信息
            if (this.form.is_teacher) {
              requestData.register_code = this.form.register_code
            } else {
              requestData.grade = parseInt(this.form.grade)
              requestData.class_name = parseInt(this.form.class_name)
            }
            
            console.log('发送注册请求:', requestData)
            
            const response = await api.post('/register', requestData)
            console.log('注册响应:', response.data)
            
            // 检查响应
            if (!response.data || !response.data.id) {
              this.$message.error('注册成功但返回的用户信息无效')
              console.error('注册响应缺少用户ID', response.data)
              return
            }
            
            // 保存用户信息到本地存储
            localStorage.setItem('user', JSON.stringify(response.data))
            console.log('用户信息已保存到本地存储')
            
            // 再次确认用户信息已正确保存
            const savedUser = JSON.parse(localStorage.getItem('user') || '{}')
            console.log('从本地存储读取的用户信息:', savedUser)
            
            // 设置步骤为注册成功
            this.currentStep = 1
            
            // 3秒后自动跳转到动态页
            setTimeout(() => {
              this.$message.success('注册成功')
              this.$router.push('/moments')
            }, 1500)
          } catch (error) {
            console.error('注册失败:', error)
            if (error.response && error.response.data && error.response.data.error) {
              this.$message.error(error.response.data.error)
            } else {
              this.$message.error('注册失败，请稍后再试')
            }
          }
        } else {
          return false
        }
      })
    }
  }
}
</script>

<style scoped>
.register-container {
  max-width: 428px;  /* iPhone 13 Pro Max 宽度 */
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  justify-content: center;
  box-sizing: border-box;
}

h1 {
  margin-bottom: 20px;
  color: #409EFF;
  font-size: 24px;
}

.register-form {
  width: 100%;
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.register-btn {
  width: 48%;
}

.back-btn {
  width: 48%;
  margin-left: 4%;
}

.success-container {
  text-align: center;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.success-icon {
  font-size: 60px;
  color: #67C23A;
  margin-bottom: 20px;
}

.register-disabled {
  text-align: center;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.warning-icon {
  font-size: 60px;
  color: #E6A23C;
  margin-bottom: 20px;
}

.loading-container {
  width: 100%;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

/* 防止步骤文字折行 */
.register-steps {
  width: 100%;
}

.register-steps .el-step__title {
  white-space: nowrap;
  font-size: 14px;
}

@media screen and (max-width: 428px) {
  .register-container {
    padding: 15px;
  }
  
  .register-form {
    padding: 15px;
  }
}
</style> 