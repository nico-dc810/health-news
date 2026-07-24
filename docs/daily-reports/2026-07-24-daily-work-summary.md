# 2026-07-24 Daily Work Summary

## 上线清单

- 今日上线：20 条。
- 重点分类：监管与产品安全 6 条、直销与营养产业动态 5 条、科研与消费者健康素材 8 条、社交线索复核 1 条。
- 消费者日常健康素材：CDC 运动、CDC 睡眠、WHO 健康饮食、NIH ODS 镁、Mayo Clinic 体重管理、PubMed 抗阻训练、PubMed 女性健康、Harvard Health 压力管理，共 8 条。

## 搜索的网站、频道与类别

- 官方监管：FDA recalls and safety alerts、FDA foodborne illness outbreaks、FTC press releases、SAMR、NMPA、CDE。
- 行业媒体：Direct Selling News、NutraIngredients。
- 医学机构与公共卫生：CDC、WHO、NIH ODS、Mayo Clinic、Harvard Health Publishing。
- 正式出版物与科研检索：PubMed 系统综述和主题检索。
- 白名单社交线索：X、YouTube、公众号、知乎仅作为问题发现，未直接作为事实来源；上线事实均回到 T1/T2 或正式出版物。

## 自媒体二创推荐

1. 买补充剂为什么要看批号，而不只看成分表。
2. 成年人每周 150 分钟运动，怎么拆到工作日。
3. 镁不是通用助眠片，补之前先看这三件事。
4. 围绝经期不是突然变老，而是一组需要管理的变化。
5. GLP-1 之后，普通体重管理项目还能靠什么留住用户。

## 被剔除或待复核内容

- 未采用低质招商软文、收入排行和个人成功故事类线索。
- 未直接采用 X、YouTube、公众号、知乎中的健康热点表达，只保留经 NIH、CDC、PubMed 等验证后的问题方向。
- Direct Selling News 部分单篇文章可能存在访问限制，今天以站点新闻入口作为行业观察源，并在合规说明中降低为行业媒体证据层级。
- 未采用没有精确主体、批号、监管状态或原始页面的转载型召回内容。

## 链接检查和质量检查

- 已生成 `static/data/latest.json`、`static/data/daily/2026-07-24.json`、`static/data/daily/index.json`。
- JSON 解析通过；SOP 质量门禁结果为 20 final、0 rejected、0 filtered；中文可读性检查通过，未发现替换字符或异常问号比例。
- 链接抽检已生成 `docs/daily-reports/2026-07-24-link-check.txt`。FTC、SAMR、CDE、NutraIngredients、WHO、Harvard Health 本地返回 200；NMPA 返回 412；CDC、NIH ODS、PubMed、Mayo Clinic、Direct Selling News 返回 403；FDA 路径本地返回 404，已记录为需明日复核的官方站点路径问题。
- 发布记录：`gh-pages` 已推送提交 `daba29a`。GitHub Pages 默认域名本机请求仍连接重置；改用 GitHub raw 的 `gh-pages` 分支文件验收，`data/latest.json`、`data/daily/2026-07-24.json`、`data/daily/index.json` 均确认日期为 2026-07-24、条数为 20、中文可读。
- 明日关注：FDA 召回扩展、FTC 健康广告退款后续、CDE/NMPA 注册与公示更新、体重管理服务在 GLP-1 语境下的合规话术。
