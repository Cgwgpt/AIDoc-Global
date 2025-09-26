#!/bin/zsh
set -euo pipefail

# 项目根目录
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT_DIR"


# 颜色输出（兼容 bash/zsh）
blue(){ echo "\033[1;34m$1\033[0m"; }
green(){ echo "\033[1;32m$1\033[0m"; }
red(){ echo "\033[1;31m$1\033[0m"; }

APP_PORT=${PORT:-8000}
UPSTREAM_DEFAULT="https://ollama-medgemma-944093292687.us-central1.run.app"

# 支持多种配置方式（兼容 zsh 未定义变量）
if [ "${MEDGEMMA_UPSTREAM:-}" != "" ]; then
  # 环境变量方式
  export MEDGEMMA_UPSTREAM
  blue "使用环境变量配置的上游服务: $MEDGEMMA_UPSTREAM"
elif [ -f "config.json" ]; then
  # 配置文件方式
  blue "使用配置文件 config.json 中的上游服务配置"
  # 配置文件会在应用启动时自动加载
else
  # 默认配置
  export MEDGEMMA_UPSTREAM=$UPSTREAM_DEFAULT
  blue "使用默认上游服务: $UPSTREAM_DEFAULT"
fi

blue "[1/3] 准备 Python 虚拟环境 (.venv)"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

blue "[2/3] 安装依赖 (如网络慢可自行改为国内镜像)"
pip install -r requirements.txt

blue "[3/3] 启动服务 http://localhost:${APP_PORT}/ui/"
exec uvicorn server.main:app --host 0.0.0.0 --port ${APP_PORT} --reload


