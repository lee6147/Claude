#!/bin/bash
# TenBuilder AI Coding Setup — macOS
# Usage: curl -sSL https://raw.githubusercontent.com/tenbuilder/tenbuilder/main/starter-kit/macos-setup.sh | bash

set -e

echo "🚀 텐빌더 AI Coding Environment Setup"
echo "==========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() { echo -e "${GREEN}[✓]${NC} $1"; }
info() { echo -e "${YELLOW}[i]${NC} $1"; }

# --- Prerequisites ---
if ! command -v brew &> /dev/null; then
    info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
step "Homebrew ready"

if ! command -v node &> /dev/null; then
    info "Installing Node.js..."
    brew install node
fi
step "Node.js $(node --version)"

# --- AI Coding Tools ---
echo ""
echo "📦 Installing AI Coding Tools..."

# Claude Code
if ! command -v claude &> /dev/null; then
    info "Installing Claude Code..."
    npm install -g @anthropic-ai/claude-code
fi
step "Claude Code installed"

# --- Git Configuration ---
echo ""
echo "⚙️  Git Configuration..."

# .gitignore_global에 .claude/ 추가
GITIGNORE_GLOBAL="${HOME}/.gitignore_global"
if [ ! -f "$GITIGNORE_GLOBAL" ]; then
    touch "$GITIGNORE_GLOBAL"
    git config --global core.excludesfile "$GITIGNORE_GLOBAL"
fi

if ! grep -q '.claude/' "$GITIGNORE_GLOBAL" 2>/dev/null; then
    echo '.claude/' >> "$GITIGNORE_GLOBAL"
    step "Added .claude/ to global gitignore"
else
    step ".claude/ already in global gitignore"
fi

# --- AI Shell Aliases ---
echo ""
echo "🔧 Shell Aliases..."

ZSHRC="${HOME}/.zshrc"
if [ -f "$ZSHRC" ] && ! grep -q '# 텐빌더 AI aliases' "$ZSHRC" 2>/dev/null; then
    cat >> "$ZSHRC" << 'ALIASES'

# 텐빌더 AI aliases
alias cc='claude'
alias ccr='claude "현재 브랜치 변경사항을 리뷰해줘"'
alias cct='claude "테스트를 실행하고 실패하면 수정해줘"'
alias ccf='claude "이 파일을 분석해줘:"'
ALIASES
    step "AI aliases added to .zshrc"
else
    step "AI aliases already configured"
fi

# --- Summary ---
echo ""
echo "==========================================="
echo "✅ Setup Complete!"
echo ""
echo "다음 단계:"
echo "  1. 새 터미널 열기 (또는 source ~/.zshrc)"
echo "  2. 프로젝트 폴더에서 'claude' 실행"
echo "  3. CLAUDE.md 설정: github.com/tenbuilder/tenbuilder/claude-code"
echo ""
echo "유용한 alias:"
echo "  cc   → claude (단축)"
echo "  ccr  → 코드 리뷰"
echo "  cct  → 테스트 실행+수정"
echo "  ccf  → 파일 분석"
echo ""
echo "📰 뉴스레터: maily.so/tenbuilder"
echo "==========================================="
