#!/bin/bash

# 猜东西游戏服务器配置脚本 (Linux)
# 支持清华源配置

echo "=== 猜东西游戏服务器配置开始 ==="

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo "请不要使用root用户运行此脚本"
   exit 1
fi

# 更新系统包管理器到清华源
echo "1. 配置清华源..."

# 备份原始sources.list
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup

# 配置清华源
sudo tee /etc/apt/sources.list > /dev/null <<EOF
# 清华大学镜像源
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $(lsb_release -cs) main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $(lsb_release -cs)-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $(lsb_release -cs)-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $(lsb_release -cs)-security main restricted universe multiverse
EOF

# 更新包列表
sudo apt update

# 安装必要的系统依赖
echo "2. 安装系统依赖..."
sudo apt install -y python3 python3-pip python3-venv redis-server nginx git curl

# 配置pip清华源
echo "3. 配置pip清华源..."
mkdir -p ~/.pip
cat > ~/.pip/pip.conf <<EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF

# 创建Python虚拟环境
echo "4. 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装Python依赖
echo "5. 安装Python依赖包..."
pip install -r requirements.txt

# 配置Redis
echo "6. 配置Redis服务..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 检查Redis状态
if sudo systemctl is-active --quiet redis-server; then
    echo "Redis服务启动成功"
else
    echo "Redis服务启动失败"
    exit 1
fi

# 配置Nginx反向代理
echo "7. 配置Nginx反向代理..."
sudo tee /etc/nginx/sites-available/guess-game > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;
    
    client_max_body_size 1M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态文件缓存
    location /static/ {
        proxy_pass http://127.0.0.1:8000/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/guess-game /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 创建systemd服务文件
echo "8. 创建系统服务..."
sudo tee /etc/systemd/system/guess-game.service > /dev/null <<EOF
[Unit]
Description=Guess Game FastAPI Application
After=network.target redis.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
sudo systemctl daemon-reload
sudo systemctl enable guess-game

# 设置防火墙规则
echo "9. 配置防火墙..."
if command -v ufw > /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 22/tcp
    echo "防火墙规则已配置"
fi

# 优化系统配置（支持高并发）
echo "10. 优化系统配置..."
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
* soft nofile 65535
* hard nofile 65535
EOF

# 优化内核参数
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
fs.file-max = 65535
EOF

sudo sysctl -p

echo "=== 配置完成 ==="
echo ""
echo "📝 接下来的步骤:"
echo "1. 编辑 .env 文件，设置你的 Qwen API Key:"
echo "   nano .env"
echo ""
echo "2. 启动服务:"
echo "   sudo systemctl start guess-game"
echo ""
echo "3. 检查服务状态:"
echo "   sudo systemctl status guess-game"
echo ""
echo "4. 查看服务日志:"
echo "   sudo journalctl -u guess-game -f"
echo ""
echo "5. 访问游戏: http://your-server-ip"
echo ""
echo "🔧 服务管理命令:"
echo "   启动: sudo systemctl start guess-game"
echo "   停止: sudo systemctl stop guess-game"
echo "   重启: sudo systemctl restart guess-game"
echo ""
echo "⚡ 系统已优化支持100+并发连接"

deactivate
