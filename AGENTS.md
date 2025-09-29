# 项目介绍

PromptWorks 是一个聚焦 Prompt 资产管理与大模型运营的全栈解决方案，仓库内包含 FastAPI 后端与 Vue + Element Plus 前端。平台支持 Prompt 全生命周期管理、模型配置、版本对比与评估实验，为团队提供统一的提示词协作与测试工作台。

# 开发规范

1. 本项目后端是python+fastapi开发，使用uv管理环境，使用poe配置任务，使用pytest测试
2. 后端开发完成后需要写对应的测试用例，并且通过uv run poe test-all测试
3. 项目前端使用Vue3+Element Plus开发，代码在./frontend中
4. 后端的api文件夹内文件仅实现接口定义、类型定义与检测、对应业务逻辑函数调用，具体业务逻辑写在services文件夹中
5. 每次开发任务完成并测试无误之后，将代码commit到本地git中（禁止：上传到云端和合并到dev或main），需要有简短的中文提交信息