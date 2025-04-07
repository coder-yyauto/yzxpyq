#!/bin/bash
# 确保脚本以 yzxuser 身份运行，并加载 micromamba 环境

export PATH="/home/yzxuser/bin:$PATH"
eval "$(micromamba shell hook --shell bash)"

micromamba activate yzx
cd /home/yzxuser/yzxpyq/backend
exec /home/yzxuser/micromamba/envs/yzx/bin/python /home/yzxuser/yzxpyq/backend/app.py

