# V1.0 核心闭环接口试跑说明

`demo_flow.http` 用于在 VS Code REST Client、JetBrains HTTP Client 或类似工具里手动试跑 MVP 闭环。

## 试跑顺序

1. 启动服务：

```bash
uvicorn app.main:app --reload
```

2. 执行 `demo_flow.http` 的第 1 个请求，创建机构。

3. 从返回结果中复制 `id`，替换所有 `{{organization_id}}`。

4. 执行第 2 个请求，创建素材。

5. 从返回结果中复制 `id`，替换 `{{material_id}}`。

6. 执行第 3 个请求，完成素材拆解。

7. 执行第 4 个请求，生成选题。

8. 从返回的选题中复制一个 `id`，替换 `{{topic_id}}`。

9. 执行第 5 个请求，生成内容任务并自动合规审核。

10. 可单独执行第 6 个请求，测试合规规则。

## 当前限制

- 当前 Agent 是规则占位实现，后续会替换为真实模型调用。
- 当前素材检索是简单标签逻辑，后续接 pgvector 语义检索。
- 当前登录鉴权暂未实现，接口以 MVP 骨架为主。

