# GET `/hospitals/search`

- 入口：`code/hospital_scanner/main.py:392`
- 数据访问：`db.search_hospitals`。
- 作用：按名称模糊搜索医院。

## 执行流程
1. 接收查询参数 `q`（必填）与 `limit`（默认 20）。
2. `db.search_hospitals` 执行 `name LIKE %q%` 的参数化查询并限制条数。
3. 返回 `{query, limit, results, count}`，`results` 为原始行数据列表。

## 设计原因
- 提供简单的关键字匹配，快速定位医院记录。

## 优点
- SQL 参数绑定避免注入。
- 响应包含查询词与结果数量，前端可直接显示。

## 缺点与风险
- 仅简单 LIKE，无拼音/分词/权重排序；字段未建全文索引。
- 响应结构未复用 `PaginatedResponse`，与其他列表接口不一致。
- 同步 sqlite 查询阻塞事件循环；无防抖/速率限制，可能被滥用。
- 医院表往往为空（刷新/扫描未落库），搜索多返回空且无提示。

## 改进建议
- 引入更强的模糊匹配（FTS5、trigram 或应用层分词），并统一分页结构。
- 增加速率限制与最小查询长度，减少滥用。
- 数据为空时返回指引（先执行 `/refresh` 或 `/scan`）。
