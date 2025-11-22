# GET `/cities`

- 入口：`code/hospital_scanner/main.py:323`
- 数据访问：`db.get_cities`。
- 作用：分页返回城市列表，可按 `province_id` 过滤。

## 执行流程
1. 接收可选 `province_id` 与 `page/page_size`。
2. `db.get_cities` 校正分页参数，按是否传入省份 ID 选择对应 count 与查询 SQL。
3. 返回 `PaginatedResponse`（含 has_next/has_prev）。

## 设计原因
- 为分级浏览提供城市层级数据。

## 优点
- 分页与总数内置，参数绑定避免 SQL 注入。

## 缺点与风险
- 同步 sqlite 查询阻塞事件循环。
- 无排序/模糊搜索；省份 ID 无效时仅返回空列表。
- 上游刷新未写库，通常为空。

## 改进建议
- DB 访问放线程池或使用异步驱动。
- 增加排序/过滤/搜索选项，空结果时提供“未初始化”提示。
