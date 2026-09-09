# 引文清单与地理统计

这份清单用于维护和核查，不进入主页、站内搜索、导航或部署目录。仓库本身是公开的，因此这里的文件仍可通过 GitHub 查看；它不是需要登录的私有后台。

## 查看清单

- [逐篇清单（可直接阅读）](current/citation-ledger.md)：施引文献、年份、DOI、被引论文、作者单位和地域。
- [逐篇清单 CSV](current/citation-ledger.csv)：一篇施引记录一行，按年份从新到旧排列。
- [作者与单位 CSV](current/author-affiliations.csv)：一篇文献 × 一位作者 × 一个单位一行，保留原始单位文字、机构标识、国家或地区、州／省、城市、坐标与定位依据。
- [引用关系 CSV](current/citation-edges.csv)：一条“施引文献 → 被引论文”关系一行，同一施引文献引用多篇目标论文时分别记录。
- [逐篇被引论文覆盖率](current/coverage-by-publication.csv)：并列列出 Scholar 显示计数、OpenAlex 逐条返回数与合并检索数。
- [运行与覆盖记录](current/manifest.json)：来源、时间、分页完整性、计数口径和限制。

对应 JSON 保留结构化元数据。`cache/` 保存本次取得的 API 响应与请求地址；`sources/` 保存 Scholar 核验、论文范围核验、地理补全及待解决单位的证据。

## 本次快照：2026-09-09

| 项目 | 数量 |
|---|---:|
| 已确认的被引论文 | 15 |
| 检索到的引用关系 | 60 |
| 去重施引记录 | 55 |
| 其中：直接自引论文 | 3 |
| 其中：非研究目录记录 | 1 |
| 外部施引论文 | 51 |
| 至少有一个已定位单位的外部施引论文 | 50 |
| 全部单位尚无法定位的外部施引论文 | 1 |
| 已定位但仍有部分单位未解决的外部施引论文 | 3 |
| 州／省及同等层级地区 | 44 |
| 地图中机构 | 77 |
| 作者—单位记录行数 | 287 |

15 篇被引论文包括 Scholar 当前列出的 14 篇，以及 1 篇通过出版方存入 Crossref 的 ORCID、作者及单位信息交叉核验的补充论文。未将 OpenAlex 作者档案中的所有同名记录直接纳入。

OpenAlex 各目标论文的引用查询均已取完游标分页，共返回 59 条关系。Scholar 本次可访问的逐条结果有 8 条，其中 7 条已存在，新增 1 条。合并后共 60 条关系。OpenAlex 的一条关系来自 `Table of Contents`，清单保留并标记 `is_non_research_record=true`，地图与施引论文计数排除它。

**不能把这份清单称为 Scholar 全部 66 条引用的完整枚举。** Scholar 主页显示 66，但 9 个有计数的引用结果页面本次仅返回 8 条逐条记录，其中 3 页直接显示没有找到施引文章，页面没有下一页链接。独立核对了结果块数量与解析结果，未发现漏读页面内记录。仅针对同一组 14 篇 Scholar 论文，本清单合并检索到 56 条关系，与显示计数相差 10；无法仅凭这个差额确定额外论文的身份，也不能将不同数据库的计数直接相加。详情见 `sources/scholar-resolved.json` 的 `parser_audit`。

## 地图的统计与定位口径

1. 地图按外部施引论文去重。一篇论文在同一州／省或同一机构内只计一次；跨多个地区的论文会分别出现，因此各地计数之和可大于论文总数。后台另保留地区分数计数，每篇已定位论文在其各地区平均分配，总和等于已定位论文数。
2. 直接自引的定义是：施引作者中出现主页作者的已确认 OpenAlex ID 或 ORCID。仅有合作者重合的论文另行标记，不自动排除。
3. 单位来自施引论文自己的作者署名元数据，而非作者当前任职单位。原始 `raw_affiliation_strings` 与原始机构映射保留在作者单位清单中。
4. 坐标来自 OpenAlex 机构地理数据，可能代表机构主校区或所在城市，不代表经过核验的每位作者办公地点。州／省聚合点放在该地区施引篇数最多的已定位机构处，不使用国家首都代填。
5. 缺失州／省时，对机构已有坐标与 Natural Earth v5.1.2 原始行政区多边形进行空间匹配。原始坐标与区域记录、边界版本和 SHA-256 保留。少数旧地区名称、不同层级或海岸线匹配失败的情况，使用政府来源的明确修订，并记录在 `sources/region-overrides.json`。香港只展示相应地区层级，不用城市代表点推断作者所在区。
6. 州／省、省级直辖市、州级地区和同等一级区域统一用于聚合。Natural Earth 边界作为制图参考；少数国家的细分层级有所不同，详见边界来源说明。
7. 作者署名中与大学共同出现的教育部实体可能表示实验室主管／资助单位。这类记录保留原文，但避免将其总部位置计作第二个作者工作地点；本快照有 3 行按此规则排除。

## 尚未确定的信息

一篇 CFD 论文的六位作者在可取得的 OpenAlex、Crossref 与出版方公开元数据中均未报告单位，保留缺失状态。另有一条大学英文名称在原文中存在疑似错误，虽有同名作者的跨源候选证据，仍未静默替换。两家公司的原始单位地址包含城市，但机构标识尚未解析；文字保留在清单中，不添加未经核实的机构点。

API 本次未返回 `is_authors_truncated`，因此使用 `null` 表示未知。`geography_complete` 仅指已返回作者记录的单位定位情况，不等于已独立证实作者名单完整。任何缺失或候选纠正均见 `sources/affiliation-supplements.json`。

## 更新

在仓库根目录运行：

```bash
python3 scripts/update_citations.py
quarto render
```

仅从已保存响应重建：

```bash
python3 scripts/update_citations.py --offline
```

脚本不需要访问计算服务器。在线模式刷新 OpenAlex；Scholar 数据是经过逐条匹配的带日期快照，更新时需重新核验并替换 `sources/scholar-*.json`。新增机构若需要空间匹配，脚本会下载固定版本的原始 Natural Earth 数据，也可通过 `--admin1-polygons` 指定该原始文件。凭据仅从环境读取，不保存到文件。

来源与方法：[OpenAlex citations](https://help.openalex.org/data/works/citations/)、[OpenAlex institutions](https://help.openalex.org/data/institutions/)、[Natural Earth admin-1](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)。地图仅加载聚合地理 JSON，不加载逐篇引文或作者名单。
