<template>
  <div class="register-container">
    <h1>注册账号</h1>
    <el-form :model="form" :rules="rules" ref="form" label-width="80px" class="register-form">
      <el-form-item label="用户类型">
        <el-radio-group v-model="form.is_teacher">
          <el-radio :label="false">学生</el-radio>
          <el-radio :label="true">教师</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名"></el-input>
      </el-form-item>
      
      <el-form-item label="密码" prop="password">
        <el-input type="password" v-model="form.password" placeholder="请输入密码"></el-input>
      </el-form-item>
      
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input type="password" v-model="form.confirmPassword" placeholder="请再次输入密码"></el-input>
      </el-form-item>
      
      <el-form-item label="真实姓名" prop="real_name">
        <el-input v-model="form.real_name" placeholder="请输入真实姓名"></el-input>
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
      form: {
        username: '',
        password: '',
        confirmPassword: '',
        real_name: '',
        is_teacher: false,
        register_code: '',
        grade: '',
        class_name: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码至少6个字符', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, validator: validatePass, trigger: 'blur' }
        ],
        real_name: [
          { required: true, message: '请输入真实姓名', trigger: 'blur' }
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
  methods: {
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
            
            this.$message.success('注册成功')
            this.$router.push('/moments')
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

@media screen and (max-width: 428px) {
  .register-container {
    padding: 15px;
  }
  
  .register-form {
    padding: 15px;
  }
}
</style> 