<template>
  <div class="register-container">
    <el-card class="register-card">
      <div slot="header">
        <h2>注册</h2>
      </div>
      <el-form :model="registerForm" :rules="rules" ref="registerForm" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input type="password" v-model="registerForm.password"></el-input>
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="registerForm.real_name"></el-input>
        </el-form-item>
        <el-form-item label="身份" prop="is_teacher">
          <el-radio-group v-model="registerForm.is_teacher">
            <el-radio :label="false">学生</el-radio>
            <el-radio :label="true">教师</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="工号/学号" prop="number">
          <el-input v-model="registerForm.number"></el-input>
        </el-form-item>
        <template v-if="!registerForm.is_teacher">
          <el-form-item label="年级" prop="grade">
            <el-select v-model="registerForm.grade" placeholder="请选择年级">
              <el-option label="一年级" value="一年级"></el-option>
              <el-option label="二年级" value="二年级"></el-option>
              <el-option label="三年级" value="三年级"></el-option>
              <el-option label="四年级" value="四年级"></el-option>
              <el-option label="五年级" value="五年级"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="班级" prop="class_name">
            <el-select v-model="registerForm.class_name" placeholder="请选择班级">
              <el-option label="1班" value="1班"></el-option>
              <el-option label="2班" value="2班"></el-option>
              <el-option label="3班" value="3班"></el-option>
              <el-option label="4班" value="4班"></el-option>
              <el-option label="5班" value="5班"></el-option>
              <el-option label="6班" value="6班"></el-option>
            </el-select>
          </el-form-item>
        </template>
        <el-form-item v-if="registerForm.is_teacher" label="注册码" prop="register_code">
          <el-input v-model="registerForm.register_code"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRegister">注册</el-button>
          <el-button @click="$router.push('/login')">返回登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'Register',
  data() {
    return {
      registerForm: {
        username: '',
        password: '',
        real_name: '',
        is_teacher: false,
        number: '',
        grade: '',
        class_name: '',
        register_code: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
        ],
        real_name: [
          { required: true, message: '请输入真实姓名', trigger: 'blur' }
        ],
        number: [
          { 
            required: true, 
            message: '请输入工号', 
            trigger: 'blur',
            validator: (rule, value, callback) => {
              if (this.registerForm.is_teacher && !value) {
                callback(new Error('请输入工号'))
              } else {
                callback()
              }
            }
          }
        ],
        grade: [
          { required: true, message: '请选择年级', trigger: 'change' }
        ],
        class_name: [
          { required: true, message: '请选择班级', trigger: 'change' }
        ],
        register_code: [
          { 
            required: true, 
            message: '请输入教师注册码', 
            trigger: 'blur',
            validator: (rule, value, callback) => {
              if (this.registerForm.is_teacher && !value) {
                callback(new Error('请输入教师注册码'))
              } else {
                callback()
              }
            }
          }
        ]
      }
    }
  },
  methods: {
    async handleRegister() {
      try {
        await this.$refs.registerForm.validate()
        const response = await api.post('/register', this.registerForm)
        if (response.data.message === '注册成功') {
          this.$message.success('注册成功')
          this.$router.push('/login')
        }
      } catch (error) {
        if (error.response) {
          this.$message.error(error.response.data.message)
        } else {
          this.$message.error('注册失败')
        }
      }
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.register-card {
  width: 100%;
  max-width: 500px;
  margin: 20px;
}

.register-card h2 {
  text-align: center;
  margin: 0;
}
</style> 