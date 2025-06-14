<template>
  <div class="post-detail">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>{{ post.user.username }}</span>
          <div class="header-operations">
            <!-- 只有发布者、教师或管理员可以删除动态 -->
            <el-button 
              v-if="canDeletePost"
              type="danger" 
              size="small" 
              @click="handleDeletePost"
            >删除动态</el-button>
            <!-- 只有发布者、教师或管理员可以禁止评论 -->
            <el-button 
              v-if="canToggleComments"
              :type="post.comments_disabled ? 'success' : 'warning'"
              size="small" 
              @click="handleToggleComments"
            >{{ post.comments_disabled ? '允许评论' : '禁止评论' }}</el-button>
          </div>
        </div>
      </template>
      <!-- 动态内容 -->
      <div class="post-content">{{ post.content }}</div>
      <!-- 评论列表 -->
      <div class="comments-section">
        <div v-for="comment in post.comments" :key="comment.id" class="comment-item">
          <div class="comment-header">
            <span>{{ comment.user.username }}</span>
            <!-- 只有评论者可以删除评论 -->
            <el-button 
              v-if="comment.user_id === currentUser.id"
              type="danger" 
              size="small" 
              @click="handleDeleteComment(comment.id)"
            >删除评论</el-button>
          </div>
          <div class="comment-content">{{ comment.content }}</div>
          <!-- 回复列表 -->
          <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
            <div class="reply-header">
              <span>{{ reply.user.username }}</span>
              <!-- 只有回复者可以删除回复 -->
              <el-button 
                v-if="reply.user_id === currentUser.id"
                type="danger" 
                size="small" 
                @click="handleDeleteComment(reply.id)"
              >删除回复</el-button>
            </div>
            <div class="reply-content">{{ reply.content }}</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      post: {},
      currentUser: {},
      // ... existing data
    }
  },
  computed: {
    canDeletePost() {
      return this.post.user_id === this.currentUser.id || 
             this.currentUser.is_teacher || 
             this.currentUser.is_admin
    },
    canToggleComments() {
      return this.post.user_id === this.currentUser.id || 
             this.currentUser.is_teacher || 
             this.currentUser.is_admin
    }
  },
  methods: {
    async handleDeletePost() {
      try {
        await this.$confirm('确定要删除这条动态吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await this.$axios.delete(`/api/posts/${this.post.id}`)
        this.$message.success('动态已删除')
        this.$router.push('/posts')
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error(error.response?.data?.error || '删除失败')
        }
      }
    },
    async handleToggleComments() {
      try {
        const response = await this.$axios.post(`/api/posts/${this.post.id}/toggle_comments`)
        this.post.comments_disabled = response.data.comments_disabled
        this.$message.success(response.data.message)
      } catch (error) {
        this.$message.error(error.response?.data?.error || '操作失败')
      }
    },
    async handleDeleteComment(commentId) {
      try {
        await this.$confirm('确定要删除这条评论吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await this.$axios.delete(`/api/comments/${commentId}`)
        this.$message.success('评论已删除')
        this.fetchPostDetail()
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error(error.response?.data?.error || '删除失败')
        }
      }
    },
    // ... existing methods
  }
}
</script>

<style scoped>
.header-operations {
  display: flex;
  gap: 10px;
}
.comment-header, .reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}
// ... existing styles
</style> 