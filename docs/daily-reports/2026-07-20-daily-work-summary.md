# 2026-07-20 每日大健康资讯与自媒体素材更新总结

## 搜索与核验范围

- 官方监管：FDA 召回与食品安全调查、FTC 健康宣称与 MLM 指导、CFE/SAMR 特殊食品查询入口、NMPA 医疗器械 UDI、商务部直销行业管理系统、CMS 药品价格谈判政策页。
- 行业与企业：Herbalife、USANA、Nu Skin 官方投资者新闻入口，Direct Selling News 行业媒体入口。
- 医学与消费者健康：CDC 运动与睡眠资源、NIH ODS 镁事实页、Harvard Health 蛋白质科普、PubMed 中老年抗阻训练 Meta 分析。
- 社媒线索：X、YouTube、公众号、知乎只作为选题发现来源；上线条目均回到官方监管、企业官网、医学机构或正式文献页面。

## 上线清单

- 今日上线 20 条：policy 5 条、product 5 条、industry 4 条、research 2 条、consumer 4 条。
- 消费者日常健康素材 5 条，覆盖食品召回处理、运动、睡眠、补剂安全、蛋白质营养和中老年力量训练。
- 重点标签：FDA、FTC、Cyclospora、食品召回、补充剂、儿童健康、直销合规、保健食品、医疗器械、GLP-1、睡眠、运动、蛋白质。

## 自媒体二创推荐

1. 植物粉不是越天然越不用看标签：Zen Principle 辣木粉召回教你核对批次。
2. 儿童增高产品为什么最容易踩广告红线：FTC TruHeight 案复盘。
3. 补充剂不能蹭 GLP-1 写成“平替”：体重管理内容的三条边界。
4. 睡眠不好先排查 5 个生活方式因素：别把助眠产品写成治疗工具。
5. 中老年练力量，强度不是越低越安全：先看评估、动作和递进。

## 被剔除或待复核内容

- 剔除低质招商软文、无原文链接的社媒爆料、只引用达人体验的补剂内容、带有快速减重和疾病治疗暗示的素材。
- 中文监管站点中未能稳定定位到具体公告页的内容未上线；保留官方查询入口作为工具型条目。
- 行业媒体和企业新闻入口只作为监测入口；涉及财报、并购或产品效果的具体判断，明日继续等待更明确公告或可核验报道。

## 链接检查与异常

- 本地对 20 个 URL 执行可访问性检查，并记录在 `docs/daily-reports/2026-07-20-link-check.txt`。
- 预期 FDA、CDC、NIH、FTC 等站点可能因反爬或地区策略返回 403/404/超时；若浏览器可打开且来源为官方具体页面，将在检查记录中标明。
- 今日使用 UTF-8 写入 JSON，并运行内容可读性脚本检查问号、替换字符和条目数。

## 明日关注

- FDA/CDC Cyclospora 是否继续扩大涉及品牌、州别或渠道。
- FTC 是否继续发布儿童健康、补充剂评价背书、MLM 收入陈述或健康宣称案件。
- Direct Selling News 与企业 IR 是否出现 7 月下旬财报、渠道调整和健康生活方式赞助新动态。
- SAMR/NMPA/CDE 是否出现可追溯到具体页面的保健食品、化妆品、医疗器械或药审公告。

## 发布后核验补充

- gh-pages 已推送到远端提交 `b7cd651`，`git ls-remote` 确认远端 `refs/heads/gh-pages` 指向该提交。
- `raw.githubusercontent.com` 已核验 `data/latest.json`、`data/daily/2026-07-20.json`、`data/daily/index.json`：日期为 2026-07-20，条数为 20，中文可读，问号数为 0。
- `https://nico-dc810.github.io/health-news/` Pages CDN 在复查时仍返回 2026-07-19 或出现 SSL EOF，本次记录为 Pages/CDN 传播待刷新；远端分支内容已确认正确。
- `https://ai.candobear.com/data/latest.json` 当前返回 SPA HTML，不适合作为 JSON 校验地址，后续应确认自定义域静态资源路由。
