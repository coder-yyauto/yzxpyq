"""
用户账号管理相关API
"""

import pandas as pd
from werkzeug.utils import secure_filename
import os

# 添加文件上传配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    if real_name and len(real_name) > 5:
        return jsonify({'error': '姓名昵称长度不能超过5个汉字'}), 400
    
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

@user_bp.route('/batch_import', methods=['POST'])
@login_required
def batch_import_users():
    if not current_user.is_admin:
        return jsonify({'error': '权限不足'}), 403
        
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式'}), 400
        
    try:
        # 读取Excel文件
        df = pd.read_excel(file)
        required_columns = ['登录账号', '年级', '班级']
        
        # 验证必要的列是否存在
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Excel文件格式不正确，必须包含：登录账号、年级、班级'}), 400
            
        success_count = 0
        error_messages = []
        
        for _, row in df.iterrows():
            try:
                username = str(row['登录账号']).strip()
                grade = str(row['年级']).strip()
                class_name = str(row['班级']).strip()
                
                # 验证数据
                if not username or not grade or not class_name:
                    error_messages.append(f'行 {_ + 2}: 数据不完整')
                    continue
                    
                # 检查用户名是否已存在
                if User.query.filter_by(username=username).first():
                    error_messages.append(f'行 {_ + 2}: 用户名 {username} 已存在')
                    continue
                    
                # 创建新用户
                new_user = User(
                    username=username,
                    password=generate_password_hash('123456'),  # 默认密码
                    grade=grade,
                    class_name=class_name,
                    is_admin=False,
                    is_first_login=True
                )
                db.session.add(new_user)
                success_count += 1
                
            except Exception as e:
                error_messages.append(f'行 {_ + 2}: {str(e)}')
                
        db.session.commit()
        
        return jsonify({
            'message': f'成功导入 {success_count} 个用户',
            'errors': error_messages if error_messages else None
        })
        
    except Exception as e:
        return jsonify({'error': f'导入失败：{str(e)}'}), 500 