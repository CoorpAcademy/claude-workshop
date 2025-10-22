#!/bin/bash

# Script to set up .env files from .env.sample
# Run from project root: ./.claude/scripts/copy_dot_env.sh
#
# This script creates:
# 1. app/server/.env (REQUIRED for the FastAPI application)
# 2. .env in root (OPTIONAL for Claude Code workshop features)

echo "🔧 Environment Setup for Natural Language MongoDB Query Interface"
echo ""

# ========================================
# Step 1: Set up app/server/.env (REQUIRED)
# ========================================

echo "📦 Step 1: Setting up application configuration (app/server/.env)"
echo ""

# Check if .env.sample exists
if [ ! -f "app/server/.env.sample" ]; then
    echo "❌ Error: app/server/.env.sample does not exist"
    exit 1
fi

# Check if .env already exists
if [ -f "app/server/.env" ]; then
    echo "⚠️  app/server/.env already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ Keeping existing app/server/.env file"
    else
        cp app/server/.env.sample app/server/.env
        echo "✅ Successfully created app/server/.env from .env.sample"
    fi
else
    cp app/server/.env.sample app/server/.env
    echo "✅ Successfully created app/server/.env from .env.sample"
fi

echo ""
echo "⚠️  REQUIRED: Edit app/server/.env and add your ANTHROPIC_API_KEY"
echo "   Get your key at: https://console.anthropic.com/"
echo ""

# ========================================
# Step 2: Optionally set up root .env (OPTIONAL)
# ========================================

echo "📦 Step 2: Workshop features configuration (optional)"
echo ""
echo "The root .env file is needed for Claude Code workshop features:"
echo "  - Claude Code hooks and automation"
echo "  - MCP server integrations (MongoDB MCP, Firecrawl)"
echo "  - Background agent execution (E2B)"
echo ""
echo "Skip this if you only want to run the application."
echo ""

read -p "Do you want to set up workshop features? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -f ".env.sample" ]; then
        echo "❌ Error: .env.sample does not exist in project root"
        exit 1
    fi

    if [ -f ".env" ]; then
        echo "⚠️  .env already exists in project root"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "✅ Keeping existing .env file"
        else
            cp .env.sample .env
            echo "✅ Successfully created .env from .env.sample"
            echo ""
            echo "⚠️  OPTIONAL: Edit .env and add workshop API keys"
            echo "   See .env.sample for available options"
        fi
    else
        cp .env.sample .env
        echo "✅ Successfully created .env from .env.sample"
        echo ""
        echo "⚠️  OPTIONAL: Edit .env and add workshop API keys"
        echo "   See .env.sample for available options"
    fi
else
    echo "⏭️  Skipping workshop features setup"
    echo "   You can set this up later with: cp .env.sample .env"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit app/server/.env and add your ANTHROPIC_API_KEY"
echo "  2. Start MongoDB: ./scripts/start_mongodb.sh"
echo "  3. Install dependencies (see README.md)"
echo "  4. Run the app: ./scripts/start.sh"
echo ""
echo "For more info, see README.md 'Environment Configuration' section"
echo "════════════════════════════════════════════════════════════"