# 开发环境
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOSTNAME=sandbox
ENV UV_PROJECT_ENVIRONMENT="/venv"
ENV UV_LINK_MODE=copy

# 1.安装基础工具+OpenSSH Server
# mkdir /var/run/sshd是SSH服务启动必须的目录
# /var/lib/apt/lists*是apt包索引缓存
RUN apt-get update && apt-get install -y \
    ca-certificates git curl openssh-server\
    && rm -rf /var/lib/apt/lists* \
    && mkdir /var/run/sshd

# 2.配置SSH的账户密码
RUN echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# 3.安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4.设置工作环境
WORKDIR /sandbox

# 5.预先配置环境，将基础依赖+Python版本同步到沙箱中并创建环境
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 6.开放SSH端口(22)和应用端口(8080)
EXPOSE 22 8080

# 7.启动SSH服务(必须使用-D在前台运行，否则容器会退出)
CMD ["/usr/sbin/sshd", "-D"]