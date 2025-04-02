<template>
  <div class="create-post-container">
    <h1>发布新动态</h1>
    
    <el-card class="create-post-card">
      <el-form :model="postForm" ref="postForm" :rules="rules">
        <el-form-item prop="content">
          <el-input
            type="textarea"
            v-model="postForm.content"
            :rows="4"
            placeholder="分享你的动态..."
          ></el-input>
        </el-form-item>
        
        <div class="upload-container">
          <el-upload
            action="#"
            list-type="picture-card"
            :file-list="fileList"
            :on-preview="handlePictureCardPreview"
            :on-remove="handleRemove"
            :before-upload="beforeUpload"
            :limit="9"
            :auto-upload="false"
            :on-exceed="handleExceed"
            :on-change="handleFileChange"
            multiple
          >
            <i class="el-icon-plus"></i>
            <div slot="tip" class="el-upload__tip">支持JPG/PNG/GIF文件，最多可上传9张图片</div>
          </el-upload>
          <el-dialog :visible.sync="dialogVisible" append-to-body>
            <img width="100%" :src="dialogImageUrl" alt="">
          </el-dialog>
        </div>
        
        <el-form-item v-if="user.is_teacher">
          <el-checkbox v-model="postForm.disable_comments">禁止评论</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitPost" :loading="submitting">发布</el-button>
          <el-button @click="$router.push('/moments')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import api from '@/api'

export default {
  name: 'CreatePost',
  data() {
    return {
      user: {},
      postForm: {
        content: '',
        disable_comments: false
      },
      fileList: [],
      dialogImageUrl: '',
      dialogVisible: false,
      submitting: false,
      rules: {
        content: [
          { required: true, message: '请输入动态内容', trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    // 检查用户登录状态
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      this.user = JSON.parse(storedUser)
      
      // 验证是否为教师身份
      if (!this.user.is_teacher) {
        this.$message.error('只有教师才能发布动态')
        this.$router.push('/moments')
        return
      }
    } else {
      this.$message.error('请先登录')
      this.$router.push('/login')
    }
  },
  methods: {
    handleRemove(file) {
      // 找到并移除已上传的文件
      const index = this.fileList.findIndex(f => f.uid === file.uid)
      if (index !== -1) {
        this.fileList.splice(index, 1)
      }
    },
    handlePictureCardPreview(file) {
      this.dialogImageUrl = file.url
      this.dialogVisible = true
    },
    handleExceed() {
      this.$message.warning('最多只能上传9张图片')
    },
    beforeUpload(file) {
      const isValidType = ['image/jpeg', 'image/png', 'image/gif'].includes(file.type)
      const isLt5M = file.size / 1024 / 1024 < 5
      
      if (!isValidType) {
        this.$message.error('只能上传JPG/PNG/GIF格式图片!')
        return false
      }
      
      if (!isLt5M) {
        this.$message.error('图片大小不能超过5MB!')
        return false
      }
      
      return true
    },
    async handleFileChange(file, fileList) {
      // 将当前文件列表保存到组件状态中
      this.fileList = fileList
      
      // 我们将在submitPost方法中统一上传所有文件
    },
    async submitPost() {
      try {
        await this.$refs.postForm.validate()
        
        this.submitting = true
        
        // 如果有文件要上传
        let imageFilenames = ''
        if (this.fileList.length > 0) {
          // 构造FormData，包含所有文件
          const formData = new FormData()
          
          // 添加所有文件到formData
          this.fileList.forEach(file => {
            if (file.raw) {
              formData.append('files[]', file.raw)
              console.log('添加文件到表单:', file.name, file.size)
            } else {
              console.warn('文件缺少raw属性:', file)
            }
          })
          
          formData.append('user_id', this.user.id)
          
          // 调试信息
          console.log('上传文件数量:', this.fileList.length)
          for (let pair of formData.entries()) {
            console.log('表单数据:', pair[0], typeof pair[1])
          }
          
          try {
            console.log('开始上传图片...')
            const uploadResponse = await api.post('/upload', formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            })
            
            console.log('上传响应:', uploadResponse.data)
            
            if (uploadResponse.data && uploadResponse.data.filenames) {
              // 保存返回的文件名列表
              imageFilenames = uploadResponse.data.filenames.join(',')
              this.$message.success(uploadResponse.data.message || '图片上传成功')
            }
          } catch (error) {
            console.error('上传图片失败:', error)
            if (error.response) {
              console.error('错误响应:', error.response.status, error.response.data)
            }
            if (error.response && error.response.data && error.response.data.error) {
              this.$message.error(error.response.data.error)
              // 不阻止继续发布，可能有些图片上传成功了
            } else {
              this.$message.error('上传图片失败，但将继续发布文字内容')
            }
          }
        }
        
        // 发布动态，包含已上传的图片文件名
        const response = await api.post('/posts', {
          content: this.postForm.content,
          images: imageFilenames,
          user_id: this.user.id,
          disable_comments: this.postForm.disable_comments
        })
        
        this.$message.success(response.data.message || '发布成功')
        this.$router.push('/moments')
      } catch (error) {
        console.error('发布失败:', error)
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else if (typeof error === 'string') {
          // Form validation error
          return
        } else {
          this.$message.error('发布失败，请稍后再试')
        }
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.create-post-container {
  max-width: 428px;  /* iPhone 13 Pro Max 宽度 */
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
  color: #409EFF;
}

.create-post-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.upload-container {
  margin: 20px 0;
}

.el-upload__tip {
  line-height: 1.2;
  padding-top: 5px;
  color: #909399;
}

@media screen and (max-width: 428px) {
  .create-post-container {
    padding: 15px;
  }
  
  .el-upload--picture-card {
    width: 80px;
    height: 80px;
    line-height: 84px;
  }
}
</style> 