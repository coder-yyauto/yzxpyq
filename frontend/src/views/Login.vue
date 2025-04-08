<template>
  <div class="login-container">
    <h1>校园社交平台</h1>
    <el-form :model="form" :rules="rules" ref="form" label-width="80px" class="login-form">
      <el-form-item label="登录账号" prop="username">
        <el-input v-model="form.username" placeholder="请输入登录账号"></el-input>
      </el-form-item>
      
      <el-form-item label="登录密码" prop="password">
        <el-input type="password" v-model="form.password" placeholder="请输入登录密码" @keyup.enter.native="submitForm('form')"></el-input>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="submitForm('form')" class="login-btn">登录</el-button>
        <el-button @click="$router.push('/register')" class="register-btn">注册</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import api from '@/api'

export default {
  name: 'Login',
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入登录账号', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入登录密码', trigger: 'blur' }
        ]
      }
    }
  },
  methods: {
    submitForm(formName) {
      this.$refs[formName].validate(async (valid) => {
        if (valid) {
          try {
            console.log('提交登录表单:', this.form)
            const response = await api.post('/login', {
              username: this.form.username,
              password: this.form.password
            })
            
            console.log('登录响应数据:', response.data)
            
            // 确保响应数据包含必要的用户信息
            if (!response.data || !response.data.id) {
              this.$message.error('登录响应缺少用户信息')
              console.error('登录响应缺少用户ID:', response.data)
              return
            }
            
            // 保存用户信息到本地存储
            localStorage.setItem('user', JSON.stringify(response.data))
            console.log('用户信息已保存到本地存储')
            
            // 保存用户信息到Vuex
            this.$store.commit('user/setCurrentUser', response.data)
            console.log('用户信息已保存到Vuex状态')
            
            // 再次确认用户信息已正确保存
            const savedUser = JSON.parse(localStorage.getItem('user') || '{}')
            console.log('从本地存储读取的用户信息:', savedUser)
            
            if (!savedUser.id) {
              this.$message.error('用户信息未正确保存')
              console.error('本地存储中缺少用户ID')
              return
            }
            
            // 显示欢迎消息
            this.$message.success(`欢迎回来，${response.data.real_name || response.data.username}!`)
            
            // 判断是否首次登录
            if (response.data.is_first_login) {
              console.log('首次登录用户，重定向到首次登录页面')
              this.$router.push('/first-login')
            } else {
              // 普通登录，跳转到动态页面
              this.$router.push('/moments')
            }
          } catch (error) {
            console.error('登录失败:', error)
            if (error.response && error.response.data && error.response.data.error) {
              this.$message.error(error.response.data.error)
            } else {
              this.$message.error('登录失败，请稍后再试')
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
.login-container {
  max-width: 428px;  /* iPhone 13 Pro Max 宽度 */
  margin: 0 auto;
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  justify-content: center;
  box-sizing: border-box;
}

h1 {
  margin-bottom: 30px;
  color: #409EFF;
  font-size: 28px;
}

.login-form {
  width: 100%;
  background-color: #fff;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-btn {
  width: 48%;
}

.register-btn {
  width: 48%;
  margin-left: 4%;
}

@media screen and (max-width: 428px) {
  .login-container {
    padding: 20px 15px;
  }
  
  .login-form {
    padding: 20px;
  }
  
  h1 {
    font-size: 24px;
  }
}
</style> 