<template>
  <div class="create-post-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>发布动态</h2>
          <el-button type="text" @click="$router.push('/moments')">返回</el-button>
        </div>
      </el-header>
      <el-main>
        <el-form :model="postForm" :rules="rules" ref="postForm" label-width="80px">
          <el-form-item label="内容" prop="content">
            <el-input
              type="textarea"
              v-model="postForm.content"
              :rows="4"
              placeholder="分享你的教学心得..."
            ></el-input>
          </el-form-item>
          <el-form-item label="图片">
            <el-upload
              class="upload-demo"
              action="/api/upload"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :on-remove="handleRemove"
              :before-upload="beforeUpload"
              multiple
              :limit="9"
              :data="{ user_id: user.id }"
            >
              <el-button size="small" type="primary">点击上传</el-button>
              <div slot="tip" class="el-upload__tip">最多上传9张图片，且每张不超过16MB</div>
            </el-upload>
            <div v-if="postForm.images.length > 0" class="image-grid">
              <div v-for="(image, index) in postForm.images" :key="index" class="image-item">
                <el-image
                  :src="image"
                  fit="cover"
                  class="preview-image"
                ></el-image>
                <div class="image-actions">
                  <el-button type="text" @click="handleRemove({ url: image })">删除</el-button>
                </div>
              </div>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSubmit">发布</el-button>
          </el-form-item>
        </el-form>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import axios from 'axios'
import api from '../api'

export default {
  name: 'CreatePost',
  data() {
    return {
      postForm: {
        content: '',
        images: []
      },
      user: JSON.parse(localStorage.getItem('user') || '{}'),
      rules: {
        content: [
          { required: true, message: '请输入内容', trigger: 'blur' },
          { max: 500, message: '内容不能超过500个字符', trigger: 'blur' }
        ]
      }
    }
  },
  methods: {
    handleUploadSuccess(response) {
      if (response.error) {
        this.$message.error(response.error)
        return
      }
      this.postForm.images.push(response.url)
    },
    handleUploadError(error) {
      this.$message.error('图片上传失败')
      console.error('Upload error:', error)
    },
    handleRemove(file) {
      const index = this.postForm.images.indexOf(file.url)
      if (index !== -1) {
        this.postForm.images.splice(index, 1)
      }
    },
    beforeUpload(file) {
      const isImage = file.type.startsWith('image/')
      const isLt16M = file.size / 1024 / 1024 < 16

      if (!isImage) {
        this.$message.error('只能上传图片文件!')
        return false
      }
      if (!isLt16M) {
        this.$message.error('图片大小不能超过 16MB!')
        return false
      }
      if (this.postForm.images.length >= 9) {
        this.$message.error('最多只能上传9张图片!')
        return false
      }
      return true
    },
    async handleSubmit() {
      try {
        await this.$refs.postForm.validate()
        const response = await api.post('/posts', {
          content: this.postForm.content,
          images: this.postForm.images.join(','),
          user_id: this.user.id
        })
        this.$message.success('发布成功')
        this.$router.push('/moments')
      } catch (error) {
        if (error.response) {
          this.$message.error(error.response.data.message)
        } else {
          this.$message.error('发布失败')
        }
      }
    }
  }
}
</script>

<style scoped>
.create-post-container {
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

.header-content h2 {
  margin: 0;
}

.el-main {
  padding: 20px;
  padding-top: 60px;  /* 为固定头部留出空间 */
}

.upload-demo {
  margin-bottom: 20px;
}

.el-upload__tip {
  margin-top: 10px;
  color: #666;
  font-size: 12px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 20px;
}

.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 4px;
  overflow: hidden;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-actions {
  position: absolute;
  top: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.5);
  padding: 5px;
  border-radius: 0 0 0 4px;
}

.image-actions .el-button {
  color: white;
  padding: 2px 5px;
}

.image-actions .el-button:hover {
  color: #409EFF;
}
</style> 