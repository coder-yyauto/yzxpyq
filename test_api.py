import requests
import json
import random
import string

# API基础URL
BASE_URL = 'http://localhost:5000/api'

def random_string(length=6):
    """生成随机字符串作为用户名"""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def test_register_student():
    """测试学生注册"""
    username = f"student_{random_string()}"
    print(f"\n测试学生注册: {username}")
    
    data = {
        'username': username,
        'password': 'password123',
        'real_name': f'学生{random_string(4)}',
        'grade': random.randint(1, 5),
        'class_name': random.randint(1, 6)
    }
    
    print(f"请求数据: {data}")
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    return response.json() if response.status_code == 201 else None

def test_register_teacher():
    """测试教师注册"""
    username = f"teacher_{random_string()}"
    print(f"\n测试教师注册: {username}")
    
    data = {
        'username': username,
        'password': 'password123',
        'real_name': f'教师{random_string(4)}',
        'register_code': 'teacher2024'
    }
    
    print(f"请求数据: {data}")
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    return response.json() if response.status_code == 201 else None

def test_login(username, password='password123'):
    """测试登录"""
    print(f"\n测试登录: {username}")
    
    data = {
        'username': username,
        'password': password
    }
    
    print(f"请求数据: {data}")
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":
    # 测试学生注册和登录
    student = test_register_student()
    if student:
        print(f"学生注册成功，ID: {student.get('id')}")
        # 尝试登录
        student_login = test_login(student['username'])
        if student_login:
            print(f"学生登录成功，ID: {student_login.get('id')}")
        else:
            print("学生登录失败")
    else:
        print("学生注册失败")
    
    # 测试教师注册和登录
    teacher = test_register_teacher()
    if teacher:
        print(f"教师注册成功，ID: {teacher.get('id')}")
        # 尝试登录
        teacher_login = test_login(teacher['username'])
        if teacher_login:
            print(f"教师登录成功，ID: {teacher_login.get('id')}")
        else:
            print("教师登录失败")
    else:
        print("教师注册失败") 