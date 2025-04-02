<template>
  <div class="user-profile">
    <h1>个人资料</h1>
    <div class="profile-card">
      <div class="profile-header">
        <div class="user-info">
          <h2 :class="{'teacher-name': user.is_teacher}">{{ user.real_name }}</h2>
          <p><span class="label">身份:</span> {{ user.is_teacher ? '教师' : '学生' }}</p>
          <p v-if="!user.is_teacher">
            <span class="label">班级:</span> {{ user.grade }}年级{{ user.class_name }}班
          </p>
          <p><span class="label">用户名:</span> {{ user.username }}</p>
        </div>
      </div>
    </div>

    <div class="action-buttons">
      <el-button type="primary" @click="$router.push('/moments')">查看动态</el-button>
      <el-button type="success" @click="$router.push('/create')">发布新动态</el-button>
      <el-button type="danger" @click="logout">退出登录</el-button>
    </div>
  </div>
</template>

<script>
import api from '@/api'

export default {
  name: 'UserProfile',
  data() {
    return {
      user: {}
    }
  },
  created() {
    // 从本地存储获取用户信息
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      this.user = JSON.parse(storedUser)
    } else {
      this.$message.error('未登录')
      this.$router.push('/login')
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('user')
      this.$message.success('已退出登录')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.user-profile {
  max-width: 428px;  /* iPhone 13 Pro Max 宽度 */
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

h1 {
  margin-bottom: 20px;
  color: #409EFF;
}

.profile-card {
  width: 100%;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.profile-header {
  display: flex;
  align-items: flex-start;
}

.user-info {
  flex: 1;
}

.user-info h2 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 20px;
}

.label {
  font-weight: bold;
  color: #606266;
}

.teacher-name {
  color: #409EFF;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 20px;
}

@media screen and (max-width: 428px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 10px;
  }
  
  .action-buttons button {
    width: 100%;
  }
}
</style> 