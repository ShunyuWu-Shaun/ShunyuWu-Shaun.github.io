# 2026-09-24 引文更新

Google Scholar 从 66 条增至 70 条。实际浏览器重新检查了 9 篇被引论文的全部 12 个分页，原 66 条均仍存在，新增 4 篇文献、4 条引用关系。总量与逐篇被引计数相符；原有两组重复版本保留并继续标记。

## 新增文献与署名单位

| 施引文献 | 作者单位（按出版方署名） | 地域 |
|---|---|---|
| [Hierarchical reinforcement learning for safe output tracking…](https://doi.org/10.1007/s00521-026-12456-7) | Center for Research and Advanced Studies (CINVESTAV), Ramos Arizpe | Coahuila, Mexico |
| [Event-Triggered Self-Learning Parallel Tracking Control…](https://doi.org/10.1109/TCYB.2026.3725996) | Macau University of Science and Technology; Institute of Automation, Chinese Academy of Sciences; University of Chinese Academy of Sciences; Shenyang University of Technology | Macau; Beijing; Liaoning |
| [Energy Management of AI Data Center Microgrids…](https://doi.org/10.1109/TICPS.2026.3733880) | Shanghai Jiao Tong University; KTH Royal Institute of Technology; State Grid Jiangsu Electric Power | Shanghai; Stockholm; Jiangsu |
| [Bridging Representation Learning and Optimal Control…](https://doi.org/10.1109/TTE.2026.3734226) | Beijing Institute of Technology | Beijing |

每位作者的原始署名、单位映射、地域来源见 `../../current/author-affiliations.csv` 和 `../publisher-affiliation-updates.json`。三篇 IEEE 论文的作者页与 DOI 已逐一核对；Springer 论文的作者、署名和参考文献 18 均由出版方页面核实。FCEV 论文尚无 OpenAlex DOI 记录，使用出版方文献号 `IEEE11693968` 和 Crossref 元数据，不编造索引 ID。

## 本次地理修订

- CINVESTAV 原始索引给出 Mexico City 总部坐标；论文署名位于 Ramos Arizpe, Coahuila，现使用该城市的 GeoNames 代表点。
- 北京建龙、宁波水务、杭氧的旧索引匹配分别误指太原重工、宁夏水利、浙江能源，现按论文原始单位文字和城市修正。
- Unidata 与 CMB Network Technology (Hangzhou) 的署名城市分别为 Rome、Hangzhou，现使用明确的本地机构标识和城市代表点。
- 同一作者出现相同机构 ID 的多个别名时去重，并保留原始列表。作者单位关系按“文献 × 作者 × 机构”计数；地图仍按外部施引文献去重。

## 保存内容与边界

引文页面成员清单、四条新增原始行、出版方署名转录、Crossref 原始响应、城市定位依据及刷新后的 OpenAlex 响应均已保存。Springer 原文 PDF 已下载到本地 `../../downloads/2026-09-24/`；三篇 IEEE 原文未取得可验证的 PDF，因此保留完整出版方作者页和书目元数据，不标记为全文已下载。文件下载状态和 PDF 校验值见 `retrieval-manifest.json`。

下载的全文只用于本地阅读，不提交公开仓库，也不随主页发布。后台清单保留所有引文与数字；主页仍只展示机构及所在地。
