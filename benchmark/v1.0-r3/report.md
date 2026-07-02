# Text2SQL V1.0 Benchmark Report

- Generated at: `2026-07-02T17:46:28`
- Total runs: `30`
- Pass rate: `46.67%`
- Executable rate: `46.67%`
- Average score: `0.8133`
- Average generate seconds: `13.407`
- P95 generate seconds: `25.074`
- Average execute seconds: `0.233`
- P95 execute seconds: `0.979`
- Average estimated total tokens: `2961.8`

## Seed Data

- `mobile_communities`: 黄岐白沙村(80313), （城中村）江夏村(78924), 广东南方职业学院（睦州校区）(72777), （城中村）长红村(69084), 广州存丰纺织品有限公司(65337)
- `broadband_markets`: 广东培正学院(485131), 广州南方学院(326148), 广东科技学院（松山湖校区）(296934), 广东南方职业学院（睦州校区）(243772), 广东医科大学+东莞校区(240852)
- `mobile_cities`: 广州市(20540010), 深圳市(15157494), 佛山市(13215416), 东莞市(9919078), 中山市(6255736)
- `broadband_cities`: 广州市(36900668), 深圳市(25805387), 佛山市(16164340), 东莞市(16100301), 中山市(10920133)

## Cases

- `mobile_count_by_community` [aggregate]: 黄岐白沙村 有多少移网用户？
- `mobile_list_by_community` [detail]: 列出 （城中村）江夏村 的移网用户号码，最多100条
- `broadband_count_by_market` [aggregate]: 广东培正学院 有多少宽带用户？
- `broadband_list_by_market` [detail]: 列出 广州南方学院 的宽带账号和联系电话，最多100条
- `mixed_mobile_broadband_community` [mixed]: 汇景新城 有哪些移网用户和宽带用户？
- `mobile_top_communities` [ranking]: 移网用户数最多的10个小区是哪些？
- `broadband_top_markets` [ranking]: 宽带用户数最多的10个小区或市场是哪些？
- `mobile_city_count` [aggregate]: 广州市 的移网用户数量是多少？
- `broadband_city_count` [aggregate]: 广州市 的宽带用户数量是多少？
- `mixed_city_compare` [mixed]: 对比 广州市 的移网用户和宽带用户数量

## Failed Runs

- `mobile_count_by_community` run 1: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `broadband_count_by_market` run 1: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mobile_top_communities` run 1: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mobile_city_count` run 1: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `broadband_city_count` run 1: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mixed_city_compare` run 1: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `broadband_count_by_market` run 2: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `broadband_list_by_market` run 2: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mobile_city_count` run 2: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `broadband_city_count` run 2: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mixed_city_compare` run 2: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `broadband_count_by_market` run 3: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mobile_top_communities` run 3: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mobile_city_count` run 3: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `broadband_city_count` run 3: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
- `mixed_city_compare` run 3: score=0.65, generate_error=None, execute_error=HTTP 400 from http://127.0.0.1:38000/api/v1/ask/execute-sql: {"detail":"Client error '400 Bad Request' for url 'http://100.65.5.66:9023/?database=chatbi'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"}
