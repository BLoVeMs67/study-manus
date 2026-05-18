# 规划Agent系统预设prompt
PLANNER_SYSTEM_PROMPT = ""

# 创建Plan规划提示词模板，内部有message+attachments占位符
CREATE_PLANNER_PROMPT = "{message}\n{attachments}"

# 更新Plan规划提示词模板，内部有plan和step占位符
UPDATE_PLANNER_PROMPT = "{plan}\n{step}"
