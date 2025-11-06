# backend/tests/test_auth_api.py
from fastapi.testclient import TestClient
import pytest


def test_auth_check_unauthenticated(client: TestClient):
    """
    测试在未登录状态下访问 /auth/check 接口
    """
    response = client.get("/api/v1/auth/check")
    # 断言（assert）状态码应该是 200（因为这个端点总是返回状态）
    assert response.status_code == 200
    # 断言响应的 JSON 内容
    assert response.json() == {"authenticated": False}


def test_auth_me_unauthenticated(client: TestClient):
    """
    测试在未登录状态下访问 /auth/me 接口
    应该返回 401 未认证错误
    """
    response = client.get("/api/v1/auth/me")
    # 断言状态码应该是 401 Unauthorized
    assert response.status_code == 401
    # 断言响应包含错误信息
    response_data = response.json()
    assert "detail" in response_data


def test_login_nonexistent_user(client: TestClient):
    """
    测试使用不存在的用户名登录
    """
    login_data = {"username": "nonexistent_user", "password": "any_password"}
    response = client.post("/api/v1/auth/login", json=login_data)
    # 断言状态码应该是 404 用户不存在
    assert response.status_code == 404
    # 断言响应包含错误信息
    response_data = response.json()
    assert "detail" in response_data


def test_health_check(client: TestClient):
    """
    测试健康检查端点
    """
    response = client.get("/health")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "healthy"
    assert "service" in response_data


def test_root_endpoint(client: TestClient):
    """
    测试根端点
    """
    response = client.get("/")
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data


# 你可以继续写更多测试，例如创建一个用户，然后模拟登录，再检查状态
# 以下是一个更复杂的测试示例（需要数据库中有测试用户）

@pytest.mark.skip(reason="需要数据库中存在测试用户")
def test_login_success_flow(client: TestClient):
    """
    测试完整的登录流程（需要数据库中有测试用户）
    这个测试被跳过，因为需要预先在数据库中创建测试用户
    """
    # 1. 登录
    login_data = {"username": "admin", "password": "admin123"}
    login_response = client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    # 2. 检查认证状态
    auth_response = client.get("/api/v1/auth/check")
    assert auth_response.status_code == 200
    assert auth_response.json()["authenticated"] == True
    
    # 3. 获取用户信息
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == "admin"
    
    # 4. 登出
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    
    # 5. 验证登出后状态
    auth_response_after_logout = client.get("/api/v1/auth/check")
    assert auth_response_after_logout.json()["authenticated"] == False