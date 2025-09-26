#!/bin/bash

# MedGemma AI 智能诊疗助手 - Docker 快速启动脚本
# 支持开发环境和生产环境部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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
    echo -e "${BLUE}  Docker 快速部署脚本${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查Docker和Docker Compose是否安装
check_dependencies() {
    print_message "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_message "依赖检查通过 ✓"
}

# 创建必要的目录
create_directories() {
    print_message "创建必要的目录..."
    
    mkdir -p data
    mkdir -p ssl
    mkdir -p logs
    
    print_message "目录创建完成 ✓"
}

# 初始化环境配置
init_environment() {
    print_message "初始化环境配置..."
    
    # 创建环境变量文件
    if [ ! -f .env ]; then
        cat > .env << EOF
# MedGemma AI 智能诊疗助手 - 环境配置
ADMIN_TOKEN=secret-admin
MEDGEMMA_UPSTREAM=https://ollama-medgemma-944093292687.us-central1.run.app
APP_DB_PATH=/app/data/app.db
REDIS_PASSWORD=medgemma123

# 可选配置
PORT=8000
LOG_LEVEL=info
EOF
        print_message "环境配置文件 .env 已创建"
    fi
    
    # 确保配置文件存在
    if [ ! -f config.json ]; then
        print_warning "config.json 文件不存在，将使用默认配置"
    fi
    
    print_message "环境配置初始化完成 ✓"
}

# 构建镜像
build_images() {
    print_message "构建Docker镜像..."
    
    docker-compose build --no-cache
    
    print_message "镜像构建完成 ✓"
}

# 启动服务
start_services() {
    print_message "启动服务..."
    
    # 停止可能存在的容器
    docker-compose down 2>/dev/null || true
    
    # 启动服务
    docker-compose up -d
    
    print_message "服务启动完成 ✓"
}

# 等待服务就绪
wait_for_services() {
    print_message "等待服务就绪..."
    
    # 等待主应用启动
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            print_message "主应用服务就绪 ✓"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_error "主应用服务启动超时"
            docker-compose logs medgemma-app
            exit 1
        fi
        
        sleep 2
    done
    
    # 等待Redis启动
    for i in {1..15}; do
        if docker-compose exec -T redis redis-cli ping &>/dev/null; then
            print_message "Redis服务就绪 ✓"
            break
        fi
        
        if [ $i -eq 15 ]; then
            print_error "Redis服务启动超时"
            exit 1
        fi
        
        sleep 2
    done
}

# 初始化管理员账户
init_admin() {
    print_message "初始化管理员账户..."
    
    # 等待数据库就绪
    sleep 5
    
    # 运行初始化脚本
    docker-compose exec -T medgemma-app python init_admin.py || {
        print_warning "管理员账户可能已存在，跳过初始化"
    }
    
    print_message "管理员账户初始化完成 ✓"
}

# 显示服务状态
show_status() {
    print_message "服务状态："
    docker-compose ps
    
    echo ""
    print_message "访问地址："
    echo -e "  ${GREEN}主应用:${NC} http://localhost:8000"
    echo -e "  ${GREEN}管理界面:${NC} http://localhost:8000/ui/"
    echo -e "  ${GREEN}API文档:${NC} http://localhost:8000/docs"
    echo -e "  ${GREEN}健康检查:${NC} http://localhost:8000/health"
    
    echo ""
    print_message "预设账户："
    echo -e "  ${GREEN}系统管理员:${NC} admin@medgemma.com / SecureAdmin2024!"
    echo -e "  ${GREEN}医院管理员:${NC} manager@hospital.com / HospitalManager123!"
    echo -e "  ${GREEN}普通用户:${NC} demo@test.com / demo123"
}

# 显示日志
show_logs() {
    print_message "显示服务日志..."
    docker-compose logs -f
}

# 停止服务
stop_services() {
    print_message "停止服务..."
    docker-compose down
    print_message "服务已停止 ✓"
}

# 清理资源
cleanup() {
    print_message "清理Docker资源..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_message "清理完成 ✓"
}

# 主菜单
show_menu() {
    echo ""
    echo -e "${BLUE}请选择操作：${NC}"
    echo "1) 快速部署 (开发环境)"
    echo "2) 生产环境部署 (包含Nginx)"
    echo "3) 查看服务状态"
    echo "4) 查看服务日志"
    echo "5) 停止服务"
    echo "6) 清理资源"
    echo "7) 重新构建"
    echo "8) 退出"
    echo ""
}

# 快速部署
quick_deploy() {
    print_header
    check_dependencies
    create_directories
    init_environment
    build_images
    start_services
    wait_for_services
    init_admin
    show_status
}

# 生产环境部署
production_deploy() {
    print_header
    check_dependencies
    create_directories
    init_environment
    build_images
    
    print_message "启动生产环境服务..."
    docker-compose --profile production up -d
    
    wait_for_services
    init_admin
    show_status
    
    print_message "生产环境部署完成！"
    print_message "HTTPS访问: https://localhost (需要SSL证书)"
}

# 主程序
main() {
    if [ $# -eq 0 ]; then
        # 交互模式
        while true; do
            show_menu
            read -p "请输入选项 (1-8): " choice
            
            case $choice in
                1) quick_deploy ;;
                2) production_deploy ;;
                3) show_status ;;
                4) show_logs ;;
                5) stop_services ;;
                6) cleanup ;;
                7) 
                    print_message "重新构建镜像..."
                    docker-compose build --no-cache
                    start_services
                    wait_for_services
                    show_status
                    ;;
                8) 
                    print_message "退出"
                    exit 0
                    ;;
                *) 
                    print_error "无效选项，请重新选择"
                    ;;
            esac
            
            echo ""
            read -p "按回车键继续..."
        done
    else
        # 命令行模式
        case $1 in
            "deploy"|"start") quick_deploy ;;
            "production") production_deploy ;;
            "stop") stop_services ;;
            "logs") show_logs ;;
            "status") show_status ;;
            "cleanup") cleanup ;;
            "rebuild") 
                docker-compose build --no-cache
                start_services
                wait_for_services
                show_status
                ;;
            *) 
                echo "用法: $0 [deploy|production|stop|logs|status|cleanup|rebuild]"
                exit 1
                ;;
        esac
    fi
}

# 捕获中断信号
trap 'print_warning "操作被中断"; exit 1' INT TERM

# 运行主程序
main "$@"
