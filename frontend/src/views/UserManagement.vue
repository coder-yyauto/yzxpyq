<template>
  <div class="user-management">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div class="header-operations">
            <el-upload
              class="upload-demo"
              action="/api/user/batch_import"
              :headers="headers"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :before-upload="beforeUpload"
              accept=".xlsx,.xls"
            >
              <el-button type="primary">批量导入用户</el-button>
              <template #tip>
                <div class="el-upload__tip">
                  请上传Excel文件，必须包含以下列：<br>
                  - 登录账号：学生登录账号<br>
                  - 年级：学生所在年级<br>
                  - 班级：学生所在班级<br>
                  注：导入的用户初始密码为123456
                </div>
              </template>
            </el-upload>
            <el-button type="primary" @click="showAddUserDialog">添加用户</el-button>
          </div>
        </div>
      </template>
      // ... existing code ...
    </el-card>
  </div>
</template>

<script>
// ... existing code ...
export default {
  // ... existing code ...
  methods: {
    // ... existing code ...
    beforeUpload(file) {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                     file.type === 'application/vnd.ms-excel';
      if (!isExcel) {
        this.$message.error('只能上传Excel文件！');
        return false;
      }
      return true;
    },
    handleUploadSuccess(response) {
      if (response.errors && response.errors.length > 0) {
        this.$message.warning(`${response.message}\n${response.errors.join('\n')}`);
      } else {
        this.$message.success(response.message);
        this.fetchUsers(); // 刷新用户列表
      }
    },
    handleUploadError(error) {
      this.$message.error('上传失败：' + (error.message || '未知错误'));
    },
    // ... existing code ...
  }
}
</script>

<style scoped>
// ... existing code ...
.header-operations {
  display: flex;
  gap: 10px;
  align-items: center;
}
// ... existing code ...
</style> 