import os
import uuid
from datetime import datetime
from typing import Tuple, BinaryIO

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.domain.external.file_storage import FileStorage

import logging

from app.domain.models.file import File
from app.domain.repositories.file_repository import FileRepository
from app.infrastructure.storage.cos import Cos

logger = logging.getLogger(__name__)

class CosFileStorage(FileStorage):
    """基于COS的文件存储拓展"""

    def __init__(
            self,
            bucket: str,
            cos: Cos,
            file_repository: FileRepository
    ) -> None:
        """构造函数，完成cos文件存储桶扩展初始化"""
        self.cos = cos
        self.file_repository = file_repository
        self.bucket = bucket

    async def upload_file(self, upload_file: UploadFile) -> File:
        """根据传递的文件源上传文件后返回文件信息"""
        try:
            file_id = str(uuid.uuid4())
            _, file_extension = os.path.splitext(upload_file.filename)
            if not file_extension:
                file_extension = ""

            date_path = datetime.now().strftime("%Y/%m/%d")
            cos_key = f"{date_path}/{file_id}{file_extension}"

            # 使用fastapi的线程池上传文件
            await run_in_threadpool(
                self.cos.client.put_object,
                Bucket=self.bucket,
                Body=upload_file.file,
                Key=cos_key,
            )
            logger.info(f"文件上传成功：{upload_file.filename} (ID: {file_id})")

            # 构建file模型并将数据存储到数据库
            file = File(
                id=file_id,
                filename=upload_file.filename,
                key=cos_key,
                extension=file_extension,
                mime_type=upload_file.content_type or "",
                size=upload_file.size
            )
            await self.file_repository.save(file)

            return file
        except Exception as e:
            logger.error(f"上传文件[{upload_file.filename}]失败：{str(e)}")
            raise

    async def download_file(self, file_id: str) -> Tuple[BinaryIO, File]:
        """根据传递的文件id下载文件，并返回文件源+文件信息"""
        try:
            file = await self.file_repository.get_by_id(file_id)
            if not file:
                raise ValueError(f"该文件不存在，文件id：{file_id}")

            response = await run_in_threadpool(
                self.cos.client.get_object,
                Bucket=self.bucket,
                Key=file.key,
            )

            return response["Body"], file
        except Exception as e:
            logger.error(f"下载文件[{file_id}]失败：{str(e)}")
            raise