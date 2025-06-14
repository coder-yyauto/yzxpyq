<template>
  <div class="admin-container">
    <h1>管理员控制台</h1>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="用户管理" name="users">
        <div class="admin-header">
          <h2>用户管理</h2>
          <div class="admin-info">
            <span>管理员: <span class="admin-name">{{ admin.real_name }}</span></span>
            <el-button type="danger" size="small" @click="logout">退出登录</el-button>
          </div>
        </div>
        
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="10" animated />
        </div>
        
        <div v-else>
          <el-table
            :data="users"
            border
            style="width: 100%"
            :row-class-name="getRowClassName"
          >
            <el-table-column label="ID" prop="id" width="80"></el-table-column>
            <el-table-column label="登录账号" prop="username" width="120"></el-table-column>
            <el-table-column label="姓名昵称" width="120">
              <template slot-scope="scope">
                <span :class="{'teacher-name': scope.row.is_teacher}">{{ scope.row.real_name }}</span>
              </template>
            </el-table-column>
            <el-table-column label="身份" width="100">
              <template slot-scope="scope">
                {{ scope.row.is_teacher ? '教师' : '学生' }}
              </template>
            </el-table-column>
            <el-table-column label="班级" width="120">
              <template slot-scope="scope">
                <span v-if="!scope.row.is_teacher">{{ scope.row.grade }}年{{ scope.row.class_name }}班</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template slot-scope="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                  {{ scope.row.is_active ? '正常' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="注册时间" width="160">
              <template slot-scope="scope">
                {{ formatTime(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template slot-scope="scope">
                <el-button
                  size="mini"
                  :type="scope.row.is_active ? 'danger' : 'success'"
                  @click="toggleUserActive(scope.row)"
                >
                  {{ scope.row.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button
                  size="mini"
                  type="warning"
                  @click="showResetPasswordDialog(scope.row)"
                >
                  重置密码
                </el-button>
                <el-button
                  size="mini"
                  type="danger"
                  @click="showDeleteUserDialog(scope.row)"
                  v-if="scope.row.id !== admin.id"
                >
                  删除用户
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="动态管理" name="posts">
        <div class="admin-header">
          <h2>动态管理</h2>
          <div class="admin-info">
            <span>管理员: <span class="admin-name">{{ admin.real_name }}</span></span>
            <el-button type="danger" size="small" @click="logout">退出登录</el-button>
          </div>
        </div>
        
        <div v-if="postsLoading" class="loading-container">
          <el-skeleton :rows="15" animated />
        </div>
        
        <div v-else>
          <div v-for="post in posts" :key="post.id" class="post-card">
            <div class="post-header">
              <div class="post-user-info">
                <h3 :class="{'teacher-name': post.is_teacher}">{{ post.real_name }}</h3>
                <span class="post-time">{{ formatTime(post.created_at) }}</span>
              </div>
              <div class="post-actions">
                <el-button 
                  type="danger" 
                  size="mini" 
                  @click="deletePost(post.id)"
                >删除动态</el-button>
              </div>
            </div>
            
            <div class="post-content">
              <p>{{ post.content }}</p>
              
              <!-- 图片显示 -->
              <div v-if="post.images && post.images.length > 0" class="post-images">
                <div :class="getImageGridClass(post.images.length)">
                  <div v-for="(image, index) in post.images" :key="index" class="image-item">
                    <el-image 
                      :src="'/images/' + image" 
                      fit="cover"
                      class="post-image"
                    >
                      <div slot="error" class="image-error">
                        <i class="el-icon-picture-outline"></i>
                      </div>
                    </el-image>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="post-footer">
              <div class="post-stats">
                <span>
                  <i class="el-icon-star-on"></i>
                  {{ post.like_count > 0 ? post.like_count : '点赞' }}
                </span>
                <span>
                  <i class="el-icon-chat-line-square"></i>
                  {{ post.comment_count > 0 ? post.comment_count : '评论' }}
                </span>
              </div>
            </div>
            
            <!-- 评论列表 -->
            <div v-if="post.comments && post.comments.length > 0" class="post-comments">
              <h4>评论列表：</h4>
              <div v-for="comment in post.comments" :key="comment.id" class="comment-item">
                <!-- 评论内容 -->
                <div class="comment-content">
                  <span :class="{'teacher-name': comment.is_teacher}">{{ comment.real_name }}</span>
                  <span class="comment-text">：{{ comment.content }}</span>
                </div>
                
                <!-- 评论操作 -->
                <div class="comment-actions">
                  <el-button 
                    type="danger" 
                    size="mini" 
                    @click="deleteComment(comment.id)"
                  >删除评论</el-button>
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
                      <el-button 
                        type="danger" 
                        size="mini" 
                        @click="deleteComment(reply.id)"
                      >删除回复</el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <el-divider></el-divider>
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="系统管理" name="system" v-if="admin && admin.is_admin">
        <div class="admin-header">
          <h2>系统管理</h2>
          <div class="admin-info">
            <span>管理员: <span class="admin-name">{{ admin.real_name }}</span></span>
            <el-button type="danger" size="small" @click="logout">退出登录</el-button>
          </div>
        </div>
        
        <el-card class="system-card">
          <div slot="header">
            <span>系统操作</span>
          </div>
          
          <div class="system-actions">
            <el-button 
              type="primary" 
              @click="backupSystem" 
              :loading="backupLoading"
            >一键备份</el-button>
            
            <el-button 
              type="danger" 
              @click="showClearSystemDialog" 
              :loading="clearLoading"
            >一键清空</el-button>
          </div>
          
          <div class="system-description">
            <p><strong>一键备份：</strong>备份数据库和上传文件到安全位置</p>
            <p><strong>一键清空：</strong>清空所有数据（会先自动备份），仅保留管理员账号</p>
          </div>
        </el-card>
        
        <el-card class="system-card">
          <div slot="header">
            <span>系统设置</span>
          </div>
          
          <div class="setting-item">
            <span class="setting-label">用户注册功能：</span>
            <el-switch
              v-model="registerEnabled"
              active-text="开启"
              inactive-text="关闭"
              @change="updateRegisterSetting"
              :loading="settingLoading"
            ></el-switch>
            <div class="setting-description">
              <p>控制是否允许新用户注册账号（关闭后，只有管理员可以创建新账号）</p>
            </div>
          </div>
        </el-card>
        
        <el-card class="system-card">
          <div slot="header">
            <span>用户管理</span>
          </div>
          
          <div class="user-management">
            <el-button type="primary" @click="showCreateUserDialog">新增用户</el-button>
            <el-button type="primary" @click="showImportUsersDialog">批量导入学生</el-button>
          </div>
        </el-card>
        
        <el-card class="backup-list-card">
          <div slot="header">
            <span>备份列表</span>
            <el-button 
              style="float: right; padding: 3px 0" 
              type="text" 
              @click="fetchBackupList"
              :loading="listLoading"
            >刷新</el-button>
          </div>
          
          <div v-if="listLoading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>
          
          <div v-else-if="backups.length === 0" class="empty-backup">
            <p>暂无备份记录</p>
          </div>
          
          <el-table v-else :data="backups" style="width: 100%">
            <el-table-column label="备份时间" prop="time"></el-table-column>
            <el-table-column label="备份路径" prop="path"></el-table-column>
            <el-table-column label="状态">
              <template slot-scope="scope">
                <div>
                  <el-tag type="success" v-if="scope.row.has_db">数据库</el-tag>
                  <el-tag type="info" v-else>无数据库</el-tag>
                  
                  <el-tag type="success" v-if="scope.row.has_uploads" style="margin-left: 5px">上传文件</el-tag>
                  <el-tag type="info" v-else style="margin-left: 5px">无上传文件</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template slot-scope="scope">
                <el-button 
                  size="mini" 
                  type="primary" 
                  @click="showRestoreDialog(scope.row)"
                  :disabled="!scope.row.has_db || !scope.row.has_uploads"
                >恢复系统</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 重置密码对话框 -->
    <el-dialog
      title="重置用户密码"
      :visible.sync="resetPasswordDialogVisible"
      width="400px"
    >
      <p>您正在重置用户 <span class="highlight-text">{{ selectedUser.real_name }}</span> 的密码</p>
      
      <el-form ref="resetPasswordForm" :model="resetPasswordForm" :rules="passwordRules">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="resetPasswordForm.newPassword" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="resetPasswordForm.confirmPassword" type="password" show-password></el-input>
        </el-form-item>
      </el-form>
      
      <span slot="footer" class="dialog-footer">
        <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword" :loading="submitting">确定</el-button>
      </span>
    </el-dialog>
    
    <!-- 创建用户对话框 -->
    <el-dialog
      title="创建新用户"
      :visible.sync="createUserDialogVisible"
      width="500px"
    >
      <el-form ref="createUserForm" :model="createUserForm" :rules="createUserFormRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createUserForm.username" placeholder="请输入用户名（6-16个字符，首字符必须是字母）"></el-input>
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="createUserForm.password" type="password" show-password placeholder="请输入密码（至少7位且包含字母和数字）"></el-input>
        </el-form-item>
        
        <el-form-item label="用户身份" prop="is_teacher">
          <el-radio-group v-model="createUserForm.is_teacher">
            <el-radio :label="false">学生</el-radio>
            <el-radio :label="true">教师</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="年级" prop="grade" v-if="!createUserForm.is_teacher">
          <el-select v-model="createUserForm.grade" placeholder="请选择年级">
            <el-option v-for="i in 5" :key="i" :label="`${i}年级`" :value="String(i)"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="班级" prop="class_name" v-if="!createUserForm.is_teacher">
          <el-select v-model="createUserForm.class_name" placeholder="请选择班级">
            <el-option v-for="i in 6" :key="i" :label="`${i}班`" :value="String(i)"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="姓名昵称" prop="real_name">
          <el-input v-model="createUserForm.real_name" placeholder="请输入姓名昵称（2-5个汉字，可选）"></el-input>
        </el-form-item>
        
        <el-form-item label="账号状态">
          <el-switch
            v-model="createUserForm.is_active"
            active-color="#13ce66"
            inactive-color="#ff4949"
            active-text="启用"
            inactive-text="禁用"
          ></el-switch>
        </el-form-item>
        
        <el-form-item label="发布权限">
          <el-switch
            v-model="createUserForm.can_post"
            active-color="#13ce66"
            inactive-color="#ff4949"
            active-text="允许"
            inactive-text="禁止"
          ></el-switch>
        </el-form-item>
      </el-form>
      
      <span slot="footer" class="dialog-footer">
        <el-button @click="createUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreateUser" :loading="createUserLoading">创建</el-button>
      </span>
    </el-dialog>
    
    <!-- 批量导入学生对话框 -->
    <el-dialog
      title="批量导入学生"
      :visible.sync="importUsersDialogVisible"
      width="700px"
    >
      <div class="import-instructions">
        <p>请上传包含学生信息的Excel文件，文件中应包含以下列：</p>
        <ul>
          <li><strong>username</strong>: 用户名（6-16个字符，首字符必须是字母）</li>
          <li><strong>password</strong>: 密码（至少7位，且包含字母和数字）</li>
          <li><strong>grade</strong>: 年级（1-5）</li>
          <li><strong>class_name</strong>: 班级（1-6）</li>
        </ul>
      </div>
      
      <el-upload
        class="excel-uploader"
        action="#"
        :http-request="handleExcelUpload"
        :on-change="(file) => {}"
        :auto-upload="false"
        :show-file-list="true"
        accept=".xlsx,.xls"
        :limit="1"
        ref="upload"
      >
        <el-button slot="trigger" size="small" type="primary">选择Excel文件</el-button>
        <el-button style="margin-left: 10px;" size="small" type="success" @click="$refs.upload.submit()">解析文件</el-button>
        <div slot="tip" class="el-upload__tip">只能上传xlsx/xls文件</div>
      </el-upload>
      
      <div v-if="importedStudents.length > 0" class="preview-table">
        <h3>将要导入的学生账号（共{{ importedStudents.length }}个）：</h3>
        <el-table :data="importedStudents" style="width: 100%" height="250">
          <el-table-column prop="username" label="用户名" width="150"></el-table-column>
          <el-table-column prop="grade" label="年级" width="80"></el-table-column>
          <el-table-column prop="class_name" label="班级" width="80"></el-table-column>
          <el-table-column prop="password" label="密码" width="180">
            <template slot-scope="scope">
              <el-tag type="info">{{ scope.row.password || '已设置密码' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div v-if="invalidImportRows.length > 0" class="invalid-rows">
        <h3>无效数据（共{{ invalidImportRows.length }}条）：</h3>
        <el-collapse>
          <el-collapse-item title="点击查看详情">
            <el-table :data="invalidImportRows" style="width: 100%" height="200">
              <el-table-column prop="index" label="行号" width="80"></el-table-column>
              <el-table-column prop="reason" label="错误原因"></el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <span slot="footer" class="dialog-footer">
        <el-button @click="importUsersDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="submitImportStudents" 
          :loading="importUsersLoading" 
          :disabled="importedStudents.length === 0"
        >导入</el-button>
      </span>
    </el-dialog>
    
    <!-- 修改自己密码对话框 -->
    <el-dialog
      title="修改管理员密码"
      :visible.sync="changePasswordDialogVisible"
      width="400px"
    >
      <el-form ref="adminPasswordForm" :model="adminPasswordForm" :rules="adminPasswordRules">
        <el-form-item label="当前密码" prop="oldPassword">
          <el-input v-model="adminPasswordForm.oldPassword" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="adminPasswordForm.newPassword" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="adminPasswordForm.confirmPassword" type="password" show-password></el-input>
        </el-form-item>
      </el-form>
      
      <span slot="footer" class="dialog-footer">
        <el-button @click="changePasswordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitChangeAdminPassword" :loading="submitting">确定</el-button>
      </span>
    </el-dialog>

    <div class="actions">
      <el-button @click="$router.push('/moments')">返回首页</el-button>
    </div>

    <!-- 删除用户确认对话框 -->
    <el-dialog
      title="删除用户确认"
      :visible.sync="deleteUserDialogVisible"
      width="400px"
    >
      <div class="delete-user-confirm">
        <p>您确定要删除用户 <span class="highlight-text">{{ selectedUser.real_name }}</span> 吗？</p>
        <p class="warning-text">警告：此操作将删除该用户的所有数据，包括动态、评论和点赞，且不可恢复！</p>
      </div>
      
      <span slot="footer" class="dialog-footer">
        <el-button @click="deleteUserDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDeleteUser" :loading="submitting">确认删除</el-button>
      </span>
    </el-dialog>

    <!-- 清空系统确认对话框 -->
    <el-dialog
      title="清空系统确认"
      :visible.sync="clearSystemDialogVisible"
      width="450px"
    >
      <div class="clear-system-confirm">
        <p><strong class="warning-text">警告：</strong>此操作将清空系统中的所有数据，包括：</p>
        <ul>
          <li>所有用户（除超级管理员）</li>
          <li>所有动态和评论</li>
          <li>所有上传的图片文件</li>
        </ul>
        <p>系统会在清空前自动备份当前数据，但仍请谨慎操作。</p>
        <p>超级管理员账号 <strong>yzxmst</strong> 将被保留，密码将重置为 <strong>yzxm5t1234s</strong></p>
        <p class="confirm-text">请输入 "CONFIRM" 以确认操作:</p>
        <el-input v-model="clearConfirmText" placeholder="请输入 CONFIRM"></el-input>
      </div>
      
      <span slot="footer" class="dialog-footer">
        <el-button @click="clearSystemDialogVisible = false">取消</el-button>
        <el-button 
          type="danger" 
          @click="clearSystem" 
          :loading="clearLoading"
          :disabled="clearConfirmText !== 'CONFIRM'"
        >确认清空</el-button>
      </span>
    </el-dialog>
    
    <!-- 恢复系统确认对话框 -->
    <el-dialog
      title="恢复系统确认"
      :visible.sync="restoreSystemDialogVisible"
      width="450px"
    >
      <div class="restore-system-confirm">
        <p>您正在恢复系统到备份点：<strong>{{ selectedBackup.time }}</strong></p>
        <p><strong class="warning-text">警告：</strong>此操作将覆盖当前系统中的所有数据，包括：</p>
        <ul>
          <li>所有用户账号信息</li>
          <li>所有动态和评论</li>
          <li>所有上传的图片文件</li>
        </ul>
        <p>系统会在恢复前自动备份当前数据，但仍请谨慎操作。</p>
        <p class="confirm-text">请输入 "CONFIRM" 以确认操作:</p>
        <el-input v-model="restoreConfirmText" placeholder="请输入 CONFIRM"></el-input>
      </div>
      
      <span slot="footer" class="dialog-footer">
        <el-button @click="restoreSystemDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="restoreSystem" 
          :loading="restoreLoading"
          :disabled="restoreConfirmText !== 'CONFIRM'"
        >确认恢复</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import api from '@/api'
import { format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import * as XLSX from 'xlsx'

export default {
  name: 'Admin',
  data() {
    // 密码验证规则
    const validatePassword = (rule, value, callback) => {
      if (value.length < 7) {
        callback(new Error('密码长度不能少于7位'))
      } else if (!/[a-zA-Z]/.test(value) || !/[0-9]/.test(value)) {
        callback(new Error('密码必须包含字母和数字'))
      } else {
        callback()
      }
    }
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.resetPasswordForm.newPassword) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }
    
    const validateAdminConfirmPassword = (rule, value, callback) => {
      if (value !== this.adminPasswordForm.newPassword) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }
    
    return {
      admin: null,
      users: [],
      total: 0,
      currentPage: 1,
      pageSize: 10,
      loading: true,
      submitting: false,
      selectedUser: {},
      resetPasswordDialogVisible: false,
      resetPasswordForm: {
        newPassword: '',
        confirmPassword: ''
      },
      changePasswordDialogVisible: false,
      adminPasswordForm: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      passwordRules: {
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { validator: validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      },
      adminPasswordRules: {
        oldPassword: [
          { required: true, message: '请输入当前密码', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { validator: validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateAdminConfirmPassword, trigger: 'blur' }
        ]
      },
      deleteUserDialogVisible: false,
      activeTab: 'users',
      posts: [],
      postsLoading: true,
      backups: [],
      backupLoading: false,
      clearLoading: false,
      clearSystemDialogVisible: false,
      clearConfirmText: '',
      restoreSystemDialogVisible: false,
      restoreLoading: false,
      restoreConfirmText: '',
      selectedBackup: {},
      listLoading: false,
      registerEnabled: true,
      settingLoading: false,
      createUserDialogVisible: false,
      createUserForm: {
        username: '',
        password: '',
        is_teacher: false,
        grade: '',
        class_name: '',
        real_name: '',
        is_active: true,
        can_post: true
      },
      createUserFormRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 6, max: 16, message: '用户名长度应在6-16个字符之间', trigger: 'blur' },
          { pattern: /^[a-zA-Z][a-zA-Z0-9]*$/, message: '用户名必须以字母开头且只包含字母和数字', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 7, message: '密码长度不能少于7位', trigger: 'blur' },
          { pattern: /^(?=.*[a-zA-Z])(?=.*\d).*$/, message: '密码必须包含至少一个字母和一个数字', trigger: 'blur' }
        ],
        is_teacher: [
          { required: true, message: '请选择用户身份', trigger: 'change' }
        ],
        grade: [
          { required: true, message: '请选择年级', trigger: 'change' },
          { pattern: /^\d+$/, message: '请输入有效的年级', trigger: 'change' },
          { validator: (rule, value) => {
            if (value && parseInt(value) < 1 || parseInt(value) > 5) {
              return Promise.reject('年级必须在1-5之间')
            }
            return Promise.resolve()
          }, trigger: 'change' }
        ],
        class_name: [
          { required: true, message: '请选择班级', trigger: 'change' },
          { pattern: /^\d+$/, message: '请输入有效的班级', trigger: 'change' },
          { validator: (rule, value) => {
            if (value && parseInt(value) < 1 || parseInt(value) > 6) {
              return Promise.reject('班级必须在1-6之间')
            }
            return Promise.resolve()
          }, trigger: 'change' }
        ],
        real_name: [
          { max: 5, message: '姓名昵称长度不能超过5个汉字', trigger: 'blur' }
        ]
      },
      createUserLoading: false,
      importedStudents: [],
      invalidImportRows: [],
      importUsersDialogVisible: false,
      importUsersLoading: false
    }
  },
  created() {
    this.checkAdmin()
  },
  methods: {
    async checkAdmin() {
      const userInfo = localStorage.getItem('user')
      if (!userInfo) {
        this.$router.push('/login')
        return
      }
      
      try {
        this.admin = JSON.parse(userInfo)
        if (!this.admin.is_admin) {
          this.$message.error('您没有管理员权限')
          this.$router.push('/')
          return
        }
        
        await this.fetchUsers()
        await this.fetchPosts()
        if (this.admin.is_admin) {
          await this.fetchBackupList()
          await this.getSystemConfig()
        }
      } catch (error) {
        this.$message.error('获取用户信息失败')
        this.$router.push('/login')
      }
    },
    formatTime(timeString) {
      try {
        const date = new Date(timeString)
        return format(date, 'yyyy-MM-dd HH:mm', { locale: zhCN })
      } catch (e) {
        return timeString
      }
    },
    getRowClassName({ row }) {
      if (!row.is_active) {
        return 'disabled-row'
      }
      if (row.is_teacher) {
        return 'teacher-row'
      }
      return ''
    },
    async fetchUsers() {
      this.loading = true
      
      try {
        const response = await api.get('/users', {
          params: { user_id: this.admin.id }
        })
        
        this.users = response.data
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('获取用户列表失败')
        }
        console.error('获取用户列表失败:', error)
      } finally {
        this.loading = false
      }
    },
    async toggleUserActive(user) {
      try {
        const response = await api.put(`/users/${user.id}/toggle-active`, {
          user_id: this.admin.id
        })
        
        this.$message.success(response.data.message)
        
        // 更新用户状态
        const index = this.users.findIndex(u => u.id === user.id)
        if (index !== -1) {
          this.users[index].is_active = response.data.is_active
        }
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('操作失败')
        }
        console.error('禁用/启用用户失败:', error)
      }
    },
    showResetPasswordDialog(user) {
      this.selectedUser = user
      this.resetPasswordForm.newPassword = ''
      this.resetPasswordForm.confirmPassword = ''
      this.resetPasswordDialogVisible = true
      
      // 重置表单验证状态
      if (this.$refs.resetPasswordForm) {
        this.$refs.resetPasswordForm.resetFields()
      }
    },
    showChangePasswordDialog() {
      this.adminPasswordForm.oldPassword = ''
      this.adminPasswordForm.newPassword = ''
      this.adminPasswordForm.confirmPassword = ''
      this.changePasswordDialogVisible = true
      
      // 重置表单验证状态
      if (this.$refs.adminPasswordForm) {
        this.$refs.adminPasswordForm.resetFields()
      }
    },
    submitResetPassword() {
      this.$refs.resetPasswordForm.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        this.submitting = true
        
        try {
          const response = await api.put(`/users/${this.selectedUser.id}/reset-password`, {
            user_id: this.admin.id,
            new_password: this.resetPasswordForm.newPassword
          })
          
          this.$message.success(response.data.message)
          this.resetPasswordDialogVisible = false
        } catch (error) {
          if (error.response && error.response.data && error.response.data.error) {
            this.$message.error(error.response.data.error)
          } else {
            this.$message.error('重置密码失败')
          }
          console.error('重置密码失败:', error)
        } finally {
          this.submitting = false
        }
      })
    },
    submitChangeAdminPassword() {
      this.$refs.adminPasswordForm.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        this.submitting = true
        
        try {
          const response = await api.put('/change-password', {
            user_id: this.admin.id,
            old_password: this.adminPasswordForm.oldPassword,
            new_password: this.adminPasswordForm.newPassword
          })
          
          this.$message.success('密码修改成功')
          this.changePasswordDialogVisible = false
        } catch (error) {
          if (error.response && error.response.data && error.response.data.error) {
            this.$message.error(error.response.data.error)
          } else {
            this.$message.error('密码修改失败')
          }
          console.error('密码修改失败:', error)
        } finally {
          this.submitting = false
        }
      })
    },
    logout() {
      localStorage.removeItem('user')
      this.$message.success('已退出登录')
      this.$router.push('/login')
    },
    showDeleteUserDialog(user) {
      this.selectedUser = user
      this.deleteUserDialogVisible = true
    },
    async confirmDeleteUser() {
      this.submitting = true
      
      try {
        const response = await api.delete(`/users/${this.selectedUser.id}`, {
          params: { user_id: this.admin.id }
        })
        
        this.$message.success(response.data.message)
        this.deleteUserDialogVisible = false
        this.fetchUsers()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('删除用户失败')
        }
        console.error('删除用户失败:', error)
      } finally {
        this.submitting = false
      }
    },
    async fetchPosts() {
      this.postsLoading = true
      
      try {
        const response = await api.get('/posts', {
          params: { user_id: this.admin.id }
        })
        
        this.posts = response.data
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('获取动态列表失败')
        }
        console.error('获取动态列表失败:', error)
      } finally {
        this.postsLoading = false
      }
    },
    async deletePost(postId) {
      try {
        this.$confirm('确定要删除这条动态吗？该操作将删除该动态的所有点赞和评论，且不可恢复！', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(async () => {
          const response = await api.delete(`/posts/${postId}`, {
            params: { user_id: this.admin.id }
          })
          
          this.$message.success(response.data.message)
          this.fetchPosts() // 刷新动态列表
        }).catch(() => {
          this.$message.info('已取消删除')
        })
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('删除动态失败')
        }
        console.error('删除动态失败:', error)
      }
    },
    async deleteComment(commentId) {
      try {
        this.$confirm('确定要删除这条评论吗？该操作不可恢复！', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(async () => {
          const response = await api.delete(`/comments/${commentId}`, {
            params: { user_id: this.admin.id }
          })
          
          this.$message.success(response.data.message)
          this.fetchPosts() // 刷新动态列表以更新评论
        }).catch(() => {
          this.$message.info('已取消删除')
        })
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('删除评论失败')
        }
        console.error('删除评论失败:', error)
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
    async fetchBackupList() {
      this.listLoading = true
      
      try {
        const response = await api.get('/system/backups', {
          params: { user_id: this.admin.id }
        })
        
        this.backups = response.data.backups || []
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('获取备份列表失败')
        }
        console.error('获取备份列表失败:', error)
      } finally {
        this.listLoading = false
      }
    },
    async backupSystem() {
      this.backupLoading = true
      
      try {
        const response = await api.post('/system/backup', {
          user_id: this.admin.id
        })
        
        this.$message.success(response.data.message)
        this.fetchBackupList()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('备份系统失败')
        }
        console.error('备份系统失败:', error)
      } finally {
        this.backupLoading = false
      }
    },
    showClearSystemDialog() {
      this.clearSystemDialogVisible = true
    },
    async clearSystem() {
      this.clearLoading = true
      
      try {
        const response = await api.post('/system/clear', {
          user_id: this.admin.id
        })
        
        this.$message.success(response.data.message)
        this.clearSystemDialogVisible = false
        this.fetchBackupList()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('清空系统失败')
        }
        console.error('清空系统失败:', error)
      } finally {
        this.clearLoading = false
      }
    },
    showRestoreDialog(backup) {
      this.selectedBackup = backup
      this.restoreSystemDialogVisible = true
    },
    async restoreSystem() {
      this.restoreLoading = true
      
      try {
        const response = await api.post('/system/restore', {
          user_id: this.admin.id,
          backup_path: this.selectedBackup.path
        })
        
        this.$message.success(response.data.message)
        this.restoreSystemDialogVisible = false
        this.fetchBackupList()
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('恢复系统失败')
        }
        console.error('恢复系统失败:', error)
      } finally {
        this.restoreLoading = false
      }
    },
    async updateRegisterSetting() {
      this.settingLoading = true
      
      try {
        const response = await api.post('/system/config', {
          user_id: this.admin.id,
          key: 'register_enabled',
          value: this.registerEnabled ? 'true' : 'false',
          description: '是否开启用户注册功能'
        })
        
        this.$message.success(response.data.message)
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error)
        } else {
          this.$message.error('更新注册设置失败')
        }
        console.error('更新注册设置失败:', error)
        // 如果出错，恢复原值
        this.registerEnabled = !this.registerEnabled
      } finally {
        this.settingLoading = false
      }
    },
    async getSystemConfig() {
      try {
        const response = await api.get('/system/config', {
          params: { user_id: this.admin.id }
        })
        
        // 设置注册开关状态
        if (response.data && response.data.register_enabled) {
          this.registerEnabled = response.data.register_enabled.toLowerCase() === 'true'
        }
      } catch (error) {
        console.error('获取系统配置失败:', error)
      }
    },
    showCreateUserDialog() {
      this.createUserDialogVisible = true
    },
    submitCreateUser() {
      this.$refs.createUserForm.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        this.createUserLoading = true
        
        try {
          const response = await api.post('/users', {
            user_id: this.admin.id,
            username: this.createUserForm.username,
            password: this.createUserForm.password,
            is_teacher: this.createUserForm.is_teacher,
            grade: this.createUserForm.grade,
            class_name: this.createUserForm.class_name,
            real_name: this.createUserForm.real_name,
            is_active: this.createUserForm.is_active,
            can_post: this.createUserForm.can_post
          })
          
          this.$message.success(response.data.message)
          this.createUserDialogVisible = false
          this.fetchUsers()
        } catch (error) {
          if (error.response && error.response.data && error.response.data.error) {
            this.$message.error(error.response.data.error)
          } else {
            this.$message.error('创建用户失败')
          }
          console.error('创建用户失败:', error)
        } finally {
          this.createUserLoading = false
        }
      })
    },
    showImportUsersDialog() {
      this.importUsersDialogVisible = true
    },
    handleExcelUpload(event) {
      // 处理上传的Excel文件
      const file = event.file;
      this.importUsersLoading = true;

      // 使用FileReader读取文件内容
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          // 解析Excel文件
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          
          // 获取第一个工作表
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];
          
          // 将工作表转换为JSON
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          
          // 处理数据
          this.processImportData(jsonData);
        } catch (error) {
          console.error('Excel文件解析失败:', error);
          this.$message.error('Excel文件解析失败: ' + error.message);
        } finally {
          this.importUsersLoading = false;
        }
      };

      reader.onerror = (error) => {
        console.error('文件读取失败:', error);
        this.$message.error('文件读取失败');
        this.importUsersLoading = false;
      };

      // 确保file.raw是有效的Blob对象
      if (file && file.raw instanceof Blob) {
        reader.readAsArrayBuffer(file.raw);
      } else if (file instanceof Blob) {
        reader.readAsArrayBuffer(file);
      } else {
        console.error('无效的文件对象:', file);
        this.$message.error('无效的文件对象，请重新选择文件');
        this.importUsersLoading = false;
      }
    },

    // 处理导入的数据
    processImportData(data) {
      const validStudents = [];
      const invalidRows = [];

      // 验证和格式化导入的数据
      data.forEach((row, index) => {
        // 检查必填字段
        if (!row.username || !row.grade || !row.class_name) {
          invalidRows.push({
            index: index + 2, // Excel行号从1开始，第一行通常是标题
            reason: '缺少必填字段（用户名、年级或班级）',
            data: row
          });
          return;
        }

        // 验证用户名
        if (typeof row.username !== 'string' || 
            row.username.length < 6 || 
            row.username.length > 16 || 
            !/^[a-zA-Z]/.test(row.username)) {
          invalidRows.push({
            index: index + 2,
            reason: '用户名无效（长度6-16个字符且以字母开头）',
            data: row
          });
          return;
        }

        // 验证密码（如果提供）
        if (row.password && (
            typeof row.password !== 'string' || 
            row.password.length < 7 || 
            !/[a-zA-Z]/.test(row.password) || 
            !/[0-9]/.test(row.password))) {
          invalidRows.push({
            index: index + 2,
            reason: '密码无效（长度至少7位且包含字母和数字）',
            data: row
          });
          return;
        }

        // 验证年级和班级
        const grade = parseInt(row.grade);
        const class_name = parseInt(row.class_name);
        
        if (isNaN(grade) || grade < 1 || grade > 5) {
          invalidRows.push({
            index: index + 2,
            reason: '年级无效（必须是1-5之间的数字）',
            data: row
          });
          return;
        }

        if (isNaN(class_name) || class_name < 1 || class_name > 6) {
          invalidRows.push({
            index: index + 2,
            reason: '班级无效（必须是1-6之间的数字）',
            data: row
          });
          return;
        }

        // 添加到有效学生列表
        validStudents.push({
          username: row.username,
          password: row.password || '', // 如果密码为空，传递空字符串
          grade: grade,
          class_name: class_name,
          real_name: row.real_name || row.username // 如果real_name为空，使用username作为默认值
        });
      });

      this.importedStudents = validStudents;
      this.invalidImportRows = invalidRows;

      if (validStudents.length === 0) {
        this.$message.warning('没有有效的学生数据可以导入');
      } else {
        this.$message.success(`成功解析 ${validStudents.length} 条有效数据`);
      }

      if (invalidRows.length > 0) {
        this.$message.warning(`有 ${invalidRows.length} 条数据无效，请查看详情`);
      }
    },

    // 提交导入学生
    async submitImportStudents() {
      if (this.importedStudents.length === 0) {
        this.$message.warning('没有有效的学生数据可导入');
        return;
      }

      this.importUsersLoading = true;
      try {
        // 调用批量导入API
        const response = await api.post('/admin/import-students', {
          admin_id: this.admin.id,
          students: this.importedStudents
        });
        
        // 处理响应
        this.$message.success(`成功导入 ${response.data.created_users.length} 个学生账号`);
        
        if (response.data.errors && response.data.errors.length > 0) {
          console.warn('部分学生导入失败:', response.data.errors);
          this.$message.warning(`有 ${response.data.errors.length} 个学生账号导入失败`);
        }
        
        // 关闭对话框并刷新用户列表
        this.importUsersDialogVisible = false;
        this.fetchUsers();
      } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
          this.$message.error(error.response.data.error);
        } else {
          this.$message.error('批量导入失败，请稍后重试');
        }
        console.error('批量导入学生失败:', error);
      } finally {
        this.importUsersLoading = false;
      }
    },
  }
}
</script>

<style scoped>
.admin-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.admin-name {
  color: #409EFF;
  font-weight: bold;
}

.loading-container {
  margin: 20px 0;
}

.teacher-name {
  color: #409EFF;
  font-weight: bold;
}

.teacher-row {
  background-color: #f0f9ff;
}

.disabled-row {
  background-color: #f9f0f0;
}

.highlight-text {
  color: #409EFF;
  font-weight: bold;
}

.admin-self-change-btn {
  margin-top: 20px;
}

.delete-user-confirm {
  text-align: left;
  margin-bottom: 20px;
}

.warning-text {
  color: #ff0000;
  font-weight: bold;
  margin-top: 10px;
}

/* 动态管理样式 */
.post-card {
  background-color: #fff;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 5px;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.post-user-info h3 {
  margin: 0 0 5px 0;
}

.post-time {
  color: #888;
  font-size: 14px;
}

.post-content {
  margin-bottom: 15px;
}

.post-images {
  margin-top: 10px;
}

.image-grid-1 {
  display: flex;
  justify-content: flex-start;
}

.image-grid-1 .image-item {
  width: 200px;
  height: 200px;
}

.image-grid-2, .image-grid-3, .image-grid-4 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 5px;
}

.image-grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.image-grid-4 {
  grid-template-columns: repeat(2, 1fr);
}

.image-grid-6 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
}

.image-grid-9 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
}

.image-item {
  overflow: hidden;
  border-radius: 3px;
  aspect-ratio: 1;
}

.post-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.post-stats {
  display: flex;
  color: #888;
  font-size: 14px;
}

.post-stats span {
  margin-right: 15px;
}

.post-comments {
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 10px;
}

.post-comments h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #333;
  font-size: 15px;
}

.comment-item {
  margin-bottom: 10px;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.comment-content {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.comment-text {
  word-break: break-all;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
}

.replies-list {
  margin-top: 10px;
  margin-left: 20px;
}

.reply-item {
  margin-bottom: 8px;
  padding: 8px;
  background-color: #f2f2f2;
  border-radius: 4px;
}

.reply-content {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 5px;
}

.reply-text {
  margin: 0 3px;
  word-break: break-all;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
}

.actions {
  margin-top: 20px;
  text-align: center;
}

/* 系统管理样式 */
.system-card {
  margin-bottom: 20px;
}

.system-actions {
  margin-bottom: 10px;
}

.system-description {
  color: #888;
  font-size: 14px;
}

.backup-list-card {
  margin-bottom: 20px;
}

.empty-backup {
  text-align: center;
  padding: 20px;
  color: #888;
}

.clear-system-confirm {
  text-align: left;
  margin-bottom: 20px;
}

.confirm-text {
  margin-top: 10px;
}

.restore-system-confirm {
  text-align: left;
  margin-bottom: 20px;
}

.warning-text {
  color: #F56C6C;
}

.setting-item {
  margin-bottom: 10px;
}

.setting-label {
  margin-right: 10px;
}

.setting-description {
  color: #888;
  font-size: 14px;
}

.system-card .user-management {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.import-instructions {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

.import-instructions ul {
  margin-top: 10px;
  padding-left: 20px;
}

.import-instructions li {
  margin-bottom: 5px;
}

.excel-uploader {
  margin-bottom: 20px;
}

.preview-table {
  margin-top: 20px;
}

.invalid-rows {
  margin-top: 20px;
}

.invalid-rows h3 {
  color: #E6A23C;
}

/* 对话框内部样式 */
.el-dialog__body {
  padding: 20px;
}

.dialog-footer {
  margin-top: 10px;
}

/* 表单样式 */
.el-form-item__label {
  font-weight: 500;
}

.el-radio {
  margin-right: 20px;
}
</style> 