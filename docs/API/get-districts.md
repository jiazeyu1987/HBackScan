# GET `/districts`

- 入口：`code/hospital_scanner/main.py:346`
- 数据访问：`db.get_districts`。
- 作用：分页返回区县列表，可按 `city_id` 过滤。

## 执行流程
1. 接收可选 `city_id` 与 `page/page_size`。
2. `db.get_districts` 校正分页参数，按是否传入城市 ID 选择对应 count 与查询 SQL。
3. 返回 `PaginatedResponse`。

## 设计原因
- 支撑逐级下钻行政区，并为医院列表提供上游维度。

## 优点
- 参数绑定避免 SQL 注入，提供分页元数据。

## 缺点与风险
- 同步 sqlite 查询阻塞事件循环。
- 无排序/模糊搜索，city_id 无效时默默返回空。
- 数据通常为空（刷新未落库），缺少可观测提示。

## 改进建议
- DB 访问改为异步/线程池；增加排序与过滤。
- 空结果时返回更明确的提示，或提供数据更新时间。
