from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import time
import secrets
import json
import shutil
import base64
import uuid

# 创建一个函数生成北京时间（UTC+8）而不是UTC
def beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

# 创建应用实例
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 添加请求日志记录
@app.before_request
def log_request_info():
    print('请求开始 -----------------')
    print('请求路径:', request.path)
    print('请求方法:', request.method)
    print('请求头:', dict(request.headers))
    print('请求IP:', request.remote_addr)
    print('----------------------')

# 添加全局错误处理
@app.errorhandler(Exception)
def handle_exception(e):
    print('发生异常:', str(e))
    import traceback
    traceback.print_exc()
    return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500

# 配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'school.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 文件上传限制
app.config['TEACHER_REGISTER_CODE'] = 'teacher123'  # 教师注册码

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    real_name = db.Column(db.String(80), nullable=True)  # 修改为可空
    is_teacher = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)  # 超级管理员标识
    is_active = db.Column(db.Boolean, default=True)  # 用户是否启用
    is_first_login = db.Column(db.Boolean, default=False)  # 是否首次登录需要修改密码和昵称
    can_post = db.Column(db.Boolean, default=True)  # 是否允许发布动态
    grade = db.Column(db.Integer, nullable=True)  # 年级（1-5）
    class_name = db.Column(db.Integer, nullable=True)  # 班级（1-6）
    created_at = db.Column(db.DateTime, default=beijing_time)

# 动态模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.String(500), nullable=True)  # 存储图片文件名，用逗号分隔
    created_at = db.Column(db.DateTime, default=beijing_time)
    disable_comments = db.Column(db.Boolean, default=False)  # 是否禁止评论
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))

# 评论模型
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=beijing_time)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # 父评论ID
    replied_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 被回复用户ID
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('comments', lazy='dynamic'))
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic', cascade='all, delete-orphan'))
    parent = db.relationship('Comment', remote_side=[id], backref=db.backref('replies', lazy='dynamic'), uselist=False)
    replied_to_user = db.relationship('User', foreign_keys=[replied_to_user_id])

# 点赞模型
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=beijing_time)
    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic'))
    post = db.relationship('Post', backref=db.backref('likes', lazy='dynamic', cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),)

# 系统配置模型
class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=beijing_time, onupdate=beijing_time)
    
    @classmethod
    def get_config(cls, key, default=None):
        """获取配置值，如果不存在则返回默认值"""
        config = cls.query.filter_by(key=key).first()
        if config:
            return config.value
        return default
    
    @classmethod
    def set_config(cls, key, value, description=None):
        """设置配置值，如果不存在则创建"""
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = cls(key=key, value=value, description=description)
            db.session.add(config)
        db.session.commit()
        return config

# 检查文件类型是否允许
def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 添加图片访问路由
@app.route('/api/images/<filename>')
def get_image(filename):
    """直接提供图片文件，替代nginx的静态文件服务"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 添加额外的图片路由，直接处理/images/路径的请求
@app.route('/images/<filename>')
def get_image_direct(filename):
    """直接提供图片文件，兼容/images/路径"""
    print(f"通过/images/路径访问图片: {filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/uploads', methods=['POST'])
def upload_file():
    """处理文件上传请求"""
    # 在函数内定义允许的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff'}
    
    print("====== 开始处理文件上传请求 =======")
    
    # 打印请求的详细信息，用于调试
    print("请求表单:", request.form)
    print("请求文件列表键:", list(request.files.keys()))
    print("请求头:", dict(request.headers))
    print("请求方法:", request.method)
    print("请求URL:", request.url)
    print("请求IP:", request.remote_addr)
    
    # 检查请求是否为JSON格式（Base64上传）
    if request.is_json:
        try:
            json_data = request.get_json()
            user_id = json_data.get('user_id')
            if not user_id:
                return jsonify({"error": "缺少用户ID"}), 400
                
            image_data = json_data.get('image_data')
            if not image_data:
                return jsonify({"error": "缺少图片数据"}), 400
                
            filename = json_data.get('filename', 'image.png')
            
            # 解码Base64图片数据
            try:
                # 如果数据包含Base64前缀，去除它
                if ',' in image_data:
                    image_data = image_data.split(',', 1)[1]
                
                # 解码Base64数据
                image_binary = base64.b64decode(image_data)
            except Exception as e:
                print(f"Base64解码错误: {str(e)}")
                return jsonify({"error": "图片数据格式错误"}), 400
            
            # 生成一个唯一的文件名
            timestamp = int(time.time())
            unique_id = uuid.uuid4().hex[:8]
            name, ext = os.path.splitext(filename)
            if not ext or ext == '.':
                ext = '.png'  # 默认扩展名
            safe_filename = f"{name}_{timestamp}_{unique_id}{ext}"
            
            # 保存到上传目录
            backend_filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            
            try:
                with open(backend_filepath, 'wb') as f:
                    f.write(image_binary)
                
                backend_filesize = os.path.getsize(backend_filepath)
                print(f"后端文件大小: {backend_filesize} 字节")
                
                return jsonify({
                    "message": "成功上传1张图片",
                    "filenames": [safe_filename]
                })
            except Exception as e:
                print(f"保存文件错误: {str(e)}")
                return jsonify({"error": f"保存文件失败: {str(e)}"}), 500
        except Exception as e:
            print(f"JSON请求处理错误: {str(e)}")
            return jsonify({"error": f"处理请求失败: {str(e)}"}), 500
    
    # 常规表单文件上传处理
    # 获取用户ID，这是必需的
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"error": "缺少用户ID"}), 400
    
    # 获取上传的文件
    if 'file' in request.files:
        # 单文件上传
        print("使用单文件上传模式")
        files = [request.files['file']]
    elif 'files[]' in request.files:
        # 多文件上传
        files = request.files.getlist('files[]')
        print(f"使用多文件上传模式, 找到 {len(files)} 个文件")
    else:
        # 查找任何其他可能的文件字段
        file_keys = [key for key in request.files.keys()]
        if file_keys:
            first_key = file_keys[0]
            if isinstance(request.files[first_key], list):
                files = request.files.getlist(first_key)
            else:
                files = [request.files[first_key]]
            print(f"使用自动检测的文件字段: {first_key}, 找到 {len(files)} 个文件")
        else:
            return jsonify({"error": "未找到上传的文件"}), 400
    
    # 打印文件信息
    for i, file in enumerate(files):
        print(f"文件 {i+1} 信息: 名称={file.filename}, 内容类型={file.content_type}")
    
    print(f"用户ID: {user_id}, 文件数量: {len(files)}")
    
    # 保存文件并收集文件名
    saved_filenames = []
    for i, file in enumerate(files):
        if file and file.filename:
            print(f"处理文件 {i+1}: {file.filename}, 类型: {file.content_type}")
            
            # 确保文件类型安全
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            print(f"检查文件扩展名: {file_ext.lstrip('.')}, 允许的扩展名: {ALLOWED_EXTENSIONS}")
            if file_ext.lstrip('.') not in ALLOWED_EXTENSIONS:
                print(f"文件 {i+1}: 不允许的扩展名: {file_ext}")
                continue
            
            # 生成唯一文件名
            timestamp = int(time.time())
            unique_id = uuid.uuid4().hex[:8]
            name, ext = os.path.splitext(filename)
            safe_filename = f"{name}_{timestamp}_{unique_id}{ext}"
            
            # 打印路径信息
            print(f"当前工作目录: {os.getcwd()}")
            print(f"上传目录: {app.config['UPLOAD_FOLDER']}")
            
            # 保存到后端目录
            backend_filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            print(f"尝试保存文件到后端目录: {backend_filepath}")
            
            try:
                file.save(backend_filepath)
                backend_filesize = os.path.getsize(backend_filepath)
                print(f"文件 {i+1} 保存成功: {safe_filename}")
                print(f"后端文件大小: {backend_filesize} 字节")
                
                saved_filenames.append(safe_filename)
            except Exception as e:
                print(f"保存文件 {i+1} 失败: {str(e)}")
                continue
    
    if not saved_filenames:
        return jsonify({"error": "未能成功保存任何文件"}), 400
    
    # 返回成功消息和文件名列表
    print(f"成功上传 {len(saved_filenames)} 张图片")
    response_data = {
        "message": f"成功上传{len(saved_filenames)}张图片",
        "filenames": saved_filenames
    }
    print(f"响应数据: {response_data}")
    return jsonify(response_data)

# 访问上传的文件
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 新增路由，通过/images路径访问图片
@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 检查注册是否开启
    register_enabled = SystemConfig.get_config('register_enabled', 'true')
    if register_enabled.lower() != 'true':
        return jsonify({'error': '注册功能已关闭，请联系管理员老师'}), 403
    
    if not data or not data.get('username') or not data.get('password') or not data.get('real_name'):
        return jsonify({'error': '请提供用户名、密码和真实姓名'}), 400
        
    # 验证用户名：6-16个字符，首字符必须是字母
    username = data['username']
    if not (6 <= len(username) <= 16):
        return jsonify({'error': '用户名长度必须在6-16个字符之间'}), 400
    if not username[0].isalpha():
        return jsonify({'error': '用户名必须以字母开头'}), 400
        
    # 验证真实姓名：2-5个汉字
    real_name = data['real_name']
    if not (2 <= len(real_name) <= 5):
        return jsonify({'error': '真实姓名长度必须在2-5个汉字之间'}), 400
    if not all('\u4e00' <= char <= '\u9fff' for char in real_name):
        return jsonify({'error': '真实姓名必须是汉字'}), 400
        
    # 验证密码：最少7位的字母和数字组合
    password = data['password']
    if len(password) < 7:
        return jsonify({'error': '密码长度不能少于7位'}), 400
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return jsonify({'error': '密码必须包含字母和数字'}), 400
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'error': '用户名已存在'}), 400
        
    is_teacher = False
    grade = None
    class_name = None
    
    # 验证教师注册码
    if data.get('register_code'):
        if data['register_code'] == app.config['TEACHER_REGISTER_CODE']:
            is_teacher = True
        else:
            return jsonify({'error': '教师注册码错误'}), 400
    else:
        # 学生需要年级和班级
        if not data.get('grade') or not data.get('class_name'):
            return jsonify({'error': '学生需要提供年级和班级信息'}), 400
        
        grade = data['grade']
        class_name = data['class_name']
        
        # 验证年级和班级
        if not (1 <= grade <= 5 and 1 <= class_name <= 6):
            return jsonify({'error': '年级必须在1-5年级之间，班级必须在1-6班之间'}), 400
    
    # 创建新用户 - 普通用户永远不能是管理员
    new_user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        real_name=data['real_name'],
        is_teacher=is_teacher,
        is_admin=False,  # 普通注册用户不能是管理员
        grade=grade,
        class_name=class_name
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # 返回用户信息（不包含密码）
        user_data = {
            'id': new_user.id,
            'username': new_user.username,
            'real_name': new_user.real_name,
            'is_teacher': new_user.is_teacher,
            'is_admin': new_user.is_admin,
            'grade': new_user.grade,
            'class_name': new_user.class_name
        }
        
        return jsonify(user_data), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'注册失败: {str(e)}'}), 500

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    print(f"登录请求数据: {data}")
    
    if not data or not data.get('username') or not data.get('password'):
        print("错误: 缺少用户名或密码")
        return jsonify({'error': '请提供用户名和密码'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    print(f"查询到的用户: {user}")
    
    if not user:
        print("错误: 用户不存在")
        return jsonify({'error': '用户名或密码错误'}), 401
    
    if not check_password_hash(user.password_hash, data['password']):
        print("错误: 密码不匹配")
        return jsonify({'error': '用户名或密码错误'}), 401
        
    # 检查用户是否被禁用
    if not user.is_active:
        print("错误: 用户已被禁用")
        return jsonify({'error': '该账号已被禁用，请联系管理员'}), 403
    
    # 检查是否是首次登录的空账号
    if user.is_first_login:
        print("提示: 用户首次登录，需要修改密码和个人信息")
        
    # 返回用户信息（不包含密码）
    user_data = {
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'is_teacher': user.is_teacher,
        'is_admin': user.is_admin,
        'is_active': user.is_active,
        'is_first_login': user.is_first_login,
        'can_post': user.can_post,
        'grade': user.grade,
        'class_name': user.class_name
    }
    
    print(f"登录成功，返回用户数据: {user_data}")
    return jsonify(user_data), 200

# 发布动态
@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    
    if not data or not data.get('content') or not data.get('user_id'):
        return jsonify({'error': '内容和用户ID不能为空'}), 400
    
    user_id = data.get('user_id')
    content = data.get('content')
    images = data.get('images', '')
    disable_comments = data.get('disable_comments', False)
    
    # 获取用户信息
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 验证用户是否被禁用
    if not user.is_active:
        return jsonify({'error': '您的账号已被禁用，无法发布动态'}), 403
    
    # 检查用户是否有动态发布权限
    if not user.can_post:
        return jsonify({'error': '您的账号没有发布动态的权限'}), 403
    
    # 检查是否是首次登录需要修改信息
    if user.is_first_login:
        return jsonify({'error': '请先完善个人信息和修改密码后再发布动态'}), 403
    
    # 创建新动态
    new_post = Post(
        user_id=user_id,
        content=content,
        images=images,
        disable_comments=disable_comments
    )
    
    try:
        db.session.add(new_post)
        db.session.commit()
        return jsonify({'message': '动态发布成功', 'post_id': new_post.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'发布失败: {str(e)}'}), 500

# 获取动态列表
@app.route('/api/posts', methods=['GET'])
def get_posts():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    posts = Post.query.order_by(Post.created_at.desc()).all()
    result = []
    
    for post in posts:
        post_author = User.query.get(post.user_id)
        # 检查用户是否点赞过该动态
        is_liked = Like.query.filter_by(post_id=post.id, user_id=user_id).first() is not None
        
        # 获取评论，按时间顺序排序
        comments_list = []
        if not post.disable_comments:
            comments = Comment.query.filter_by(post_id=post.id, parent_id=None).order_by(Comment.created_at.asc()).all()
            
            for comment in comments:
                comment_user = User.query.get(comment.user_id)
                comment_data = {
                    'id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat(),
                    'user_id': comment.user_id,
                    'username': comment_user.username,
                    'real_name': comment_user.real_name,
                    'is_teacher': comment_user.is_teacher,
                    'replies': []
                }
                
                # 获取回复，按时间顺序排序
                replies = Comment.query.filter_by(parent_id=comment.id).order_by(Comment.created_at.asc()).all()
                for reply in replies:
                    reply_user = User.query.get(reply.user_id)
                    replied_to_user = User.query.get(reply.replied_to_user_id) if reply.replied_to_user_id else None
                    
                    reply_data = {
                        'id': reply.id,
                        'content': reply.content,
                        'created_at': reply.created_at.isoformat(),
                        'user_id': reply.user_id,
                        'username': reply_user.username,
                        'real_name': reply_user.real_name,
                        'is_teacher': reply_user.is_teacher,
                        'replied_to_user_id': reply.replied_to_user_id,
                        'replied_to_username': replied_to_user.username if replied_to_user else None,
                        'replied_to_real_name': replied_to_user.real_name if replied_to_user else None,
                        'replied_to_is_teacher': replied_to_user.is_teacher if replied_to_user else None
                    }
                    comment_data['replies'].append(reply_data)
                
                comments_list.append(comment_data)
        
        # 获取评论数（即使评论被禁用也显示数量）
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        post_data = {
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'user_id': post.user_id,
            'username': post_author.username,
            'real_name': post_author.real_name,
            'is_teacher': post_author.is_teacher,
            'images': post.images.split(',') if post.images else [],
            'like_count': Like.query.filter_by(post_id=post.id).count(),
            'comment_count': comment_count,
            'is_liked': is_liked,
            'comments': comments_list,
            'disable_comments': post.disable_comments
        }
        result.append(post_data)
    
    return jsonify(result), 200

# 点赞/取消点赞动态
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def toggle_like(post_id):
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': '用户ID不能为空'}), 400
    
    user_id = data.get('user_id')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '动态不存在'}), 404
    
    # 检查是否已经点赞
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_like:
        # 已经点赞，取消点赞
        db.session.delete(existing_like)
        db.session.commit()
        like_count = Like.query.filter_by(post_id=post_id).count()
        return jsonify({'message': '已取消点赞', 'is_liked': False, 'likes': like_count}), 200
    else:
        # 未点赞，添加点赞
        new_like = Like(user_id=user_id, post_id=post_id)
        try:
            db.session.add(new_like)
            db.session.commit()
            like_count = Like.query.filter_by(post_id=post_id).count()
            return jsonify({'message': '点赞成功', 'is_liked': True, 'likes': like_count}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'点赞失败: {str(e)}'}), 500

# 发表评论
@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()
    
    if not data or not data.get('content') or not data.get('user_id'):
        return jsonify({'error': '评论内容和用户ID不能为空'}), 400
    
    user_id = data.get('user_id')
    content = data.get('content')
    parent_id = data.get('parent_id')
    replied_to_user_id = data.get('replied_to_user_id')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '动态不存在'}), 404
    
    if post.disable_comments:
        return jsonify({'error': '该动态已禁止评论'}), 403
    
    # 检查用户是否有发布权限
    if not user.can_post:
        return jsonify({'error': '您的账号没有评论权限'}), 403
    
    # 检查是否是首次登录需要修改信息
    if user.is_first_login:
        return jsonify({'error': '请先完善个人信息和修改密码后再发表评论'}), 403
    
    # 创建新评论
    new_comment = Comment(
        content=content,
        user_id=user_id,
        post_id=post_id,
        parent_id=parent_id,
        replied_to_user_id=replied_to_user_id
    )
    
    try:
        db.session.add(new_comment)
        db.session.commit()
        
        # 返回评论信息
        comment_data = {
            'id': new_comment.id,
            'content': new_comment.content,
            'created_at': new_comment.created_at.isoformat(),
            'user_id': user_id,
            'username': user.username,
            'real_name': user.real_name,
            'is_teacher': user.is_teacher,
            'parent_id': parent_id
        }
        
        if replied_to_user_id:
            replied_to_user = User.query.get(replied_to_user_id)
            if replied_to_user:
                comment_data['replied_to_username'] = replied_to_user.username
                comment_data['replied_to_real_name'] = replied_to_user.real_name
                comment_data['replied_to_is_teacher'] = replied_to_user.is_teacher
        
        return jsonify({'message': '评论成功', 'comment': comment_data}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'评论失败: {str(e)}'}), 500

# 删除动态
@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '动态不存在'}), 404
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查权限：仅超级管理员或动态发布者可以删除
    if not user.is_admin and post.user_id != int(user_id):
        return jsonify({'error': '权限不足，您不能删除他人的动态'}), 403
    
    try:
        # 删除与动态相关的所有内容
        
        # 1. 删除与该动态相关的所有点赞
        likes = Like.query.filter_by(post_id=post.id).all()
        for like in likes:
            db.session.delete(like)
        
        # 2. 删除与该动态相关的所有评论和回复
        comments = Comment.query.filter_by(post_id=post.id).all()
        for comment in comments:
            # 删除该评论下的所有回复
            replies = Comment.query.filter_by(parent_id=comment.id).all()
            for reply in replies:
                db.session.delete(reply)
            db.session.delete(comment)
        
        # 3. 删除动态
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': '动态已成功删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除动态失败: {str(e)}'}), 500

# 删除评论
@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查权限：超级管理员、评论发布者或动态发布者可以删除评论
    is_comment_owner = comment.user_id == int(user_id)
    is_post_owner = Post.query.get(comment.post_id).user_id == int(user_id)
    
    if not user.is_admin and not is_comment_owner and not is_post_owner:
        return jsonify({'error': '权限不足，您不能删除此评论'}), 403
    
    try:
        # 删除该评论下的所有回复
        replies = Comment.query.filter_by(parent_id=comment.id).all()
        for reply in replies:
            db.session.delete(reply)
        
        # 删除评论
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'message': '评论已成功删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除评论失败: {str(e)}'}), 500

# 切换评论禁用状态
@app.route('/api/posts/<int:post_id>/toggle-comments', methods=['PUT'])
def toggle_disable_comments(post_id):
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': '用户ID不能为空'}), 400
    
    user_id = data.get('user_id')
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '动态不存在'}), 404
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查是否是动态作者且是教师
    if not user.is_teacher:
        return jsonify({'error': '只有教师才能修改评论设置'}), 403
        
    if int(post.user_id) != int(user_id):
        return jsonify({'error': '您只能修改自己发布的动态'}), 403
    
    try:
        # 切换评论禁用状态
        post.disable_comments = not post.disable_comments
        db.session.commit()
        
        status = '禁止' if post.disable_comments else '允许'
        return jsonify({'message': f'已{status}评论', 'disable_comments': post.disable_comments}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'修改评论设置失败: {str(e)}'}), 500

# 初始化数据库
@app.route('/api/init-db', methods=['POST'])
def init_db():
    try:
        db.drop_all()
        db.create_all()
        
        # 创建超级管理员账号
        admin = User(
            username='yzxmst',
            password_hash=generate_password_hash('yzxmst123456'),
            real_name='超级管理员',
            is_teacher=True,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'message': '数据库已重置，超级管理员账号已创建',
            'admin': {
                'username': 'yzxmst',
                'password': 'yzxmst123456'
            }
        }), 200
    except Exception as e:
        return jsonify({'error': f'重置数据库失败: {str(e)}'}), 500

# 获取用户列表（仅管理员可用）
@app.route('/api/users', methods=['GET'])
def get_users():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 401
    
    admin = User.query.get(user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以查看用户列表'}), 403
    
    # 排除超级管理员自己
    users = User.query.filter(User.id != admin.id).order_by(User.created_at.desc()).all()
    
    result = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'is_teacher': user.is_teacher,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'grade': user.grade,
            'class_name': user.class_name,
            'created_at': user.created_at.isoformat()
        }
        result.append(user_data)
    
    return jsonify(result), 200

# 禁用/启用用户（仅管理员可用）
@app.route('/api/users/<int:target_user_id>/toggle-active', methods=['PUT'])
def toggle_user_active(target_user_id):
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': '管理员ID不能为空'}), 400
    
    admin_id = data.get('user_id')
    
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以禁用/启用用户'}), 403
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'error': '目标用户不存在'}), 404
    
    # 防止管理员禁用自己
    if int(target_user_id) == int(admin_id):
        return jsonify({'error': '不能禁用/启用自己的账号'}), 400
    
    # 切换用户状态
    target_user.is_active = not target_user.is_active
    
    try:
        db.session.commit()
        status = '启用' if target_user.is_active else '禁用'
        return jsonify({
            'message': f'已成功{status}用户 {target_user.real_name}',
            'user_id': target_user.id,
            'is_active': target_user.is_active
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500

# 重置用户密码（仅管理员可用）
@app.route('/api/users/<int:target_user_id>/reset-password', methods=['PUT'])
def reset_user_password(target_user_id):
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('new_password'):
        return jsonify({'error': '管理员ID和新密码不能为空'}), 400
    
    admin_id = data.get('user_id')
    new_password = data.get('new_password')
    
    # 验证密码：最少7位的字母和数字组合
    if len(new_password) < 7:
        return jsonify({'error': '密码长度不能少于7位'}), 400
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
        return jsonify({'error': '密码必须包含字母和数字'}), 400
    
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以重置密码'}), 403
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'error': '目标用户不存在'}), 404
    
    # 超级管理员可以重置任何人的密码，包括自己
    
    # 重置密码
    target_user.password_hash = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        return jsonify({
            'message': f'已成功重置用户 {target_user.real_name} 的密码',
            'user_id': target_user.id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'重置密码失败: {str(e)}'}), 500

# 用户修改自己的密码
@app.route('/api/change-password', methods=['PUT'])
def change_password():
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': '用户ID、旧密码和新密码不能为空'}), 400
    
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    # 验证新密码：最少7位的字母和数字组合
    if len(new_password) < 7:
        return jsonify({'error': '新密码长度不能少于7位'}), 400
    if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
        return jsonify({'error': '新密码必须包含字母和数字'}), 400
    
    # 获取用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 验证旧密码
    if not check_password_hash(user.password_hash, old_password):
        return jsonify({'error': '旧密码不正确'}), 401
    
    # 更新密码
    user.password_hash = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        return jsonify({
            'message': '密码修改成功',
            'user_id': user.id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'密码修改失败: {str(e)}'}), 500

# 删除用户（仅超级管理员可用）
@app.route('/api/users/<int:target_user_id>', methods=['DELETE'])
def delete_user(target_user_id):
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '管理员ID不能为空'}), 400
    
    admin = User.query.get(user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以删除用户'}), 403
    
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({'error': '目标用户不存在'}), 404
    
    # 管理员不能删除自己
    if int(target_user_id) == int(user_id):
        return jsonify({'error': '不能删除自己的账号'}), 400
    
    try:
        # 删除用户相关的所有内容
        # 1. 删除该用户的点赞
        likes = Like.query.filter_by(user_id=target_user_id).all()
        for like in likes:
            db.session.delete(like)
        
        # 2. 删除该用户的评论和回复
        comments = Comment.query.filter_by(user_id=target_user_id).all()
        for comment in comments:
            # 删除该评论下的所有回复
            replies = Comment.query.filter_by(parent_id=comment.id).all()
            for reply in replies:
                db.session.delete(reply)
            db.session.delete(comment)
        
        # 3. 删除该用户的动态
        posts = Post.query.filter_by(user_id=target_user_id).all()
        for post in posts:
            # 删除与该动态相关的所有点赞
            post_likes = Like.query.filter_by(post_id=post.id).all()
            for like in post_likes:
                db.session.delete(like)
            
            # 删除与该动态相关的所有评论和回复
            post_comments = Comment.query.filter_by(post_id=post.id).all()
            for comment in post_comments:
                # 删除该评论下的所有回复
                replies = Comment.query.filter_by(parent_id=comment.id).all()
                for reply in replies:
                    db.session.delete(reply)
                db.session.delete(comment)
            
            # 删除动态
            db.session.delete(post)
        
        # 4. 最后删除用户
        db.session.delete(target_user)
        db.session.commit()
        
        return jsonify({'message': f'用户 {target_user.real_name} 已成功删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除用户失败: {str(e)}'}), 500

# 系统备份、清空和恢复功能 (仅供超级管理员使用)

# 获取系统配置（超级管理员可以获取所有配置，普通用户只能获取公开配置）
@app.route('/api/system/config', methods=['GET'])
def get_system_config():
    user_id = request.args.get('user_id')
    config_key = request.args.get('key')
    
    # 定义公开配置，不需要用户ID也可访问
    public_configs = ['register_enabled']
    
    # 如果请求了公开配置，直接返回
    if config_key and config_key in public_configs:
        value = SystemConfig.get_config(config_key)
        if value is None:
            return jsonify({'error': f'配置 {config_key} 不存在'}), 404
        return jsonify({config_key: value}), 200
    
    # 以下配置需要认证
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    else:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    # 如果指定了key，则只返回该key的配置
    if config_key:
        # 敏感配置只有管理员可以获取
        sensitive_configs = ['db_path', 'backup_path']
        if config_key in sensitive_configs and not user.is_admin:
            return jsonify({'error': '无权访问该配置'}), 403
        
        value = SystemConfig.get_config(config_key)
        if value is None:
            return jsonify({'error': f'配置 {config_key} 不存在'}), 404
        
        return jsonify({config_key: value}), 200
    
    # 获取所有配置
    if user.is_admin:
        # 管理员可以获取所有配置
        configs = SystemConfig.query.all()
        result = {config.key: config.value for config in configs}
    else:
        # 普通用户只能获取公开配置
        configs = SystemConfig.query.filter(SystemConfig.key.in_(public_configs)).all()
        result = {config.key: config.value for config in configs}
    
    return jsonify(result), 200

# 更新系统配置（仅限超级管理员）
@app.route('/api/system/config', methods=['POST', 'PUT'])
def update_system_config():
    data = request.get_json()
    
    if not data or not data.get('user_id') or 'key' not in data or 'value' not in data:
        return jsonify({'error': '参数不完整，需要用户ID、配置键和值'}), 400
    
    admin_id = data.get('user_id')
    key = data.get('key')
    value = data.get('value')
    description = data.get('description')
    
    # 验证是否为超级管理员
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以修改系统配置'}), 403
    
    try:
        # 设置配置
        config = SystemConfig.set_config(key, value, description)
        return jsonify({
            'message': f'系统配置已更新',
            'key': config.key,
            'value': config.value
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新系统配置失败: {str(e)}'}), 500

# 一键备份系统
@app.route('/api/system/backup', methods=['POST'])
def backup_system():
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': '管理员ID不能为空'}), 400
    
    admin_id = data.get('user_id')
    
    # 验证是否为超级管理员
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以执行此操作'}), 403
    
    try:
        # 创建备份目录，使用时间戳命名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'/var/log/campus_yzx/backup_{timestamp}'
        
        # 确保目录存在
        os.makedirs('/var/log/campus_yzx', exist_ok=True)
        os.makedirs(backup_dir, exist_ok=True)
        
        # 备份数据库
        db_path = os.path.join(basedir, 'instance', 'school.db')
        backup_db_path = os.path.join(backup_dir, 'school.db')
        shutil.copy2(db_path, backup_db_path)
        
        # 备份上传目录
        uploads_path = app.config['UPLOAD_FOLDER']
        backup_uploads_path = os.path.join(backup_dir, 'uploads')
        os.makedirs(backup_uploads_path, exist_ok=True)
        
        # 仅复制文件，不复制目录结构
        for filename in os.listdir(uploads_path):
            file_path = os.path.join(uploads_path, filename)
            if os.path.isfile(file_path):
                shutil.copy2(file_path, os.path.join(backup_uploads_path, filename))
        
        return jsonify({
            'message': f'系统备份成功，备份已保存到 {backup_dir}',
            'backup_path': backup_dir,
            'timestamp': timestamp
        }), 200
    except Exception as e:
        return jsonify({'error': f'备份失败: {str(e)}'}), 500

# 一键清空系统
@app.route('/api/system/clear', methods=['POST'])
def clear_system():
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': '管理员ID不能为空'}), 400
    
    admin_id = data.get('user_id')
    
    # 验证是否为超级管理员
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以执行此操作'}), 403
    
    try:
        # 先进行系统备份
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'/var/log/campus_yzx/backup_{timestamp}'
        
        # 确保目录存在
        os.makedirs('/var/log/campus_yzx', exist_ok=True)
        os.makedirs(backup_dir, exist_ok=True)
        
        # 备份数据库
        db_path = os.path.join(basedir, 'instance', 'school.db')
        backup_db_path = os.path.join(backup_dir, 'school.db')
        shutil.copy2(db_path, backup_db_path)
        
        # 备份上传目录
        uploads_path = app.config['UPLOAD_FOLDER']
        backup_uploads_path = os.path.join(backup_dir, 'uploads')
        os.makedirs(backup_uploads_path, exist_ok=True)
        
        # 仅复制文件，不复制目录结构
        for filename in os.listdir(uploads_path):
            file_path = os.path.join(uploads_path, filename)
            if os.path.isfile(file_path):
                shutil.copy2(file_path, os.path.join(backup_uploads_path, filename))
        
        # 清空系统数据，但保留超级管理员用户
        # 1. 删除所有点赞
        db.session.query(Like).delete()
        
        # 2. 删除所有评论
        db.session.query(Comment).delete()
        
        # 3. 删除所有动态
        db.session.query(Post).delete()
        
        # 4. 删除除了超级管理员以外的所有用户
        admin_users = User.query.filter_by(is_admin=True).all()
        admin_ids = [admin.id for admin in admin_users]
        db.session.query(User).filter(~User.id.in_(admin_ids)).delete(synchronize_session=False)
        
        # 5. 重置超级管理员密码 (yzxmst -> yzxm5t1234s)
        admin_user = User.query.filter_by(username='yzxmst').first()
        if admin_user:
            admin_user.password_hash = generate_password_hash('yzxm5t1234s')
        
        # 6. 清空上传目录，但保留目录结构
        for filename in os.listdir(uploads_path):
            file_path = os.path.join(uploads_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        db.session.commit()
        
        return jsonify({
            'message': '系统已成功清空，备份已保存',
            'backup_path': backup_dir,
            'timestamp': timestamp
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'清空系统失败: {str(e)}'}), 500

# 获取备份列表
@app.route('/api/system/backups', methods=['GET'])
def get_backups():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '管理员ID不能为空'}), 400
    
    # 验证是否为超级管理员
    admin = User.query.get(user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以查看备份'}), 403
    
    try:
        backup_dir = '/var/log/campus_yzx'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
            return jsonify({'backups': []}), 200
        
        backups = []
        for item in os.listdir(backup_dir):
            path = os.path.join(backup_dir, item)
            if os.path.isdir(path) and item.startswith('backup_'):
                # 提取时间戳
                timestamp = item.replace('backup_', '')
                # 格式化时间显示
                try:
                    dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = timestamp
                
                # 检查是否包含数据库和上传文件
                has_db = os.path.exists(os.path.join(path, 'school.db'))
                has_uploads = os.path.exists(os.path.join(path, 'uploads'))
                
                backups.append({
                    'id': timestamp,
                    'path': path,
                    'time': formatted_time,
                    'has_db': has_db,
                    'has_uploads': has_uploads
                })
        
        # 按时间戳排序，最新的在前面
        backups.sort(key=lambda x: x['id'], reverse=True)
        
        return jsonify({'backups': backups}), 200
    except Exception as e:
        return jsonify({'error': f'获取备份列表失败: {str(e)}'}), 500

# 恢复系统
@app.route('/api/system/restore', methods=['POST'])
def restore_system():
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('backup_path'):
        return jsonify({'error': '管理员ID和备份ID不能为空'}), 400
    
    admin_id = data.get('user_id')
    backup_path = data.get('backup_path')
    
    # 验证是否为超级管理员
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以执行此操作'}), 403
    
    try:
        # 当前时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 备份路径
        # backup_path直接从前端传入
        
        # 验证备份目录是否存在
        if not os.path.exists(backup_path):
            return jsonify({'error': '指定的备份不存在'}), 404
        
        # 检查备份是否完整
        backup_db_path = os.path.join(backup_path, 'school.db')
        backup_uploads_path = os.path.join(backup_path, 'uploads')
        
        if not os.path.exists(backup_db_path):
            return jsonify({'error': '备份数据库文件不存在'}), 400
        
        if not os.path.exists(backup_uploads_path):
            return jsonify({'error': '备份上传目录不存在'}), 400
        
        # 先备份当前系统状态
        current_backup_dir = f'/var/log/campus_yzx/backup_before_restore_{timestamp}'
        os.makedirs(current_backup_dir, exist_ok=True)
        
        # 备份当前数据库
        db_path = os.path.join(basedir, 'instance', 'school.db')
        current_backup_db_path = os.path.join(current_backup_dir, 'school.db')
        shutil.copy2(db_path, current_backup_db_path)
        
        # 备份当前上传目录
        uploads_path = app.config['UPLOAD_FOLDER']
        current_backup_uploads_path = os.path.join(current_backup_dir, 'uploads')
        os.makedirs(current_backup_uploads_path, exist_ok=True)
        
        for filename in os.listdir(uploads_path):
            file_path = os.path.join(uploads_path, filename)
            if os.path.isfile(file_path):
                shutil.copy2(file_path, os.path.join(current_backup_uploads_path, filename))
        
        # 恢复数据库
        shutil.copy2(backup_db_path, db_path)
        
        # 清空当前上传目录
        for filename in os.listdir(uploads_path):
            file_path = os.path.join(uploads_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # 恢复上传文件
        for filename in os.listdir(backup_uploads_path):
            file_path = os.path.join(backup_uploads_path, filename)
            if os.path.isfile(file_path):
                shutil.copy2(file_path, os.path.join(uploads_path, filename))
        
        return jsonify({
            'message': '系统已成功恢复',
            'backup_path': backup_path,
            'current_backup': current_backup_dir
        }), 200
    except Exception as e:
        return jsonify({'error': f'恢复系统失败: {str(e)}'}), 500

# 超级管理员添加用户
@app.route('/api/admin/users', methods=['POST'])
def admin_add_user():
    data = request.get_json()
    
    if not data or not data.get('admin_id'):
        return jsonify({'error': '管理员ID不能为空'}), 400
    
    admin_id = data.get('admin_id')
    
    # 验证操作者是否为超级管理员
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以添加用户'}), 403
    
    # 验证必需字段
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # 验证用户名：6-16个字符，首字符必须是字母
    username = data['username']
    if not (6 <= len(username) <= 16):
        return jsonify({'error': '用户名长度必须在6-16个字符之间'}), 400
    if not username[0].isalpha():
        return jsonify({'error': '用户名必须以字母开头'}), 400
    
    # 验证密码：最少7位的字母和数字组合
    password = data['password']
    if len(password) < 7:
        return jsonify({'error': '密码长度不能少于7位'}), 400
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return jsonify({'error': '密码必须包含字母和数字'}), 400
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': '用户名已存在'}), 400
    
    # 处理可选的真实姓名
    real_name = data.get('real_name')
    
    # 如果提供了真实姓名，进行验证
    if real_name and len(real_name) > 0:
        if not (2 <= len(real_name) <= 5):
            return jsonify({'error': '姓名昵称长度必须在2-5个汉字之间'}), 400
        if not all('\u4e00' <= char <= '\u9fff' for char in real_name):
            return jsonify({'error': '姓名昵称必须是汉字'}), 400
    
    # 获取其他字段
    is_teacher = bool(data.get('is_teacher', False))
    is_active = bool(data.get('is_active', True))
    can_post = bool(data.get('can_post', True))
    is_first_login = bool(data.get('is_first_login', True))
    grade = data.get('grade') if not is_teacher else None
    class_name = data.get('class_name') if not is_teacher else None
    
    # 如果是学生账号，验证年级和班级
    if not is_teacher:
        if not grade or not class_name:
            return jsonify({'error': '学生账号必须提供年级和班级'}), 400
        if not (1 <= int(grade) <= 5 and 1 <= int(class_name) <= 6):
            return jsonify({'error': '年级必须在1-5年级之间，班级必须在1-6班之间'}), 400
        
        # 转换为整数
        grade = int(grade)
        class_name = int(class_name)
    
    # 创建新用户
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        real_name=real_name,
        is_teacher=is_teacher,
        is_admin=False,  # 管理员创建的用户不能是管理员
        is_active=is_active,
        can_post=can_post,
        is_first_login=is_first_login,
        grade=grade,
        class_name=class_name
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # 返回新创建的用户信息
        user_data = {
            'id': new_user.id,
            'username': new_user.username,
            'real_name': new_user.real_name,
            'is_teacher': new_user.is_teacher,
            'is_admin': new_user.is_admin,
            'is_active': new_user.is_active,
            'is_first_login': new_user.is_first_login,
            'can_post': new_user.can_post,
            'grade': new_user.grade,
            'class_name': new_user.class_name
        }
        
        return jsonify({'message': '用户创建成功', 'user': user_data}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建用户失败: {str(e)}'}), 500

# 批量导入学生账号
@app.route('/api/admin/import-students', methods=['POST'])
def import_students():
    data = request.get_json()
    
    if not data or not data.get('admin_id') or not data.get('students'):
        return jsonify({'error': '管理员ID和学生数据不能为空'}), 400
    
    admin_id = data.get('admin_id')
    students = data.get('students')
    
    # 验证操作者是否为超级管理员
    admin = User.query.get(admin_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': '权限不足，只有超级管理员可以批量导入账号'}), 403
    
    # 验证学生数据
    if not isinstance(students, list) or len(students) == 0:
        return jsonify({'error': '学生数据格式不正确或为空'}), 400
    
    # 创建的用户列表
    created_users = []
    errors = []
    
    for i, student in enumerate(students):
        # 验证必需字段
        if not student.get('username') or not student.get('password') or not student.get('grade') or not student.get('class_name'):
            errors.append({
                'index': i,
                'error': '用户名、密码、年级和班级不能为空',
                'data': student
            })
            continue
        
        # 验证用户名：6-16个字符，首字符必须是字母
        username = student['username']
        if not (6 <= len(username) <= 16):
            errors.append({
                'index': i,
                'error': '用户名长度必须在6-16个字符之间',
                'data': student
            })
            continue
        
        if not username[0].isalpha():
            errors.append({
                'index': i,
                'error': '用户名必须以字母开头',
                'data': student
            })
            continue
        
        # 验证密码：最少7位的字母和数字组合
        password = student['password']
        if len(password) < 7:
            errors.append({
                'index': i,
                'error': '密码长度不能少于7位',
                'data': student
            })
            continue
        
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            errors.append({
                'index': i,
                'error': '密码必须包含字母和数字',
                'data': student
            })
            continue
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            errors.append({
                'index': i,
                'error': '用户名已存在',
                'data': student
            })
            continue
        
        # 验证年级和班级
        try:
            grade = int(student['grade'])
            class_name = int(student['class_name'])
            
            if not (1 <= grade <= 5 and 1 <= class_name <= 6):
                errors.append({
                    'index': i,
                    'error': '年级必须在1-5年级之间，班级必须在1-6班之间',
                    'data': student
                })
                continue
        except (ValueError, TypeError):
            errors.append({
                'index': i,
                'error': '年级和班级必须是数字',
                'data': student
            })
            continue
        
        # 创建新用户
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            real_name=None,  # 批量创建的学生账号不设置姓名昵称
            is_teacher=False,  # 一定是学生
            is_admin=False,  # 一定不是管理员
            is_active=True,  # 默认启用
            can_post=False,  # 默认禁止发布内容
            is_first_login=True,  # 必须首次登录修改密码和姓名
            grade=grade,
            class_name=class_name
        )
        
        try:
            db.session.add(new_user)
            created_users.append({
                'username': new_user.username,
                'grade': new_user.grade,
                'class_name': new_user.class_name
            })
        except Exception as e:
            errors.append({
                'index': i,
                'error': f'创建用户失败: {str(e)}',
                'data': student
            })
    
    # 提交事务
    try:
        db.session.commit()
        return jsonify({
            'message': f'成功导入 {len(created_users)} 个学生账号',
            'created_users': created_users,
            'errors': errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'批量导入失败: {str(e)}'}), 500

# 更新用户密码和个人信息（首次登录使用）
@app.route('/api/users/update-profile', methods=['POST'])
def update_first_login_profile():
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('password') or not data.get('real_name'):
        return jsonify({'error': '用户ID、新密码和姓名昵称不能为空'}), 400
    
    user_id = data.get('user_id')
    password = data.get('password')
    real_name = data.get('real_name')
    
    # 验证密码：最少7位的字母和数字组合
    if len(password) < 7:
        return jsonify({'error': '密码长度不能少于7位'}), 400
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return jsonify({'error': '密码必须包含字母和数字'}), 400
    
    # 验证真实姓名：2-5个汉字
    if not (2 <= len(real_name) <= 5):
        return jsonify({'error': '姓名昵称长度必须在2-5个汉字之间'}), 400
    if not all('\u4e00' <= char <= '\u9fff' for char in real_name):
        return jsonify({'error': '姓名昵称必须是汉字'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        # 更新用户信息
        user.password_hash = generate_password_hash(password)
        user.real_name = real_name
        user.is_first_login = False  # 标记为非首次登录
        
        db.session.commit()
        
        # 返回更新后的用户信息
        user_data = {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'is_teacher': user.is_teacher,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'is_first_login': user.is_first_login,
            'can_post': user.can_post,
            'grade': user.grade,
            'class_name': user.class_name
        }
        
        return jsonify({
            'message': '个人信息更新成功',
            'user': user_data
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新个人信息失败: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 确保所有表存在
        # 初始化系统配置
        if not SystemConfig.query.filter_by(key='register_enabled').first():
            SystemConfig.set_config('register_enabled', 'true', '是否开启用户注册功能')
    app.run(host='0.0.0.0', port=5000, debug=True) 