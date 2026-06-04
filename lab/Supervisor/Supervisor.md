# Supervisor 进程管理器

### Debian/Ubuntu/Centos 中通过 apt/yum 安装（生产环境推荐）
``` bash
# Debian/Ubuntu
apt-get install supervisor

# Centos
yum install supervisor
```

#### apt-get 安装后，supervisor的主配置文件在(不完整)
``` bash
/etc/supervisor/supervisord.conf
```
#### 子配置文件在
``` bash
/etc/supervisor/conf.d/*.conf
```

如果使用supervisor管理fastapi项目，可以在当前项目下添加一个 ```supervisor.conf```,然后运行：
``` bash
supervisord -c supervisord.conf -n
```