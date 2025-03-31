from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

app = Flask(__name__)
CORS(app)

# 配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'school.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_teacher = db.Column(db.Boolean, default=False)
    real_name = db.Column(db.String(50), nullable=False)  # 姓名
    number = db.Column(db.String(20))                     # 工号/学号
    grade = db.Column(db.String(20))                      # 年级
    class_name = db.Column(db.String(20))                 # 班级

# 点赞记录模型
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 朋友圈模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    images = db.Column(db.Text)  # 存储图片路径，用逗号分隔
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    likes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', lazy=True)
    like_records = db.relationship('Like', backref='post', lazy=True)

# 评论模型
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # 父评论ID
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

# 创建数据库表
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # 保存并压缩图片
        image = Image.open(file)
        # 如果图片太大，进行压缩
        if image.size[0] > 1200 or image.size[1] > 1200:
            image.thumbnail((1200, 1200))
        image.save(filepath, quality=85)
        
        return unique_filename
    return None

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 检查用户身份
    user_id = request.form.get('user_id')
    if user_id:
        user = db.session.get(User, user_id)
        if user and user.is_teacher:
            # 检查当前用户的图片数量
            existing_post = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).first()
            if existing_post and existing_post.images:
                image_count = len(existing_post.images.split(','))
                if image_count >= 9:
                    return jsonify({'error': '最多只能上传9张图片'}), 400
    
    filename = save_image(file)
    if filename:
        return jsonify({
            'filename': filename,
            'url': f'/uploads/{filename}'
        })
    return jsonify({'error': '不支持的文件类型'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 教师注册码
TEACHER_REGISTER_CODE = "teacher2024"  # 在实际应用中应该存储在配置文件中

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    is_teacher = data.get('is_teacher', False)
    
    # 如果是注册教师账号，需要验证注册码
    if is_teacher:
        register_code = data.get('register_code')
        if not register_code or register_code != TEACHER_REGISTER_CODE:
            return jsonify({'message': '教师注册码错误'}), 400
    
    user = User(
        username=data['username'],
        password=data['password'],
        is_teacher=is_teacher,
        real_name=data['real_name'],
        number=data.get('number'),  # 改为可选
        grade=data.get('grade'),
        class_name=data.get('class_name')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '注册成功'})

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'is_teacher': user.is_teacher,
            'real_name': user.real_name,
            'number': user.number,
            'grade': user.grade,
            'class_name': user.class_name
        })
    return jsonify({'message': '用户名或密码错误'}), 401

# 发布朋友圈
@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    post = Post(
        content=data['content'],
        images=data.get('images', ''),
        user_id=data['user_id']
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': '发布成功', 'post_id': post.id})

# 获取朋友圈列表
@app.route('/api/posts', methods=['GET'])
def get_posts():
    user_id = request.args.get('user_id')
    posts = Post.query.order_by(Post.created_at.desc()).all()
    
    def get_comment_tree(comments):
        comment_dict = {}
        root_comments = []
        
        # 构建评论树
        for comment in comments:
            comment_dict[comment.id] = {
                'id': comment.id,
                'content': comment.content,
                'user_id': comment.user_id,
                'username': db.session.get(User, comment.user_id).username,
                'real_name': db.session.get(User, comment.user_id).real_name,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'replies': []
            }
            
            if comment.parent_id:
                parent = comment_dict.get(comment.parent_id)
                if parent:
                    parent['replies'].append(comment_dict[comment.id])
            else:
                root_comments.append(comment_dict[comment.id])
        
        return root_comments
    
    return jsonify([{
        'id': post.id,
        'content': post.content,
        'images': post.images.split(',') if post.images else [],
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': post.user_id,
        'username': db.session.get(User, post.user_id).username,
        'real_name': db.session.get(User, post.user_id).real_name,
        'likes': post.likes,
        'is_liked': user_id and bool(Like.query.filter_by(user_id=user_id, post_id=post.id).first()),
        'comments': get_comment_tree(post.comments)
    } for post in posts])

# 点赞
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'message': '用户未登录'}), 401
    
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if like:
        # 取消点赞
        db.session.delete(like)
        post.likes -= 1
        db.session.commit()
        return jsonify({'message': '取消点赞成功', 'likes': post.likes})
    else:
        # 添加点赞
        like = Like(user_id=user_id, post_id=post_id)
        db.session.add(like)
        post.likes += 1
        db.session.commit()
        return jsonify({'message': '点赞成功', 'likes': post.likes})

# 评论
@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.json
    comment = Comment(
        content=data['content'],
        user_id=data['user_id'],
        post_id=post_id,
        parent_id=data.get('parent_id')  # 可选的父评论ID
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({
        'message': '评论成功',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user_id': comment.user_id,
            'username': db.session.get(User, comment.user_id).username,
            'real_name': db.session.get(User, comment.user_id).real_name,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'parent_id': comment.parent_id
        }
    })

# 删除评论接口
@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'message': '用户未登录'}), 401
    
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != user_id:
        return jsonify({'message': '无权删除此评论'}), 403
    
    if comment.replies:
        return jsonify({'message': '该评论已被回复，无法删除'}), 400
    
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': '删除成功'})

if __name__ == '__main__':
    app.run(debug=True) 