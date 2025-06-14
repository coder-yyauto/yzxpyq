<template>
  <div class="post-list">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>动态列表</span>
          <el-button type="primary" @click="showCreatePostDialog">发布动态</el-button>
        </div>
      </template>
      
      <div v-for="post in posts" :key="post.id" class="post-item">
        <div class="post-header">
          <span class="username">{{ post.user.username }}</span>
          <div class="post-operations">
            <!-- 使用下拉菜单 -->
            <el-dropdown v-if="canManagePost(post)" @command="handleCommand($event, post)">
              <el-button type="primary" size="small">
                更多操作<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="'delete'">删除动态</el-dropdown-item>
                  <el-dropdown-item :command="'toggle_comments'">
                    {{ post.comments_disabled ? '允许评论' : '禁止评论' }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <div class="post-content">{{ post.content }}</div>
        <div class="post-footer">
          <span class="time">{{ formatTime(post.created_at) }}</span>
          <el-button type="text" @click="viewPostDetail(post.id)">查看详情</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ArrowDown } from '@element-plus/icons-vue'

export default {
  components: {
    ArrowDown
  },
  data() {
    return {
      posts: [],
      currentUser: {},
      loading: false
    }
  },
  async created() {
    // 获取当前用户信息
    try {
      const response = await this.$axios.get('/api/user/info')
      this.currentUser = response.data
      console.log('当前用户信息:', this.currentUser)
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
    // 获取动态列表
    await this.fetchPosts()
  },
  methods: {
    async fetchPosts() {
      try {
        this.loading = true
        const response = await this.$axios.get('/api/posts')
        this.posts = response.data
        console.log('获取到的动态列表:', this.posts)
      } catch (error) {
        console.error('获取动态列表失败:', error)
        this.$message.error('获取动态列表失败')
      } finally {
        this.loading = false
      }
    },
    canManagePost(post) {
      // 添加调试日志
      console.log('Current User:', this.currentUser)
      console.log('Post:', post)
      console.log('Post User ID:', post.user_id, typeof post.user_id)
      console.log('Current User ID:', this.currentUser.id, typeof this.currentUser.id)
      
      // 确保ID类型一致
      const postUserId = parseInt(post.user_id)
      const currentUserId = parseInt(this.currentUser.id)
      
      const canManage = postUserId === currentUserId || 
                       this.currentUser.is_teacher || 
                       this.currentUser.is_admin
                       
      console.log('Can Manage:', canManage)
      return canManage
    },
    formatTime(time) {
      if (!time) return ''
      const date = new Date(time)
      return date.toLocaleString()
    },
    viewPostDetail(postId) {
      this.$router.push(`/posts/${postId}`)
    },
    showCreatePostDialog() {
      this.$router.push('/posts/create')
    },
    async handleCommand(command, post) {
      switch (command) {
        case 'delete':
          await this.handleDeletePost(post.id)
          break
        case 'toggle_comments':
          await this.handleToggleComments(post.id)
          break
      }
    },
    async handleDeletePost(postId) {
      try {
        await this.$confirm('确定要删除这条动态吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await this.$axios.delete(`/api/posts/${postId}`)
        this.$message.success('动态已删除')
        this.fetchPosts() // 刷新列表
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error(error.response?.data?.error || '删除失败')
        }
      }
    },
    async handleToggleComments(postId) {
      try {
        const response = await this.$axios.post(`/api/posts/${postId}/toggle_comments`)
        this.$message.success(response.data.message)
        this.fetchPosts() // 刷新列表
      } catch (error) {
        this.$message.error(error.response?.data?.error || '操作失败')
      }
    },
  }
}
</script>

<style scoped>
.post-operations {
  display: flex;
  gap: 10px;
  align-items: center;
}
.post-item {
  margin-bottom: 20px;
  padding: 15px;
  border-bottom: 1px solid #eee;
}
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.post-content {
  margin: 10px 0;
}
.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  color: #999;
}
</style> 