<template>
  <div class="moments-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>教学朋友圈</h2>
          <div class="user-info">
            <span>{{ user.real_name }}</span>
            <el-button type="text" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <div class="moments-content">
          <div v-if="user.is_teacher" class="create-post">
            <el-button type="primary" @click="$router.push('/create-post')">发布新动态</el-button>
          </div>
          <div class="posts-list">
            <el-card v-for="post in posts" :key="post.id" class="post-card">
              <div class="post-header">
                <span class="post-author">{{ post.real_name }}</span>
                <span class="post-time">{{ post.created_at }}</span>
              </div>
              <div class="post-content">
                {{ post.content }}
              </div>
              <div v-if="post.images && post.images.length" class="post-images">
                <el-image
                  v-for="(image, index) in post.images"
                  :key="index"
                  :src="image"
                  :preview-src-list="post.images"
                  fit="cover"
                  class="post-image"
                ></el-image>
              </div>
              <div class="post-actions">
                <el-button 
                  type="text" 
                  @click="handleLike(post)"
                  :class="{ 'liked': post.is_liked }"
                >
                  <i class="el-icon-star-off"></i>
                  {{ post.likes }}
                </el-button>
                <el-button type="text" @click="showCommentInput(post)">
                  <i class="el-icon-chat-dot-round"></i>
                  评论
                </el-button>
              </div>
              <div class="comments-section">
                <div v-for="comment in post.comments" :key="comment.id" class="comment-item">
                  <div class="comment-content">
                    <span class="comment-user">{{ comment.real_name }}</span>
                    <span class="comment-text">{{ comment.content }}</span>
                  </div>
                  <div class="comment-actions">
                    <el-button 
                      type="text" 
                      size="small" 
                      @click="showReplyInput(post, comment)"
                      v-if="comment.user_id !== user.id"
                    >
                      回复
                    </el-button>
                    <el-button 
                      type="text" 
                      size="small" 
                      @click="handleDeleteComment(post, comment)"
                      v-if="comment.user_id === user.id && !comment.replies.length"
                    >
                      删除
                    </el-button>
                  </div>
                  <div v-if="comment.replies && comment.replies.length" class="replies-section">
                    <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                      <div class="reply-content">
                        <span class="reply-user">{{ reply.real_name }}</span>
                        <span class="reply-text">{{ reply.content }}</span>
                      </div>
                      <div class="reply-actions">
                        <el-button 
                          type="text" 
                          size="small" 
                          @click="handleDeleteComment(post, reply)"
                          v-if="reply.user_id === user.id"
                        >
                          删除
                        </el-button>
                      </div>
                    </div>
                  </div>
                  <div v-if="post.replyingTo === comment.id" class="reply-input">
                    <el-input
                      v-model="post.replyContent"
                      placeholder="回复评论..."
                      @keyup.enter.native="submitReply(post, comment)"
                    >
                      <el-button slot="append" @click="submitReply(post, comment)">发送</el-button>
                    </el-input>
                  </div>
                </div>
                <div v-if="post.showCommentInput" class="comment-input">
                  <el-input
                    v-model="post.newComment"
                    placeholder="写下你的评论..."
                    @keyup.enter.native="submitComment(post)"
                  >
                    <el-button slot="append" @click="submitComment(post)">发送</el-button>
                  </el-input>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'Moments',
  data() {
    return {
      user: JSON.parse(localStorage.getItem('user') || '{}'),
      posts: []
    }
  },
  created() {
    this.fetchPosts()
  },
  methods: {
    async fetchPosts() {
      try {
        const response = await api.get('/posts')
        this.posts = response.data
      } catch (error) {
        this.$message.error('获取动态失败')
      }
    },
    async handleLike(post) {
      try {
        const response = await api.post(`/posts/${post.id}/like`)
        post.likes = response.data.likes
      } catch (error) {
        this.$message.error('点赞失败')
      }
    },
    showCommentInput(post) {
      this.$set(post, 'showCommentInput', true)
      this.$set(post, 'newComment', '')
    },
    showReplyInput(post, comment) {
      this.$set(post, 'replyingTo', comment.id)
      this.$set(post, 'replyContent', '')
    },
    async submitComment(post) {
      if (!post.newComment.trim()) return
      try {
        const response = await api.post(`/posts/${post.id}/comments`, {
          content: post.newComment,
          user_id: this.user.id
        })
        post.comments.push(response.data.comment)
        post.newComment = ''
        post.showCommentInput = false
      } catch (error) {
        this.$message.error('评论失败')
      }
    },
    async submitReply(post, comment) {
      if (!post.replyContent.trim()) return
      try {
        const response = await api.post(`/posts/${post.id}/comments`, {
          content: post.replyContent,
          user_id: this.user.id,
          parent_id: comment.id
        })
        comment.replies.push(response.data.comment)
        post.replyContent = ''
        post.replyingTo = null
      } catch (error) {
        this.$message.error('回复失败')
      }
    },
    async handleDeleteComment(post, comment) {
      try {
        await api.delete(`/comments/${comment.id}`, {
          data: { user_id: this.user.id }
        })
        if (comment.parent_id) {
          // 删除回复
          const parentComment = post.comments.find(c => c.id === comment.parent_id)
          if (parentComment) {
            parentComment.replies = parentComment.replies.filter(r => r.id !== comment.id)
          }
        } else {
          // 删除主评论
          post.comments = post.comments.filter(c => c.id !== comment.id)
        }
        this.$message.success('删除成功')
      } catch (error) {
        if (error.response) {
          this.$message.error(error.response.data.message)
        } else {
          this.$message.error('删除失败')
        }
      }
    },
    handleLogout() {
      localStorage.removeItem('user')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.moments-container {
  min-height: 100vh;
  background-color: #f5f5f5;
  max-width: 390px;  /* iPhone 13 Pro 宽度 */
  margin: 0 auto;
  position: relative;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.moments-content {
  padding: 20px;
  padding-top: 60px;  /* 为固定头部留出空间 */
}

.create-post {
  margin-bottom: 20px;
  text-align: right;
}

.post-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.post-header {
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.post-author {
  font-weight: bold;
  font-size: 16px;
}

.post-time {
  color: #999;
  font-size: 14px;
}

.post-content {
  margin-bottom: 10px;
  line-height: 1.6;
  font-size: 15px;
}

.post-images {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
  margin-bottom: 10px;
}

.post-image {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 4px;
}

.post-actions {
  border-top: 1px solid #eee;
  padding-top: 10px;
  margin-bottom: 10px;
}

.comments-section {
  background-color: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
}

.comment-item {
  margin-bottom: 10px;
  padding: 8px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.comment-content {
  margin-bottom: 4px;
}

.comment-user {
  font-weight: bold;
  margin-right: 5px;
  color: #409EFF;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

.replies-section {
  margin-left: 20px;
  margin-top: 8px;
  padding-left: 10px;
  border-left: 2px solid #eee;
}

.reply-item {
  margin-bottom: 8px;
  padding: 4px;
  background-color: #fff;
  border-radius: 4px;
}

.reply-content {
  margin-bottom: 4px;
}

.reply-user {
  font-weight: bold;
  margin-right: 5px;
  color: #409EFF;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.reply-input {
  margin-top: 8px;
  margin-left: 20px;
}

.comment-input {
  margin-top: 10px;
}

.post-actions .liked {
  color: #409EFF;
}

/* 适配 iPhone 13 Pro 的底部安全区域 */
@supports (padding-bottom: env(safe-area-inset-bottom)) {
  .moments-content {
    padding-bottom: calc(20px + env(safe-area-inset-bottom));
  }
}
</style> 