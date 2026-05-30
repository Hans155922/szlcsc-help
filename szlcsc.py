import math
import time
import requests
from decimal import Decimal, ROUND_HALF_UP

PAGE_SIZE = 30


def D(x):
    # 安全转 Decimal，避免 float 精度问题
    return Decimal(str(x))


def round_money(x):
    # 按官方金额规则四舍五入到 2 位小数。
    return D(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_to_int(x):
    # 元转分
    return int(round_money(x) * 100)


def int_to_money(x):
    return Decimal(x) / Decimal(100)


def fmt_money(x):
    return f"{Decimal(x):.2f}"


def get_first_price(product_vo):
    # 取商品第一个价格档，用于判断是否已经超过价格范围
    price_list = product_vo.get("productPriceList") or []
    if not price_list:
        return None

    ratio = product_vo.get("convesionRatio", 1) or 1
    return D(price_list[0].get("productPrice", 0)) * D(ratio)


def get_all(brandIdFilter, maxprice):
    res = []
    session = requests.Session()
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) " "AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/125.0.0.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://list.szlcsc.com/",
        "Origin": "https://list.szlcsc.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    session.headers.update(headers)
    base_url = "https://list.szlcsc.com/brand/product"

    def fetch_page(page):
        params = {
            "currentPage": page,
            "pageSize": PAGE_SIZE,
            "catalogIdFilter": "",
            "brandIdFilter": brandIdFilter,
            "standardFilter": "",
            "brandPlaceFilter": "",
            "labelFilter": "",
            "arrangeFilter": "",
            "smtLabelFilter": "",
            "spotFilter": 0,
            "discountFilter": 1,
            "startPrice": "",
            "endPrice": "",
            "sortNumber": 1,
            "queryParameterValue": "",
            "lastParamName": "",
            "keyword": "",
            "secondKeyword": "",
            "hasDataFile": "false",
            "demandNumber": "",
            "satisfyStockType": "",
        }

        response = session.get(base_url, params=params, timeout=15)
        if response.status_code != 200:
            print("请求失败")
            print("状态码：", response.status_code)
            print("URL：", response.url)
            print("响应内容前 500 字：")
            print(response.text[:500])
            raise RuntimeError("接口请求被拒绝，可能需要浏览器 Cookie")
        return response.json()

    data = fetch_page(1)
    result = data.get("result") or {}
    totalcount = result.get("totalCount", 0)
    search_result = result.get("searchResult") or {}
    this_page = search_result.get("productRecordList") or []
    res.extend(this_page)
    print(f"总数量：{totalcount}")
    print(f"当前第 1 页，已获取 {len(res)}/{totalcount}")
    total_pages = math.ceil(totalcount / PAGE_SIZE)
    for page in range(2, total_pages + 1):
        time.sleep(0.2)
        data = fetch_page(page)
        result = data.get("result") or {}
        search_result = result.get("searchResult") or {}
        this_page = search_result.get("productRecordList") or []
        if not this_page:
            break
        res.extend(this_page)
        print(f"当前第 {page} 页，已获取 {len(res)}/{totalcount}")
        last_product_vo = this_page[-1].get("productVO") or {}
        last_price = get_first_price(last_product_vo)
        if last_price is not None and last_price > D(maxprice) + D(2):
            print(f"已超过价格限制，当前价格为 {last_price}，停止获取")
            break
    return res


def calculate(brandIdFilter, price):
    all_goods = get_all(brandIdFilter, price)
    res = []
    max_search_price = D(price) + D(2)
    for item in all_goods:
        product_vo = item.get("productVO") or {}
        product_code = product_vo.get("productCode")
        if not product_code:
            continue
        valid_stock = int(product_vo.get("validStockNumber") or 0)
        if valid_stock <= 0:
            continue
        ratio = product_vo.get("convesionRatio", 1) or 1
        ratio = D(ratio)
        product_price_list = product_vo.get("productPriceList") or []
        price_ranges = []
        for price_item in product_price_list:
            raw_price = price_item.get("productPrice")
            if raw_price is None:
                continue
            unit_price = D(raw_price) * ratio
            sp_number = int(price_item.get("spNumber") or 1)
            ep_number = int(price_item.get("epNumber") or valid_stock)
            start_qty = max(1, sp_number)
            end_qty = min(ep_number, valid_stock)
            if unit_price <= max_search_price and start_qty <= end_qty:
                price_ranges.append([unit_price, start_qty, end_qty])

        if price_ranges:
            res.append([price_ranges, product_code])

    return res


def build_product_options(price_ranges, product_code, upper_int):
    options = []
    seen_subtotal = set()
    for unit_price, start_qty, end_qty in price_ranges:
        price_int = money_to_int(unit_price)
        if price_int <= 0:
            continue
        max_qty_by_money = int(Decimal(upper_int) / Decimal(100) / unit_price) + 2
        real_end_qty = min(end_qty, max_qty_by_money)
        if real_end_qty < start_qty:
            continue
        for qty in range(start_qty, real_end_qty + 1):
            raw_subtotal = unit_price * qty
            subtotal = round_money(raw_subtotal)
            subtotal_int = money_to_int(subtotal)
            if subtotal_int > upper_int:
                continue
            key = subtotal_int
            if key in seen_subtotal:
                continue
            seen_subtotal.add(key)
            options.append(
                {
                    "code": product_code,
                    "qty": qty,
                    "price": unit_price,
                    "raw_subtotal": raw_subtotal,
                    "subtotal_int": subtotal_int,
                }
            )
    options.sort(key=lambda x: x["subtotal_int"])
    return options


def find_best_orders(goods, target=16, top_n=5, initial_extra=2, max_expand_times=6, max_total_states=1000000, per_total_limit=5, required_codes=None):
    """
    goods	calculate() 返回的商品价格档数据
    target	目标金额，要求结果总价 大于等于 这个值
    top_n	返回几个凑单方案，例如 5
    initial_extra	初始搜索范围，例如 2 表示先找 16 ~ 18 元之间的方案
    max_expand_times	如果找不到足够方案，最多扩大搜索范围几次
    max_total_states	动态规划状态数量上限，越大越准但越慢
    per_total_limit	同一个总价最多保留几个不同组合
    required_codes	必须包含的货号列表，例如 ["C123456"]
    """
    if required_codes is None:
        required_codes = []
    required_codes = set(str(code).strip() for code in required_codes if str(code).strip())
    target_int = money_to_int(target)
    for expand_index in range(max_expand_times + 1):
        extra = D(initial_extra) * (D(2) ** expand_index)
        upper = D(target) + extra
        upper_int = money_to_int(upper)
        product_options = []
        for price_ranges, product_code in goods:
            product_code = str(product_code).strip()
            options = build_product_options(price_ranges, product_code, upper_int)
            if options:
                product_options.append((product_code, options))

        available_codes = {code for code, _ in product_options}
        missing_codes = required_codes - available_codes
        if missing_codes:
            print("以下指定货号没有可用价格档，无法参与凑单：")
            for code in missing_codes:
                print(" ", code)
            return []
        states = {0: [[]]}
        for index, (product_code, options) in enumerate(product_options, 1):
            old_states = list(states.items())
            # 普通货号：可以跳过
            # 指定必须包含的货号：不能跳过，必须选一个数量
            if product_code in required_codes:
                new_states = {}
            else:
                new_states = {total: combos[:] for total, combos in states.items()}
            for current_total, combos in old_states:
                for option in options:
                    new_total = current_total + option["subtotal_int"]
                    if new_total > upper_int:
                        break
                    bucket = new_states.setdefault(new_total, [])
                    if len(bucket) >= per_total_limit:
                        continue
                    for combo in combos:
                        if len(bucket) >= per_total_limit:
                            break
                        bucket.append(combo + [option])
            states = new_states
            if not states:
                break
            if len(states) > max_total_states:
                over_keys = sorted(key for key in states.keys() if key >= target_int)
                under_keys = sorted((key for key in states.keys() if key < target_int), reverse=True)
                keep_over_count = min(len(over_keys), top_n * 50)
                keep_under_count = max_total_states - keep_over_count
                keep_keys = set(over_keys[:keep_over_count] + under_keys[:keep_under_count] + [0])
                states = {key: states[key][:per_total_limit] for key in keep_keys if key in states}
            print(f"已处理 {index}/{len(product_options)} 个货号，当前状态数：{len(states)}")
        results = []
        for total_int in sorted(states.keys()):
            if total_int < target_int:
                continue
            for combo in states[total_int]:
                if not combo:
                    continue
                combo_codes = {item["code"] for item in combo}
                # 双重保险：确保所有指定货号都在方案里
                if not required_codes.issubset(combo_codes):
                    continue
                results.append(
                    {
                        "total": int_to_money(total_int),
                        "items": [
                            {
                                "code": item["code"],
                                "qty": item["qty"],
                                "price": item["price"],
                                "raw_subtotal": item["raw_subtotal"],
                                "subtotal": int_to_money(item["subtotal_int"]),
                            }
                            for item in combo
                        ],
                    }
                )
                if len(results) >= top_n:
                    return results[:top_n]
        print(f"在 {target} 到 {upper} 范围内没有找到足够方案，扩大搜索范围...")

    return results[:top_n]


def print_orders(orders):
    if not orders:
        print("没有找到合适的凑单方案")
        return
    print("\n========== 最优凑单方案 ==========")
    for index, order in enumerate(orders, 1):
        print(f"\n方案 {index}：总价 = {fmt_money(order['total'])}")
        for item in order["items"]:
            print(f"  货号：{item['code']}，" f"数量：{item['qty']}，" f"单价：{item['price']}，" f"未舍入小计：{item['raw_subtotal']}，" f"结算小计：{fmt_money(item['subtotal'])}")


if __name__ == "__main__":
    brand_id = 12131
    # 品牌代码
    target_price = 16
    # 凑单价格
    goods = calculate(brand_id, target_price)
    print(f"\n可参与计算的货号数量：{len(goods)}")
    orders = find_best_orders(goods, target=target_price, top_n=5, initial_extra=2)
    # orders = find_best_orders(goods, target=target_price, top_n=5, initial_extra=2, required_codes=["C123456", "C234567"])
    print_orders(orders)
