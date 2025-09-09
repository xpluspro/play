# 猜东西游戏

一个基于FastAPI和LangChain的智能猜谜游戏，支持多人在线游戏，集成通义千问AI。

## 功能特点

- 🎯 多种游戏主题（动物、水果、物品、地点等）
- 🤖 智能AI对话系统（基于通义千问）
- ⏱️ 实时计时器
- 📊 游戏统计和排行
- 🌐 Web界面，支持多设备访问
- ⚡ 高性能架构，支持100+并发用户
- 🔄 实时WebSocket通信
- 📱 响应式设计，支持手机和电脑

## 技术栈

### 后端
- **FastAPI**: 现代高性能Web框架
- **LangChain**: AI应用开发框架
- **Redis**: 会话存储和缓存
- **WebSocket**: 实时通信
- **Uvicorn**: ASGI服务器

### 前端
- **HTML5/CSS3**: 现代Web界面
- **JavaScript**: 动态交互
- **WebSocket客户端**: 实时通信

### AI服务
- **通义千问 (Qwen)**: 阿里云大语言模型

## 快速开始

### 环境要求
- Python 3.8+
- Redis 6.0+
- 2核4G服务器（推荐配置）

### Windows安装

```bash
# 克隆项目
git clone <repository-url>
cd guess-game

# 运行配置脚本（管理员权限）
.\setup_simple.bat
```

### Linux安装

```bash
# 克隆项目
git clone <repository-url>
cd guess-game

# 运行配置脚本
chmod +x setup_linux.sh
./setup_linux.sh
```

### 手动配置

1. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate.bat  # Windows
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制并编辑.env文件
cp .env.example .env
# 编辑.env文件，设置QWEN_API_KEY
```

4. **启动Redis**
```bash
# Linux
sudo systemctl start redis-server

# Docker方式（推荐）
docker run -d -p 6379:6379 redis:alpine
```

5. **启动服务器**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 配置说明

### 环境变量 (.env)
```env
QWEN_API_KEY=your_qwen_api_key_here          # 通义千问API密钥
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # API地址
REDIS_URL=redis://localhost:6379/0           # Redis连接地址
MAX_CONCURRENT_USERS=100                     # 最大并发用户数
SESSION_TIMEOUT=3600                         # 会话超时时间（秒）
```

### 游戏配置

游戏题目在 `models.py` 中的 `GAME_PROMPTS` 字典中配置：

```python
GAME_PROMPTS = {
    "animal": GamePrompt(
        name="神秘动物",
        answer="熊猫",
        system_prompt="...",  # 系统提示词
        hints=["它是哺乳动物", "它很稀有"],  # 提示信息
        max_attempts=15  # 最大尝试次数
    ),
    # 更多游戏...
}
```

## 使用说明

### 访问游戏
1. 打开浏览器访问 `http://localhost:8000`
2. 选择游戏主题
3. 通过提问来猜出答案
4. 查看计时器和统计信息

### 游戏玩法
- 用户通过不同的URL后缀访问不同主题的游戏
- 向AI提问来获取线索（例如："这是动物吗？"）
- AI会给出"是/否"或简短描述性回答
- 在限定次数内猜出正确答案

### URL路由
- `/` - 主页，游戏选择
- `/game/animal` - 动物主题
- `/game/fruit` - 水果主题  
- `/game/object` - 物品主题
- `/game/place` - 地点主题

## API文档

### 主要API端点

- `GET /` - 游戏主页
- `GET /game/{game_id}` - 游戏页面
- `GET /api/games` - 获取游戏列表
- `POST /api/start_game/{game_id}` - 开始新游戏
- `POST /api/guess` - 提交猜测
- `GET /api/hints/{game_id}` - 获取提示
- `GET /api/session/{session_id}/history` - 获取聊天历史
- `WS /ws/{session_id}` - WebSocket连接

### 请求示例

```javascript
// 开始游戏
const response = await fetch('/api/start_game/animal', {
    method: 'POST'
});
const { session_id } = await response.json();

// 提交猜测
const guessResponse = await fetch('/api/guess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        guess: "这是熊猫吗？",
        session_id: session_id
    })
});
```

## 部署说明

### 生产环境部署

1. **使用Nginx反向代理**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **使用systemd管理服务**
```bash
# 服务文件已在setup_linux.sh中自动创建
sudo systemctl start guess-game
sudo systemctl enable guess-game
```

3. **性能优化**
- 使用多进程部署（workers=4）
- Redis持久化配置
- 内核参数优化（已包含在配置脚本中）

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## 性能特性

- **高并发支持**: 优化后支持100+并发用户
- **异步架构**: 基于FastAPI的异步处理
- **连接池**: Redis连接池复用
- **会话管理**: 基于Redis的分布式会话
- **负载均衡**: 支持多进程部署

## 开发指南

### 添加新游戏主题

1. 在 `models.py` 中添加新的游戏配置：
```python
GAME_PROMPTS["new_theme"] = GamePrompt(
    name="新主题",
    answer="答案",
    system_prompt="系统提示词...",
    hints=["提示1", "提示2"],
    max_attempts=10
)
```

2. 在前端添加对应的图标和描述

### 自定义AI响应

修改 `chat_service.py` 中的 `get_response` 方法来自定义AI的响应逻辑。

### 扩展统计功能

可以在Redis中存储更多统计数据，如用户排行、游戏历史等。

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 检查Redis服务是否启动
   - 确认连接地址正确

2. **API密钥错误**  
   - 检查.env文件中的QWEN_API_KEY配置
   - 确认API密钥有效且有足够额度

3. **端口占用**
   - 检查8000端口是否被占用
   - 修改端口配置

4. **依赖安装失败**
   - 使用清华源: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`
   - 检查Python版本兼容性

### 日志查看

```bash
# Linux systemd服务日志
sudo journalctl -u guess-game -f

# 直接运行时的日志
uvicorn main:app --log-level debug
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 联系方式

如有问题请提交Issue或联系开发者。
