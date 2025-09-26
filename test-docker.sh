#!/bin/bash

# MedGemma AI 智能诊疗助手 - Docker 部署测试脚本

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
    echo -e "${BLUE}  MedGemma Docker 部署测试${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 测试Docker环境
test_docker_env() {
    print_message "测试Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行"
        return 1
    fi
    
    print_message "Docker环境检查通过 ✓"
    return 0
}

# 测试配置文件
test_config_files() {
    print_message "检查配置文件..."
    
    local files=("Dockerfile" "docker-compose.yml" ".dockerignore" "docker-start.sh" "nginx.conf")
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "配置文件缺失: $file"
            return 1
        fi
        print_message "✓ $file"
    done
    
    print_message "配置文件检查通过 ✓"
    return 0
}

# 测试Docker Compose配置
test_compose_config() {
    print_message "验证Docker Compose配置..."
    
    if docker-compose config &> /dev/null; then
        print_message "Docker Compose配置验证通过 ✓"
        return 0
    else
        print_error "Docker Compose配置验证失败"
        return 1
    fi
}

# 测试构建镜像
test_build_image() {
    print_message "测试构建Docker镜像..."
    
    if docker-compose build --no-cache &> /dev/null; then
        print_message "Docker镜像构建成功 ✓"
        return 0
    else
        print_error "Docker镜像构建失败"
        return 1
    fi
}

# 测试启动服务
test_start_services() {
    print_message "测试启动服务..."
    
    # 清理可能存在的容器
    docker-compose down 2>/dev/null || true
    
    # 启动服务
    if docker-compose up -d &> /dev/null; then
        print_message "服务启动成功 ✓"
        
        # 等待服务就绪
        sleep 10
        
        # 检查服务状态
        if docker-compose ps | grep -q "Up"; then
            print_message "服务运行状态检查通过 ✓"
            return 0
        else
            print_error "服务未正常运行"
            return 1
        fi
    else
        print_error "服务启动失败"
        return 1
    fi
}

# 测试健康检查
test_health_check() {
    print_message "测试健康检查..."
    
    # 等待服务完全启动
    sleep 15
    
    # 测试应用健康检查
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_message "应用健康检查通过 ✓"
        return 0
    else
        print_error "应用健康检查失败"
        return 1
    fi
}

# 测试API接口
test_api_endpoints() {
    print_message "测试API接口..."
    
    local endpoints=("/health" "/api/users/register" "/docs")
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f "http://localhost:8000$endpoint" &> /dev/null; then
            print_message "✓ $endpoint"
        else
            print_warning "⚠ $endpoint (可能正常，取决于具体实现)"
        fi
    done
    
    print_message "API接口测试完成 ✓"
    return 0
}

# 清理测试环境
cleanup_test() {
    print_message "清理测试环境..."
    docker-compose down -v &> /dev/null || true
    print_message "测试环境清理完成 ✓"
}

# 显示测试结果
show_test_results() {
    local passed=$1
    local total=$2
    
    echo ""
    print_header
    echo -e "测试结果: ${GREEN}$passed${NC}/${total} 通过"
    
    if [ $passed -eq $total ]; then
        print_message "🎉 所有测试通过！Docker部署配置正确。"
        echo ""
        print_message "下一步操作："
        echo "1. 运行 ./docker-start.sh 启动完整服务"
        echo "2. 访问 http://localhost:8000/ui/ 使用系统"
        echo "3. 查看 ./DOCKER_DEPLOYMENT.md 获取详细部署指南"
    else
        print_error "❌ 部分测试失败，请检查配置"
    fi
}

# 主测试函数
run_tests() {
    local passed=0
    local total=6
    
    print_header
    
    # 测试1: Docker环境
    if test_docker_env; then
        ((passed++))
    fi
    
    # 测试2: 配置文件
    if test_config_files; then
        ((passed++))
    fi
    
    # 测试3: Docker Compose配置
    if test_compose_config; then
        ((passed++))
    fi
    
    # 测试4: 构建镜像
    if test_build_image; then
        ((passed++))
    fi
    
    # 测试5: 启动服务
    if test_start_services; then
        ((passed++))
    fi
    
    # 测试6: 健康检查
    if test_health_check; then
        ((passed++))
    fi
    
    # 额外测试: API接口
    test_api_endpoints
    
    # 清理测试环境
    cleanup_test
    
    # 显示结果
    show_test_results $passed $total
    
    return $((total - passed))
}

# 主程序
main() {
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "用法: $0 [--help]"
        echo ""
        echo "MedGemma AI 智能诊疗助手 - Docker 部署测试脚本"
        echo ""
        echo "选项:"
        echo "  --help, -h    显示此帮助信息"
        echo ""
        echo "此脚本将测试以下内容："
        echo "1. Docker环境检查"
        echo "2. 配置文件验证"
        echo "3. Docker Compose配置验证"
        echo "4. 镜像构建测试"
        echo "5. 服务启动测试"
        echo "6. 健康检查测试"
        echo "7. API接口测试"
        exit 0
    fi
    
    # 运行测试
    run_tests
    exit $?
}

# 捕获中断信号
trap 'print_warning "测试被中断"; cleanup_test; exit 1' INT TERM

# 运行主程序
main "$@"
