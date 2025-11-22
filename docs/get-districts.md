# GET `/districts`

- 入口：`code/hospital_scanner/main.py:346`
- 数据访问：`db.get_districts`。
- 作用：分页返回区县列表，可按 `city_id` 过滤。

## 执行流程
1. 接收可选 `city_id` 与 `page/page_size`。
2. `db.get_districts` 校正分页参数，按是否传入城市 ID 选择对应 count 与查询 SQL。
3. 返回 `PaginatedResponse`。

## 设计原因
- 支撑逐级下钻的行政区浏览，并为医院列表提供上游维度。

## 优点
- 参数绑定避免 SQL 注入。
- 提供基本的分页元数据。

## 缺点与风险
- 同步 sqlite 查询阻塞事件循环。
- 未提供排序/模糊搜索，且缺少输入校验（如 city_id 是否存在）。
- 当前上游刷新未写库，接口通常返回空，缺少可观测提示。

## 改进建议
- 迁移到异步/线程池数据库访问。
- 增加排序与过滤选项，返回更明确的空结果原因。
- 在数据层实现 upsert 与约束校验，避免脏数据。
