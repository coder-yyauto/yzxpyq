from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import time
import secrets
import json
import shutil
import base64
import uuid

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
    real_name = db.Column(db.String(80), nullable=False)
    is_teacher = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)  # 超级管理员标识
    is_active = db.Column(db.Boolean, default=True)  # 用户是否启用
    grade = db.Column(db.Integer, nullable=True)  # 年级（1-5）
    class_name = db.Column(db.Integer, nullable=True)  # 班级（1-6）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 动态模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.String(500), nullable=True)  # 存储图片文件名，用逗号分隔
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    disable_comments = db.Column(db.Boolean, default=False)  # 是否禁止评论
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))

# 评论模型
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic'))
    post = db.relationship('Post', backref=db.backref('likes', lazy='dynamic', cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),)

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
        
    # 检查真实姓名是否已存在
    existing_real_name = User.query.filter_by(real_name=data['real_name']).first()
    if existing_real_name:
        return jsonify({'error': '该真实姓名已被注册'}), 400
    
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
    
    # 返回用户信息（不包含密码）
    user_data = {
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'is_teacher': user.is_teacher,
        'is_admin': user.is_admin,
        'is_active': user.is_active,
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

# 删除评论
@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404
    
    # 检查是否是评论作者
    if str(comment.user_id) != user_id:
        return jsonify({'error': '您没有权限删除该评论'}), 403
    
    try:
        # 如果有回复，需要一并删除
        for reply in comment.replies:
            db.session.delete(reply)
        
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': '评论已删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除评论失败: {str(e)}'}), 500

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
    
    # 检查是否是教师且是动态作者
    if str(post.user_id) != user_id or not user.is_teacher:
        return jsonify({'error': '您没有权限删除该动态'}), 403
    
    try:
        # 删除相关的点赞、评论
        for like in post.likes:
            db.session.delete(like)
        
        for comment in post.comments:
            for reply in comment.replies:
                db.session.delete(reply)
            db.session.delete(comment)
        
        # 删除动态
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': '动态已删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

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
    
    # 防止管理员重置自己的密码（应该走正常修改密码流程）
    if int(target_user_id) == int(admin_id):
        return jsonify({'error': '不能通过此接口重置自己的密码'}), 400
    
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 确保所有表存在
    app.run(host='0.0.0.0', port=5000, debug=True) 