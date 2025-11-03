#!/usr/bin/env python3
"""
测试前端API响应，验证超级管理员字段
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_user_response_fields():
    """测试用户响应字段"""
    print("🚀 测试用户API响应字段")
    
    # 测试超级管理员登录
    print("\n=== 测试超级管理员登录响应 ===")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": "admin"})
    
    if response.status_code == 200:
        data = response.json()
        user = data.get("user", {})
        
        print("✅ 登录成功，用户字段:")
        for key, value in user.items():
            print(f"   {key}: {value}")
        
        # 检查关键字段
        required_fields = ['is_admin', 'is_super_admin', 'role']
        missing_fields = []
        
        for field in required_fields:
            if field not in user:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
        else:
            print("✅ 所有必需字段都存在")
        
        # 验证超级管理员标识
        if user.get('is_super_admin') == True:
            print("✅ is_super_admin 字段正确")
        else:
            print(f"❌ is_super_admin 字段错误: {user.get('is_super_admin')}")
        
        if user.get('is_admin') == True:
            print("✅ is_admin 字段正确")
        else:
            print(f"❌ is_admin 字段错误: {user.get('is_admin')}")
        
        cookies = response.cookies
        
        # 测试当前用户信息API
        print("\n=== 测试当前用户信息API ===")
        me_response = requests.get(f"{BASE_URL}/api/v1/auth/me", cookies=cookies)
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print("✅ 获取当前用户信息成功")
            print("   用户字段:")
            for key, value in me_data.items():
                print(f"     {key}: {value}")
            
            # 验证字段一致性
            if me_data.get('is_super_admin') == user.get('is_super_admin'):
                print("✅ /auth/me 的 is_super_admin 字段与登录响应一致")
            else:
                print("❌ /auth/me 的 is_super_admin 字段与登录响应不一致")
        else:
            print(f"❌ 获取当前用户信息失败: {me_response.status_code}")
    
    else:
        print(f"❌ 超级管理员登录失败: {response.status_code}")
    
    # 测试普通管理员登录
    print("\n=== 测试普通管理员登录响应 ===")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": "jlpss-chenjianxiong"})
    
    if response.status_code == 200:
        data = response.json()
        user = data.get("user", {})
        
        print("✅ 登录成功，用户字段:")
        for key, value in user.items():
            print(f"   {key}: {value}")
        
        # 验证普通管理员标识
        if user.get('is_super_admin') == False:
            print("✅ is_super_admin 字段正确 (False)")
        else:
            print(f"❌ is_super_admin 字段错误: {user.get('is_super_admin')}")
        
        if user.get('is_admin') == True:
            print("✅ is_admin 字段正确 (True)")
        else:
            print(f"❌ is_admin 字段错误: {user.get('is_admin')}")
    
    else:
        print(f"❌ 普通管理员登录失败: {response.status_code}")

def test_user_list_response():
    """测试用户列表响应"""
    print("\n=== 测试用户列表API响应 ===")
    
    # 先登录超级管理员
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                                 json={"username": "admin"})
    
    if login_response.status_code == 200:
        cookies = login_response.cookies
        
        # 获取用户列表
        users_response = requests.get(f"{BASE_URL}/api/v1/users", cookies=cookies)
        
        if users_response.status_code == 200:
            data = users_response.json()
            users = data.get('items', [])
            
            print(f"✅ 获取用户列表成功，共 {len(users)} 个用户")
            
            for user in users:
                username = user.get('username')
                role = user.get('role')
                is_admin = user.get('is_admin')
                is_super_admin = user.get('is_super_admin')
                
                print(f"   用户: {username}")
                print(f"     role: {role}")
                print(f"     is_admin: {is_admin}")
                print(f"     is_super_admin: {is_super_admin}")
                
                # 验证字段逻辑
                if role == 'super_admin' and is_super_admin == True and is_admin == True:
                    print(f"     ✅ 超级管理员字段逻辑正确")
                elif role == 'admin' and is_super_admin == False and is_admin == True:
                    print(f"     ✅ 普通管理员字段逻辑正确")
                elif role == 'user' and is_super_admin == False and is_admin == False:
                    print(f"     ✅ 普通用户字段逻辑正确")
                else:
                    print(f"     ❌ 用户字段逻辑异常")
        else:
            print(f"❌ 获取用户列表失败: {users_response.status_code}")
    else:
        print(f"❌ 超级管理员登录失败: {login_response.status_code}")

def main():
    """主函数"""
    print("🔍 测试前端API响应字段")
    
    test_user_response_fields()
    test_user_list_response()
    
    print("\n🎉 API字段测试完成!")

if __name__ == "__main__":
    main()