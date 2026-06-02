import os

from fastapi import APIRouter, Depends

from app.interfaces.errors.exceptions import BadRequestException
from app.interfaces.schema.base import Response
from app.interfaces.schema.shell import ExecCommandRequest, ViewShellRequest, WaitForProcessRequest
from app.interfaces.service_dependencies import get_shell_service
from app.models.shell import ShellExecResult, ShellViewResult, ShellWaitResult, ShellWriteResult, WriteToProcessRequest, \
    ShellKillResult, KillProcessRequest
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


@router.post(
    path="/view-shell",
    response_model=Response[ShellViewResult],
)
async def view_shell(
        request: ViewShellRequest,
        shell_service: ShellService = Depends(get_shell_service)
) -> Response[ShellViewResult]:
    """根据传递的会话id+是否返回控制台标识获取Shell命令执行结果"""
    # 1.判断下Shell会话id是否存在
    if not request.session_id or request.session_id == "":
        raise BadRequestException("Shell会话id为空")

    # 2.调用服务获取命令执行结果
    result = await shell_service.view_shell(request.session_id, request.console)

    return Response.success(data=result)


@router.post(
    path="/wait-for-process",
    response_model=Response[ShellWaitResult],
)
async def wait_for_process(
        request: WaitForProcessRequest,
        shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellWaitResult]:
    """传递会话id+秒数执行等待并获取等待结果"""
    # 1.判断下Shell会话id是否存在
    if not request.session_id or request.session_id == "":
        raise BadRequestException("Shell会话id为空")

    # 2.调用服务
    result = await shell_service.wait_for_process(request.session_id, request.seconds)

    return Response.success(
        msg=f"进程结束，返回状态码(returncode)：{result.returncode}",
        data=result
    )


@router.post(
    path="/write-to-process",
    response_model=Response[ShellWriteResult]
)
async def write_to_process(
        request: WriteToProcessRequest,
        shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellWriteResult]:
    """根据传递的会话+写入内容+按下回车标识向指定子进程"""
    # 1.判断下Shell会话id是否存在
    if not request.session_id or request.session_id == "":
        raise BadRequestException("Shell会话id为空")

    result = await shell_service.wait_to_process(
        session_id=request.session_id,
        input_text=request.input_text,
        press_enter=request.press_enter,
    )

    return Response.success(
        msg="向进程写入数据成功",
        data=result
    )


@router.post(
    path="/kill-process",
    response_model=Response[ShellKillResult]
)
async def kill_process(
        request: KillProcessRequest,
        shell_service: ShellService = Depends(get_shell_service),
) -> Response[KillProcessRequest]:
    """根据传递的会话id关闭指定会话"""
    # 1.判断下Shell会话id是否存在
    if not request.session_id or request.session_id == "":
        raise BadRequestException("Shell会话id为空")

    result = await shell_service.kill_process(session_id=request.session_id)

    return Response.success(
        msg="进程终止" if result.status == "terminated" else "进程已结束",
        data=result
    )
