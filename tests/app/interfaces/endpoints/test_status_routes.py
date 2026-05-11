from fastapi.testclient import TestClient


def test_get_status(client: TestClient):
    """创建获取应用状态的端点"""

    # 1.请求获取状态api得到响应
    response = client.get("/api/status")
    data = response.json()

    # 2.校验响应内容是否正确
    assert response.status_code == 200
    assert data.get("code") == 200
