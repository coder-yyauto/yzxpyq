<template>
  <div class="first-login-container">
    <div class="first-login-form">
      <h2>首次登录信息完善</h2>
      <p class="info-text">请完善您的个人信息和修改初始密码</p>
      
      <el-form :model="userForm" :rules="rules" ref="userForm" label-width="100px">
        <el-form-item label="登录账号" prop="username">
          <el-input v-model="userForm.username" disabled></el-input>
        </el-form-item>
        
        <el-form-item label="姓名昵称" prop="real_name">
          <el-input v-model="userForm.real_name" placeholder="请输入2-5个汉字"></el-input>
        </el-form-item>
        
        <el-form-item label="新密码" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="请输入新密码（至少7位字母和数字组合）"></el-input>
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="userForm.confirmPassword" type="password" placeholder="请再次输入新密码"></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitForm('userForm')" :loading="loading">保存信息</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from 'vuex';

export default {
  name: 'FirstLogin',
  data() {
    // 密码验证
    const validatePassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'));
      } else if (value.length < 7) {
        callback(new Error('密码长度不能少于7位'));
      } else if (!/(?=.*[a-zA-Z])(?=.*[0-9])/.test(value)) {
        callback(new Error('密码必须包含字母和数字'));
      } else {
        if (this.userForm.confirmPassword !== '') {
          this.$refs.userForm.validateField('confirmPassword');
        }
        callback();
      }
    };
    
    // 确认密码验证
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'));
      } else if (value !== this.userForm.password) {
        callback(new Error('两次输入密码不一致'));
      } else {
        callback();
      }
    };
    
    // 真实姓名验证
    const validateRealName = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入姓名昵称'));
      } else if (value.length < 2 || value.length > 5) {
        callback(new Error('姓名昵称长度必须在2-5个汉字之间'));
      } else if (!/^[\u4e00-\u9fff]+$/.test(value)) {
        callback(new Error('姓名昵称必须是汉字'));
      } else {
        callback();
      }
    };
    
    return {
      userForm: {
        username: '',
        real_name: '',
        password: '',
        confirmPassword: '',
        user_id: null
      },
      rules: {
        real_name: [
          { max: 5, message: '姓名昵称长度不能超过5个汉字', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { validator: validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      },
      loading: false
    };
  },
  computed: {
    ...mapState({
      currentUser: state => state.user.currentUser
    })
  },
  created() {
    // 检查用户状态
    if (!this.currentUser) {
      this.$router.push('/login');
      return;
    }
    
    // 如果不是首次登录用户，跳转到主页
    if (!this.currentUser.is_first_login) {
      this.$router.push('/');
      return;
    }
    
    // 填充用户信息
    this.userForm.username = this.currentUser.username;
    this.userForm.user_id = this.currentUser.id;
    if (this.currentUser.real_name) {
      this.userForm.real_name = this.currentUser.real_name;
    }
  },
  methods: {
    submitForm(formName) {
      this.$refs[formName].validate((valid) => {
        if (valid) {
          this.loading = true;
          
          // 准备提交数据
          const updateData = {
            user_id: this.userForm.user_id,
            real_name: this.userForm.real_name,
            password: this.userForm.password
          };
          
          // 提交到后端API
          axios.post('/api/users/update-profile', updateData)
            .then(response => {
              this.loading = false;
              console.log('更新个人信息响应:', response.data);
              
              if (!response.data.user || !response.data.user.id) {
                console.error('更新响应缺少用户信息');
                this.$message.error('更新失败：响应数据无效');
                return;
              }
              
              // 更新本地存储的用户信息
              const userData = response.data.user;
              console.log('准备更新的用户数据:', userData);
              
              localStorage.setItem('user', JSON.stringify(userData));
              console.log('已更新本地存储');
              
              // 更新Vuex状态
              this.$store.commit('user/setCurrentUser', userData);
              console.log('已更新Vuex状态');
              
              // 再次确认用户信息已正确保存
              const savedUser = JSON.parse(localStorage.getItem('user') || '{}');
              console.log('从本地存储读取的更新后用户信息:', savedUser);
              
              if (!savedUser.id || savedUser.is_first_login) {
                console.error('用户信息未正确保存或is_first_login状态未更新');
                this.$message.error('更新失败：用户信息保存异常');
                return;
              }
              
              // 显示成功消息
              this.$message.success('个人信息更新成功');
              
              // 跳转到动态页面
              this.$router.push('/moments');
            })
            .catch(error => {
              this.loading = false;
              let errorMessage = '更新失败';
              if (error.response && error.response.data && error.response.data.error) {
                errorMessage = error.response.data.error;
              }
              this.$message.error(errorMessage);
            });
        } else {
          return false;
        }
      });
    }
  }
};
</script>

<style scoped>
.first-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.first-login-form {
  width: 500px;
  padding: 40px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  margin-bottom: 10px;
  color: #303133;
}

.info-text {
  text-align: center;
  color: #909399;
  margin-bottom: 30px;
}

.el-form-item {
  margin-bottom: 25px;
}
</style>
