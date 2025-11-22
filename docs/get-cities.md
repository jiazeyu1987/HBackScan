# GET `/cities`

- 入口：`code/hospital_scanner/main.py:323`
- 数据访问：`db.get_cities`。
- 作用：分页返回城市列表，可按 `province_id` 过滤。

## 执行流程
1. 接收可选 `province_id` 以及 `page/page_size`。
2. `db.get_cities` 校正分页参数，若提供省份则先 count 再分页查询对应城市，否则查询全部。
3. 返回 `PaginatedResponse`，包含 `has_next/has_prev`。

## 设计原因
- 为分级浏览提供城市层级数据，支持按省份过滤。

## 优点
- 分页与总数计算内置，前端易用。
- SQL 使用参数绑定，避免注入。

## 缺点与风险
- 同步 sqlite 访问阻塞事件循环，无法支撑高并发。
- 无排序自定义、无模糊搜索。
- 当上游 `/refresh` 未落库或 `province_id` 无效时返回空列表且未提示。

## 改进建议
- 使用线程池/异步驱动访问数据库。
- 增加排序与过滤选项（按名称、更新时间、医院数量等）。
- 返回明确的“未找到/未初始化”提示或 404，以改善前端体验。
