import os

from fastapi import APIRouter, Depends

from app.interfaces.schema.base import Response
from app.interfaces.schema.shell import ExecCommandRequest
from app.interfaces.service_dependencies import get_shell_service
from app.models.shell import ShellExecResult
from app.services.shell import ShellService

# Shell模块路由
router = APIRouter(prefix="/shell", tags=["Shell模块"])


@router.post(
    path="/exec-command",
    response_model=Response[ShellExecResult],
)
async def exec_command(
        request: ExecCommandRequest,
        shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellExecResult]:
    """在指定的Shell会话中运行命令"""
    # 1.判断是否传递了session_id，若不存在则新建
    if not request.session_id or request.session_id == "":
        request.session_id = shell_service.create_session_id()

    # 2.判断是否传递了执行目录，如果未传递则使用根目录作为执行路径
    if not request.exec_dir or request.exec_dir == "":
        request.exec_dir = os.path.expanduser("~")

    # 3.调用服务执行命令获取结果
    result = await shell_service.exec_command(
        session_id=request.session_id,
        exec_dir=request.exec_dir,
        command=request.command,
    )

    return Response.success(data=result)
