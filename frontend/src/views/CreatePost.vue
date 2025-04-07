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
            name="files[]"
            accept="image/jpeg,image/png,image/gif,image/webp,image/bmp,image/svg+xml,image/tiff"
          >
            <i class="el-icon-plus"></i>
            <div slot="tip" class="el-upload__tip">支持JPG/PNG/GIF/WEBP/BMP/SVG/TIFF文件，最多可上传9张图片</div>
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
import axios from 'axios'

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
      
      // 检查用户是否被禁用
      if (!this.user.is_active) {
        this.$message.error('您的账号已被禁用，请联系管理员')
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
      const isValidType = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/svg+xml', 'image/tiff'].includes(file.type)
      const isLt5M = file.size / 1024 / 1024 < 5
      
      if (!isValidType) {
        this.$message.error('只能上传JPG/PNG/GIF/WEBP/BMP/SVG/TIFF格式图片!')
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
      console.log('文件列表已更新，当前文件数量:', this.fileList.length)
      console.log('新添加的文件:', file.name, file.size, file.type)
      
      // 我们将在submitPost方法中统一上传所有文件
    },
    async submitPost() {
      try {
        await this.$refs.postForm.validate()
        
        this.submitting = true
        console.log("开始发布流程")
        
        // 如果有文件要上传
        let imageFilenames = ''
        if (this.fileList.length > 0) {
          // 显示上传提示
          this.$message.info(`正在上传${this.fileList.length}张图片，请稍候...`)
          
          // 创建简单的FormData对象
          const formData = new FormData()
          
          // 添加用户ID
          formData.append('user_id', this.user.id)
          
          // 尝试多种方式提取文件对象
          let uploadedCount = 0
          
          for (let i = 0; i < this.fileList.length; i++) {
            const file = this.fileList[i]
            let fileObj = null
            
            // 检查raw属性（Element UI存储原始文件的位置）
            if (file.raw) {
              fileObj = file.raw
              console.log(`使用raw属性获取文件 ${i+1}: ${file.name}`)
            }
            // 检查originFileObj属性（某些UI库使用）
            else if (file.originFileObj) {
              fileObj = file.originFileObj
              console.log(`使用originFileObj属性获取文件 ${i+1}: ${file.name}`)
            }
            // 检查是否本身就是File对象
            else if (file instanceof File || file instanceof Blob) {
              fileObj = file
              console.log(`文件 ${i+1} 本身就是File对象: ${file.name}`)
            }
            
            // 如果我们成功获取了文件对象
            if (fileObj) {
              formData.append('files[]', fileObj)
              uploadedCount++
              console.log(`成功添加文件 ${i+1} 到formData: ${file.name}`)
            } else {
              console.error(`无法获取文件 ${i+1} 的原始对象: ${file.name}`)
            }
          }
          
          if (uploadedCount === 0) {
            this.$message.error('无法处理任何文件，请重新选择图片')
            this.submitting = false
            return
          }
          
          // 检查FormData对象是否有效
          console.log(`预计上传 ${uploadedCount} 张图片`)
          
          try {
            console.log('发送上传请求...')
            
            // 使用fetch发送上传请求
            const response = await fetch('/api/uploads', {
              method: 'POST',
              body: formData
            })
            
            // 检查响应状态
            if (!response.ok) {
              const errorText = await response.text()
              throw new Error(`上传失败 (${response.status}): ${errorText}`)
            }
            
            // 解析JSON响应
            const data = await response.json()
            console.log('上传响应:', data)
            
            if (data && data.filenames && data.filenames.length > 0) {
              imageFilenames = data.filenames.join(',')
              this.$message.success(`图片上传成功: ${data.message || ''}`)
            } else {
              throw new Error('服务器返回的响应缺少文件名')
            }
          } catch (uploadError) {
            console.error('图片上传失败:', uploadError)
            this.$message.error(`图片上传失败: ${uploadError.message}`)
            this.submitting = false
            return
          }
        }
        
        // 发布动态
        try {
          console.log('正在发布动态...')
          console.log('内容:', this.postForm.content)
          console.log('图片:', imageFilenames)
          
          const postResponse = await api.post('/posts', {
            content: this.postForm.content,
            images: imageFilenames,
            user_id: this.user.id,
            disable_comments: this.postForm.disable_comments
          });
          
          this.$message.success(postResponse.data.message || '发布成功');
          this.$router.push('/moments');
        } catch (postError) {
          console.error('发布失败:', postError)
          if (postError.response && postError.response.data && postError.response.data.error) {
            this.$message.error(postError.response.data.error)
          } else {
            this.$message.error(`发布失败: ${postError.message}`)
          }
        }
      } catch (error) {
        console.error('表单验证失败:', error)
        // 表单验证错误不需要显示提示
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