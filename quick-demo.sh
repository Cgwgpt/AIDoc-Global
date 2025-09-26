#!/bin/bash

# MedGemma AI 智能诊疗助手 - 快速演示脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  MedGemma AI 智能诊疗助手${NC}"
    echo -e "${BLUE}  快速演示脚本${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查系统要求
check_requirements() {
    print_message "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 检查Docker服务
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    
    # 检查端口占用
    if lsof -i :8000 &> /dev/null; then
        print_warning "端口 8000 已被占用，将尝试停止现有服务"
        docker-compose down 2>/dev/null || true
    fi
    
    print_message "系统要求检查通过 ✓"
}

# 快速部署
quick_deploy() {
    print_message "开始快速部署..."
    
    # 创建必要目录
    mkdir -p data ssl logs
    
    # 启动服务
    print_message "启动Docker服务..."
    docker-compose up -d
    
    # 等待服务启动
    print_message "等待服务启动..."
    sleep 15
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_message "服务启动成功 ✓"
    else
        print_error "服务启动失败"
        docker-compose logs
        exit 1
    fi
}

# 健康检查
health_check() {
    print_message "执行健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_message "健康检查通过 ✓"
            return 0
        fi
        
        print_message "健康检查中... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    print_error "健康检查超时"
    return 1
}

# 初始化管理员
init_admin() {
    print_message "初始化管理员账户..."
    
    # 等待数据库就绪
    sleep 5
    
    # 运行初始化脚本
    if docker-compose exec -T medgemma-app python init_admin.py 2>/dev/null; then
        print_message "管理员账户初始化成功 ✓"
    else
        print_warning "管理员账户可能已存在，跳过初始化"
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    print_header
    echo ""
    print_message "🎉 部署完成！"
    echo ""
    echo -e "${GREEN}访问地址：${NC}"
    echo -e "  🌐 主应用: ${BLUE}http://localhost:8000${NC}"
    echo -e "  🎨 管理界面: ${BLUE}http://localhost:8000/ui/${NC}"
    echo -e "  📚 API文档: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "  ❤️  健康检查: ${BLUE}http://localhost:8000/health${NC}"
    echo ""
    echo -e "${GREEN}预设账户：${NC}"
    echo -e "  👑 系统管理员: ${YELLOW}admin@medgemma.com${NC} / ${YELLOW}SecureAdmin2024!${NC}"
    echo -e "  🏥 医院管理员: ${YELLOW}manager@hospital.com${NC} / ${YELLOW}HospitalManager123!${NC}"
    echo -e "  👤 普通用户: ${YELLOW}demo@test.com${NC} / ${YELLOW}demo123${NC}"
    echo ""
    echo -e "${GREEN}服务管理：${NC}"
    echo -e "  📊 查看状态: ${BLUE}docker-compose ps${NC}"
    echo -e "  📝 查看日志: ${BLUE}docker-compose logs -f${NC}"
    echo -e "  🛑 停止服务: ${BLUE}docker-compose down${NC}"
    echo -e "  🔄 重启服务: ${BLUE}docker-compose restart${NC}"
    echo ""
    echo -e "${GREEN}快速操作：${NC}"
    echo -e "  🚀 一键启动: ${BLUE}./docker-start.sh${NC}"
    echo -e "  🏭 生产部署: ${BLUE}./docker-start.sh production${NC}"
    echo -e "  🧪 测试配置: ${BLUE}./test-docker.sh${NC}"
    echo ""
}

# 演示API调用
demo_api() {
    print_message "演示API调用..."
    
    echo ""
    echo -e "${BLUE}API调用示例：${NC}"
    echo ""
    
    # 健康检查
    echo -e "${YELLOW}1. 健康检查：${NC}"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
    echo ""
    
    # 用户注册
    echo -e "${YELLOW}2. 用户注册示例：${NC}"
    curl -s -X POST http://localhost:8000/api/users/register \
        -H 'Content-Type: application/json' \
        -d '{
            "name": "演示用户",
            "organization": "演示医院",
            "phone": "13800000000",
            "email": "demo@example.com",
            "password": "demo123"
        }' | jq . 2>/dev/null || echo "注册请求已发送"
    echo ""
    
    # 用户登录
    echo -e "${YELLOW}3. 用户登录示例：${NC}"
    curl -s -X POST http://localhost:8000/api/users/login \
        -H 'Content-Type: application/json' \
        -d '{
            "email": "demo@test.com",
            "password": "demo123"
        }' | jq . 2>/dev/null || echo "登录请求已发送"
    echo ""
}

# 主程序
main() {
    print_header
    
    # 检查系统要求
    check_requirements
    
    # 快速部署
    quick_deploy
    
    # 健康检查
    if health_check; then
        # 初始化管理员
        init_admin
        
        # 显示访问信息
        show_access_info
        
        # 演示API调用
        demo_api
        
        print_message "🎉 快速演示完成！"
        print_message "现在可以访问 http://localhost:8000/ui/ 开始使用系统"
        
    else
        print_error "部署失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# 捕获中断信号
trap 'print_warning "演示被中断"; exit 1' INT TERM

# 运行主程序
main "$@"
