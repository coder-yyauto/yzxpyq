from flask import Flask, request, jsonify
import os
import time
import secrets
from werkzeug.utils import secure_filename
import logging
import sys

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("upload_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('upload_test')

app = Flask(__name__)

# 配置上传参数
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tiff'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/uploads', methods=['POST'])
def upload_file():
    logger.info("\n====== 开始处理文件上传请求 =======")
    logger.info(f"请求方法: {request.method}")
    logger.info(f"请求URL: {request.url}")
    logger.info(f"请求头: {dict(request.headers)}")
    logger.info(f"请求表单: {request.form}")
    logger.info(f"请求文件列表键: {list(request.files.keys())}")
    
    try:
        # 检查是否有文件部分
        if 'files[]' not in request.files:
            if 'file' in request.files:
                # 如果使用单文件上传
                files = [request.files['file']]
                logger.info("使用单文件上传模式")
            else:
                logger.error("错误: 没有文件部分")
                logger.error(f"请求文件对象: {request.files}")
                logger.error(f"请求form数据: {request.form}")
                return jsonify({'error': '没有文件部分'}), 400
        else:
            # 使用多文件上传
            files = request.files.getlist('files[]')
            logger.info(f"使用多文件上传模式, 找到 {len(files)} 个文件")
            for i, file in enumerate(files):
                logger.info(f"文件 {i+1} 信息: 名称={file.filename}, 内容类型={file.content_type}")
        
        user_id = request.form.get('user_id')
        logger.info(f"用户ID: {user_id}, 文件数量: {len(files)}")
        
        if not files or all(file.filename == '' for file in files):
            logger.error("错误: 没有选择文件")
            return jsonify({'error': '没有选择文件'}), 400
        
        if user_id is None:
            logger.error("错误: 用户ID不能为空")
            return jsonify({'error': '用户ID不能为空'}), 400
        
        valid_filenames = []
        
        # 限制最多上传9张图片
        for i, file in enumerate(files):
            if i >= 9:
                break
                
            if file.filename == '':
                logger.warning(f"文件 {i+1} 没有文件名，跳过")
                continue
                
            logger.info(f"处理文件 {i+1}: {file.filename}, 类型: {file.content_type}")
            if file and allowed_file(file.filename):
                try:
                    # 生成安全的文件名
                    filename = secure_filename(file.filename)
                    # 添加时间戳和随机字符串，确保文件名唯一
                    basename, extension = os.path.splitext(filename)
                    unique_filename = f"{basename}_{int(time.time())}_{secrets.token_hex(4)}{extension}"
                    
                    # 打印当前工作目录和目标路径
                    logger.info(f"当前工作目录: {os.getcwd()}")
                    logger.info(f"上传目录: {app.config['UPLOAD_FOLDER']}")
                    
                    # 确保上传目录存在
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # 保存文件
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    logger.info(f"尝试保存文件到: {file_path}")
                    file.save(file_path)
                    
                    # 验证文件是否确实保存成功
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        logger.info(f"文件 {i+1} 保存成功: {unique_filename}, 大小: {file_size} 字节")
                        valid_filenames.append(unique_filename)
                    else:
                        logger.error(f"错误: 文件 {unique_filename} 保存失败, 文件不存在")
                except Exception as e:
                    logger.exception(f"保存文件 {file.filename} 时出错: {str(e)}")
            else:
                logger.warning(f"文件 {file.filename} 类型不允许, 允许的类型: {ALLOWED_EXTENSIONS}")
        
        if not valid_filenames:
            logger.error("错误: 没有有效的图片文件")
            return jsonify({'error': '没有有效的图片文件'}), 400
            
        logger.info(f"成功上传 {len(valid_filenames)} 张图片")
        response_data = {
            'message': f'成功上传{len(valid_filenames)}张图片', 
            'filenames': valid_filenames
        }
        logger.info(f"响应数据: {response_data}")
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"上传处理过程中发生异常: {str(e)}")
        return jsonify({'error': f'上传处理过程中发生异常: {str(e)}'}), 500

@app.route('/')
def index():
    return '''
    <!doctype html>
    <title>上传测试</title>
    <h1>上传图片测试</h1>
    <form method=post action="/api/uploads" enctype=multipart/form-data>
      <input type=file name=files[] multiple>
      <input type=hidden name=user_id value=1>
      <input type=submit value=上传>
    </form>
    '''

if __name__ == "__main__":
    port = 5001
    logger.info(f"启动测试服务器在端口 {port}...")
    app.run(host='0.0.0.0', port=port, debug=True) 