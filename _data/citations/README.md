# 引文清单与地理统计

这份清单用于维护和核查，不进入主页、站内搜索、导航或部署目录。仓库本身是公开的，因此这里的文件仍可通过 GitHub 查看；它不是需要登录的私有后台。

## 查看清单

- [Scholar 66 条原始记录](current/scholar-citations.csv)：与主页显示计数逐项对应，保留重复版本标记、作者单位、地域和结果页来源。

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
| 检索到的引用关系 | 69 |
| 去重施引记录 | 64 |
| 其中：直接自引论文 | 4 |
| 其中：非研究目录记录 | 1 |
| 外部施引论文 | 59 |
| 至少有一个已定位单位的外部施引论文 | 59 |
| 全部单位尚无法定位的外部施引论文 | 0 |
| 已定位但仍有部分单位未解决的外部施引论文 | 3 |
| 州／省及同等层级地区 | 49 |
| 地图中机构 | 89 |
| 作者—单位记录行数 | 323 |

15 篇被引论文包括 Scholar 当前列出的 14 篇，以及 1 篇通过出版方存入 Crossref 的 ORCID、作者及单位信息交叉核验的补充论文。未将 OpenAlex 作者档案中的所有同名记录直接纳入。

**Scholar 主页显示的 66 条记录已全部逐页取得并核对。** 本次实际浏览器访问了 9 篇有引用论文的全部 12 个结果页面，各目标的返回条数为 13、12、11、8、8、6、5、2、1，合计 66。每条记录均已匹配到确定的文献；可在 `current/scholar-citations.csv` 中逐行查看。

其中两组是同一文献在不同网站的版本：供应链预测论文的 Elsevier／ACM 版本，以及电动车速度预测论文的 IEEE／Academia 版本。两组均核对到同一 DOI，原始 66 行继续保留并标记 `duplicate_of_result_id`。按“施引文献 × 被引论文”去重后为 **64 条关系、60 篇不同施引文献**。同一施引文献引用多篇目标论文时，仍保留多条引用关系。

OpenAlex 的 15 个目标查询均已取完游标分页，返回 59 条关系。与完整 Scholar 结果合并后，共 **69 条关系、64 篇去重施引记录**。它比 Scholar 单独集合更大，是因为同时保留了补充被引论文的引文和其他索引中的额外记录，而不是把两个数据库的总数相加。OpenAlex 中一条 `Table of Contents` 记录仍保留并标记为非研究记录，地图将其排除。

早先非浏览器请求曾返回不完整页面；重新通过实际浏览器读取并逐页核对后已解决。此前关于“无法枚举 66 条”的判断已撤销，不能据早先的响应推断 Scholar 本身缺少这些记录。

## 地图的统计与定位口径

1. 地图按外部施引论文去重。一篇论文在同一州／省或同一机构内只计一次；跨多个地区的论文会分别出现，因此各地计数之和可大于论文总数。后台另保留地区分数计数，每篇已定位论文在其各地区平均分配，总和等于已定位论文数。
2. 直接自引的定义是：施引作者中出现主页作者的已确认 OpenAlex ID 或 ORCID。仅有合作者重合的论文另行标记，不自动排除。
3. 单位来自施引论文自己的作者署名元数据，而非作者当前任职单位。原始 `raw_affiliation_strings` 与机构映射保留在作者单位清单中。经出版方补全的记录另标 `affiliation_source`；补全前的 API 作者记录保留在 `authorships_original`。
4. 坐标主要来自 OpenAlex 机构地理数据，另有一个公司点采用 GeoNames 的已确认城市代表点，可能代表机构主校区或所在城市，不代表经过核验的每位作者办公地点。州／省聚合点放在该地区施引篇数最多的已定位机构处，不使用国家首都代填。
5. 缺失州／省时，对机构已有坐标与 Natural Earth v5.1.2 原始行政区多边形进行空间匹配。原始坐标与区域记录、边界版本和 SHA-256 保留。少数旧地区名称、不同层级或海岸线匹配失败的情况，使用政府来源的明确修订，并记录在 `sources/region-overrides.json`。香港只展示相应地区层级，不用城市代表点推断作者所在区。
6. 州／省、省级直辖市、州级地区和同等一级区域统一用于聚合。Natural Earth 边界作为制图参考；少数国家的细分层级有所不同，详见边界来源说明。
7. 作者署名中与大学共同出现的教育部实体可能表示实验室主管／资助单位。这类记录保留原文，但避免将其总部位置计作第二个作者工作地点；本快照有 3 行按此规则排除。

## 尚未确定的信息

CFD 论文六位作者的原文署名现已通过出版方页面“Show more”完整核实：前四位作者为重庆理工大学，另两位分别为湖北三峡实验室与 Hubei Sinophorus Electronic Materials Co., Ltd.。原文省市与公司自身地址完成交叉核验，公司点使用 GeoNames 的宜昌城市代表点，明确不是公司场址。

目前三篇已定位论文仍有部分单位未解析：一条大学英文名称在原文中存在疑似错误，保留候选证据而不静默替换；另外两家公司的原始地址包含城市，但尚未确认机构标识。原始单位文字均保留。对于无 OpenAlex 记录的中文综述和 IFIP 会议论文，作者与单位直接来自出版社 PDF，使用明确的本地标识，未编造 DOI 或 OpenAlex ID。

OpenAlex API 本次未返回 `is_authors_truncated`，相应值使用 `null` 表示未知；从出版社 PDF 完整核验的作者名单另标来源。`geography_complete` 仅指已返回作者记录的单位定位情况，不等于已独立证实作者名单完整。任何缺失或候选纠正均见 `sources/affiliation-supplements.json`。

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

来源与方法：[OpenAlex citations](https://help.openalex.org/data/works/citations/)、[OpenAlex institutions](https://help.openalex.org/data/institutions/)、[Natural Earth admin-1](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)、[GeoNames](https://www.geonames.org/)（[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)）。地图仅加载聚合地理 JSON，不加载逐篇引文或作者名单。
