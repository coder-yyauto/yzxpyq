<template>
  <div class="moments-container">
    <!-- 顶部导航栏 -->
    <div class="top-nav">
      <h1>朋友圈</h1>
      <div class="user-info">
        <el-switch
          v-model="useExactTime"
          active-text="精确时间"
          inactive-text="相对时间"
          @change="updateTimeFormat"
          style="margin-right: 15px;"
        ></el-switch>
        <span :class="{'teacher-name': user.is_teacher}">{{ user.real_name }}</span>
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="el-dropdown-link">
            <i class="el-icon-arrow-down"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="profile">个人资料</el-dropdown-item>
            <el-dropdown-item command="admin" v-if="user.is_admin">管理控制台</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </div>
    
    <div class="action-btns">
      <el-button type="primary" @click="$router.push('/create')">发布新动态</el-button>
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="15" animated />
    </div>
    
    <div v-else-if="posts.length === 0" class="empty-container">
      <p>暂无动态，去发布一条吧！</p>
    </div>
    
    <div v-else class="posts-container">
      <div v-for="post in posts" :key="post.id" class="post-card">
        <div class="post-header">
          <div class="post-user-info">
            <h3 :class="{'teacher-name': post.is_teacher}">{{ post.real_name }}</h3>
            <span class="post-time">{{ formatTime(post.created_at) }}</span>
          </div>
          <div class="post-operations">
            <el-dropdown v-if="canManagePost(post)" @command="handlePostAction($event, post)">
              <span class="el-dropdown-link">
                <i class="el-icon-more"></i>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="'delete'">删除动态</el-dropdown-item>
                  <el-dropdown-item :command="'toggle_comments'">
                    {{ post.disable_comments ? '允许评论' : '禁止评论' }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <div class="post-content">
          <p>{{ post.content }}</p>
          
          <!-- 九宫格图片显示 -->
          <div v-if="post.images && post.images.length > 0" :class="getImageGridClass(post.images.length)">
            <el-image
              v-for="(image, index) in post.images"
              :key="index"
              :src="'/api/images/' + image"
              :preview-src-list="post.images.map(img => '/api/images/' + img)"
              fit="cover"
              @error="handleImageError"
            >
              <template #error>
                <div class="image-error">
                  <i class="el-icon-picture-outline"></i>
                </div>
              </template>
            </el-image>
          </div>
        </div>
        
        <div class="post-footer">
          <div class="post-stats">
            <span class="like-btn" @click="likePost(post)">
              <i :class="post.is_liked ? 'el-icon-star-on' : 'el-icon-star-off'"></i>
              {{ post.like_count > 0 ? post.like_count : '点赞' }}
            </span>
            <span 
              :class="['comment-btn', {'comment-disabled': post.disable_comments}]" 
              @click="focusCommentInput(post)"
              v-if="!post.disable_comments"
            >
              <i class="el-icon-chat-line-square"></i>
              {{ post.comment_count > 0 ? post.comment_count : '评论' }}
            </span>
            <span class="comment-disabled" v-else>
              <i class="el-icon-chat-dot-square"></i>
              已禁止评论
            </span>
          </div>
          
          <!-- 评论列表 -->
          <div v-if="post.comments && post.comments.length > 0 && !post.disable_comments" class="post-comments">
            <div v-for="comment in post.comments" :key="comment.id" class="comment-item">
              <!-- 评论内容 -->
              <div class="comment-content">
                <span :class="{'teacher-name': comment.is_teacher}">{{ comment.real_name }}</span>
                <span class="comment-text">：{{ comment.content }}</span>
              </div>
              
              <!-- 评论操作 -->
              <div class="comment-actions">
                <span class="reply-btn" @click="showReplyInput(post.id, comment.id, comment.user_id, comment.real_name)">回复</span>
                <span class="delete-btn" v-if="canDeleteComment(comment)" @click="deleteComment(comment.id)">删除</span>
              </div>
              
              <!-- 回复列表 -->
              <div v-if="comment.replies && comment.replies.length > 0" class="replies-list">
                <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                  <!-- 回复内容 -->
                  <div class="reply-content">
                    <span :class="{'teacher-name': reply.is_teacher}">{{ reply.real_name }}</span>
                    <span class="reply-text">回复</span>
                    <span :class="{'teacher-name': reply.replied_to_is_teacher}">{{ reply.replied_to_real_name }}</span>
                    <span class="reply-text">：{{ reply.content }}</span>
                  </div>
                  
                  <!-- 回复操作 -->
                  <div class="reply-actions">
                    <span class="reply-btn" @click="showReplyInput(post.id, comment.id, reply.user_id, reply.real_name)">回复</span>
                    <span class="delete-btn" v-if="canDeleteComment(reply)" @click="deleteComment(reply.id)">删除</span>
                  </div>
                </div>
              </div>
              
              <!-- 回复输入框 -->
              <div v-if="replyInfo.active && replyInfo.commentId === comment.id" class="reply-input-container">
                <el-input
                  v-model="replyInfo.content"
                  type="textarea"
                  :rows="2"
                  :placeholder="`回复 ${replyInfo.replyToName}...`"
                ></el-input>
                <div class="reply-btns">
                  <el-button size="mini" @click="cancelReply">取消</el-button>
                  <el-button type="primary" size="mini" @click="submitReply(post.id)">提交回复</el-button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 评论输入框 -->
          <div v-if="!post.disable_comments" class="comment-input-container" :id="`comment-input-${post.id}`">
            <el-input
              v-model="commentContent[post.id]"
              type="textarea"
              :rows="2"
              placeholder="发表评论..."
            ></el-input>
            <el-button type="primary" @click="submitComment(post.id)">评论</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/api'
import { formatDistanceToNow, format, addHours } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default {
  name: 'Moments',
  data() {
    return {
      loading: true,
      posts: [],
      user: {},
      commentContent: {},
      useExactTime: false, // 控制是否使用精确时间
      replyInfo: {
        active: false,
        postId: null,
        commentId: null,
        replyToUserId: null,
        replyToName: '',
        content: ''
      }
    }
  },
  created() {
    console.log('Moments组件创建')
    // 从本地存储获取用户信息
    const storedUser = localStorage.getItem('user')
    console.log('Moments - 本地存储中的用户字符串:', storedUser)
    
    // 读取用户的时间格式首选项
    const timeFormat = localStorage.getItem('timeFormat')
    if (timeFormat === 'exact') {
      this.useExactTime = true
    }
    
    if (!storedUser) {
      console.error('Moments - 本地存储中没有用户信息')
      this.$message.error('请先登录')
      this.$router.push('/login')
      return
    }
    
    try {
      this.user = JSON.parse(storedUser)
      console.log('Moments - 解析后的用户对象:', this.user)
      
      if (!this.user || !this.user.id) {
        console.error('Moments - 用户对象无效或缺少ID')
        this.$message.error('登录信息无效，请重新登录')
        localStorage.removeItem('user')
        this.$router.push('/login')
        return
      }
      
      this.fetchPosts()
    } catch (error) {
      console.error('Moments - 解析用户信息时出错:', error)
      this.$message.error('登录信息无效，请重新登录')
      localStorage.removeItem('user')
      this.$router.push('/login')
    }
  },
  methods: {
    handleCommand(command) {
      if (command === 'logout') {
        this.logout()
      } else if (command === 'profile') {
        this.$router.push('/profile')
      } else if (command === 'admin') {
        this.$router.push('/admin')
      }
    },
    logout() {
      localStorage.removeItem('user')
      this.$message.success('已退出登录')
      this.$router.push('/login')
    },
    async fetchPosts() {
      try {
        if (!this.user || !this.user.id) {
          this.$message.error('请先登录')
          this.$router.push('/login')
          return
        }
        
        this.loading = true
        const response = await api.get('/posts', {
          params: { user_id: this.user.id }
        })
        
        if (response.data && Array.isArray(response.data)) {
          this.posts = response.data
          // 初始化评论内容对象
          this.posts.forEach(post => {
            this.$set(this.commentContent, post.id, '')
          })
        } else {
          console.error('获取动态失败：数据格式错误', response.data)
          this.$message.error('获取动态失败：数据格式错误')
        }
      } catch (error) {
        console.error('获取动态失败:', error)
        if (error.response) {
          if (error.response.status === 401) {
            this.$message.error('登录已过期，请重新登录')
            localStorage.removeItem('user')
            this.$router.push('/login')
            return
          }
          if (error.response.data && error.response.data.error) {
            this.$message.error(error.response.data.error)
          } else {
            this.$message.error('获取动态失败')
          }
        } else {
          this.$message.error('网络错误，请稍后重试')
        }
      } finally {
        this.loading = false
      }
    },
    formatTime(timeString) {
      try {
        // 解析ISO格式的时间字符串
        const date = new Date(timeString)
        
        if (this.useExactTime) {
          // 精确的时间格式：年-月-日 时:分
          return format(date, 'yyyy-MM-dd HH:mm', { locale: zhCN })
        } else {
          // 相对时间格式：几小时前
          return formatDistanceToNow(date, { addSuffix: true, locale: zhCN })
        }
      } catch (e) {
        console.error('时间格式化错误:', e, timeString)
        return timeString
      }
    },
    getImageGridClass(count) {
      if (count === 1) return 'image-grid-1'
      if (count === 2) return 'image-grid-2'
      if (count === 3) return 'image-grid-3'
      if (count === 4) return 'image-grid-4'
      if (count <= 6) return 'image-grid-6'
      return 'image-grid-9'
    },
    previewImage(images, index) {
      // 添加前缀以获取完整URL
      const fullImageUrl = `/api/images/${images[index]}`
      this.$msgbox({
        title: '图片预览',
        message: this.$createElement('img', {
          attrs: {
            src: fullImageUrl,
            alt: '预览图片',
            style: 'max-width: 100%; max-height: 80vh;'
          }
        }),
        showCancelButton: false,
        confirmButtonText: '关闭',
        customClass: 'image-preview-dialog'
      })
    },
    async likePost(post) {
      try {
        const response = await api.post(`/posts/${post.id}/like`, {
          user_id: this.user.id
        })
        
        // 更新点赞状态
        post.is_liked = response.data.is_liked
        post.like_count = response.data.likes
        
        // 提示用户
        this.$message.success(response.data.message)
      } catch (error) {
        console.error('点赞失败:', error)
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('点赞失败')
        }
      }
    },
    focusCommentInput(post) {
      if (post.disable_comments) return
      
      this.$nextTick(() => {
        const commentInput = document.getElementById(`comment-input-${post.id}`)
        if (commentInput) {
          commentInput.querySelector('textarea').focus()
        }
      })
    },
    async submitComment(postId) {
      const content = this.commentContent[postId]
      if (!content || !content.trim()) {
        this.$message.warning('评论内容不能为空')
        return
      }
      
      try {
        const response = await api.post(`/posts/${postId}/comments`, {
          content,
          user_id: this.user.id
        })
        
        // 清空评论内容
        this.$set(this.commentContent, postId, '')
        
        // 刷新动态列表
        this.fetchPosts()
        
        // 提示用户
        this.$message.success(response.data.message)
      } catch (error) {
        console.error('评论失败:', error)
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('评论失败')
        }
      }
    },
    showReplyInput(postId, commentId, userId, name) {
      this.replyInfo = {
        active: true,
        postId,
        commentId,
        replyToUserId: userId,
        replyToName: name,
        content: ''
      }
    },
    cancelReply() {
      this.replyInfo.active = false
      this.replyInfo.content = ''
    },
    async submitReply(postId) {
      if (!this.replyInfo.content || !this.replyInfo.content.trim()) {
        this.$message.warning('回复内容不能为空')
        return
      }
      
      try {
        const response = await api.post(`/posts/${postId}/comments`, {
          content: this.replyInfo.content,
          user_id: this.user.id,
          parent_id: this.replyInfo.commentId,
          replied_to_user_id: this.replyInfo.replyToUserId
        })
        
        // 清空回复内容并隐藏回复框
        this.cancelReply()
        
        // 刷新动态列表
        this.fetchPosts()
        
        // 提示用户
        this.$message.success(response.data.message)
      } catch (error) {
        console.error('回复失败:', error)
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('回复失败')
        }
      }
    },
    canDeleteComment(comment) {
      // 管理员可以删除任何评论
      if (this.user.is_admin) return true
      
      // 教师可以删除普通用户的评论
      if (this.user.is_teacher && !comment.is_teacher) return true
      
      // 所有用户都可以删除自己的评论
      return comment.user_id === this.user.id
    },
    async deleteComment(commentId) {
      try {
        const confirmed = await this.$confirm('确定要删除这条评论吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).catch(() => false)
        
        if (!confirmed) return
        
        const response = await api.delete(`/comments/${commentId}`, {
          params: { user_id: this.user.id }
        })
        
        // 刷新动态列表
        this.fetchPosts()
        
        // 提示用户
        this.$message.success(response.data.message)
      } catch (error) {
        console.error('删除评论失败:', error)
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('删除评论失败')
        }
      }
    },
    async handlePostAction(command, post) {
      if (command === 'delete') {
        this.deletePost(post.id)
      } else if (command === 'toggle_comments') {
        this.toggleComments(post.id)
      }
    },
    async deletePost(postId) {
      try {
        const confirmed = await this.$confirm('确定要删除这条动态吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).catch(() => false)
        
        if (!confirmed) return
        
        const response = await api.delete(`/posts/${postId}`, {
          params: { user_id: this.user.id }
        })
        
        // 刷新动态列表
        this.fetchPosts()
        
        // 提示用户
        this.$message.success(response.data.message)
      } catch (error) {
        console.error('删除动态失败:', error)
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('删除动态失败')
        }
      }
    },
    async toggleComments(postId) {
      try {
        const response = await api.put(`/posts/${postId}/toggle-comments`, {
          user_id: this.user.id
        })
        
        // 刷新动态列表
        this.fetchPosts()
        
        // 提示用户
        this.$message.success(response.data.message)
      } catch (error) {
        console.error('修改评论设置失败:', error)
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('修改评论设置失败')
        }
      }
    },
    updateTimeFormat() {
      // 保存用户的时间格式首选项
      localStorage.setItem('timeFormat', this.useExactTime ? 'exact' : 'relative')
      // 刷新动态以更新时间显示
      this.fetchPosts()
    },
    canManagePost(post) {
      // 添加调试日志
      console.log('Current User:', this.user)
      console.log('Post:', post)
      console.log('Post User ID:', post.user_id, typeof post.user_id)
      console.log('Current User ID:', this.user.id, typeof this.user.id)
      
      // 确保ID类型一致
      const postUserId = parseInt(post.user_id)
      const currentUserId = parseInt(this.user.id)
      
      // 管理员可以管理任何动态
      if (this.user.is_admin) return true
      
      // 教师可以管理普通用户的动态
      if (this.user.is_teacher && !post.is_teacher) return true
      
      // 所有用户都可以管理自己的动态
      const canManage = postUserId === currentUserId
                       
      console.log('Can Manage:', canManage)
      return canManage
    },
    handleImageError(e) {
      console.error('图片加载失败:', e);
      // 可以在这里添加重试逻辑或显示默认图片
    }
  }
}
</script>

<style scoped>
.moments-container {
  max-width: 428px;  /* iPhone 13 Pro Max 宽度 */
  margin: 0 auto;
  padding: 15px;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eaeaea;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
}

.el-dropdown-link {
  cursor: pointer;
  color: #909399;
  font-size: 18px;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-dropdown-link:hover {
  color: #409EFF;
}

h1 {
  font-size: 22px;
  color: #409EFF;
  margin: 0;
}

.action-btns {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  gap: 10px;
}

.loading-container, .empty-container {
  margin-top: 20px;
  text-align: center;
}

.empty-container p {
  color: #909399;
  font-size: 16px;
}

.posts-container {
  margin-top: 20px;
}

.post-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 15px;
  overflow: hidden;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.post-user-info {
  display: flex;
  flex-direction: column;
}

.post-user-info h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.teacher-name {
  color: #409EFF;
  font-weight: bold;
}

.post-time {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.post-operations {
  display: flex;
  gap: 10px;
  align-items: center;
}

.post-content {
  margin-top: 10px;
  margin-bottom: 15px;
}

.post-content p {
  margin: 0;
  font-size: 15px;
  line-height: 1.5;
  word-break: break-word;
}

/* 九宫格图片样式 */
.post-images {
  margin-top: 10px;
  overflow: hidden;
}

.image-grid-1 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 4px;
  max-width: 66%;
}

.image-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
}

.image-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.image-grid-4 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 4px;
}

.image-grid-6 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 4px;
}

.image-grid-9 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 4px;
}

.image-item {
  position: relative;
  overflow: hidden;
  background-color: #f5f5f5;
  aspect-ratio: 1;
  border-radius: 4px;
}

.post-image {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.3s;
}

.post-image:hover {
  transform: scale(1.03);
}

.image-error {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  color: #909399;
  font-size: 24px;
  background-color: #f5f5f5;
}

.post-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}

.post-stats {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 10px;
  gap: 20px;
}

.like-btn, .comment-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  cursor: pointer;
}

.comment-disabled {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #909399;
  cursor: not-allowed;
}

.like-btn i.el-icon-star-on {
  color: #409EFF;
}

.post-comments {
  margin-top: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
  padding: 10px;
}

.comment-item {
  margin-bottom: 10px;
}

.comment-content {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 5px;
}

.comment-text {
  color: #606266;
  word-break: break-word;
}

.comment-actions, .reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  font-size: 12px;
  margin-bottom: 5px;
}

.reply-btn, .delete-btn {
  color: #909399;
  cursor: pointer;
}

.reply-btn:hover, .delete-btn:hover {
  color: #409EFF;
}

.replies-list {
  margin-left: 15px;
  margin-top: 5px;
  margin-bottom: 5px;
}

.reply-item {
  margin-bottom: 8px;
}

.reply-content {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 3px;
}

.reply-text {
  color: #606266;
  margin: 0 3px;
}

.reply-input-container, .comment-input-container {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reply-btns {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.image-preview-dialog {
  max-width: 90vw;
}
</style> 