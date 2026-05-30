# 立创商城自动凑单工具

一个用于立创商城（LCSC）商品凑单的 Python 脚本工具。

该工具可以根据指定品牌 ID 和目标金额，自动获取该品牌下的商品价格与库存信息，并计算出若干个满足条件的凑单方案，帮助用户快速找到总价刚好超过目标金额的商品组合。

## 使用场景

适用于以下情况：

- 立创商城下单时需要凑满指定金额
- 想从某个品牌中自动寻找低价商品组合
- 需要指定某些商品必须出现在凑单方案中
- 需要指定某些商品的采购组数
- 想避免手动逐个商品计算价格和数量

## 环境要求

- Python 3.8+
- requests

## 安装依赖

```bash
pip install requests
```

## 快速开始

将脚本保存为 `main.py`，然后运行：

```bash
python main.py
```

默认配置位于脚本底部：

```python
if __name__ == "__main__":
    brand_id = 12131
    # 品牌代码

    target_price = 16
    # 凑单价格

    goods = calculate(brand_id, target_price)

    print(f"\n可参与计算的货号数量：{len(goods)}")

    orders = find_best_orders(
        goods,
        target=target_price,
        top_n=5,
        initial_extra=2,
        required_codes=[
            # 只要求包含，不指定数量
            # "C123456",

            # 只要求包含，不指定数量
            # ["C234567"],

            # 要求包含，并且采购组数必须是 10
            # ["C345678", 10],
        ],
    )

    print_orders(orders)
```

## 参数说明

### brand_id

品牌 ID，用于指定要从立创商城哪个品牌下获取商品。

```python
brand_id = 12131
```

### target_price

目标凑单金额。

脚本会寻找总价大于等于该金额的商品组合。

```python
target_price = 16
```

例如目标金额为 `16`，则会寻找总价大于等于 `16` 元的方案。

### top_n

返回的凑单方案数量。

```python
orders = find_best_orders(
    goods,
    target=16,
    top_n=5
)
```

### initial_extra

初始搜索范围。

例如：

```python
orders = find_best_orders(
    goods,
    target=16,
    initial_extra=2
)
```

表示优先在 `16 ~ 18` 元之间寻找方案。

如果找不到足够方案，脚本会自动扩大搜索范围。

### max_expand_times

最大扩大搜索范围次数。

```python
orders = find_best_orders(
    goods,
    target=16,
    max_expand_times=6
)
```

搜索范围会按倍数逐步扩大。

### max_total_states

动态规划状态数量上限。

```python
orders = find_best_orders(
    goods,
    target=16,
    max_total_states=1000000
)
```

数值越大，搜索结果可能越准确，但运行时间和内存占用也会增加。

### per_total_limit

同一个总价最多保留几个不同组合。

```python
orders = find_best_orders(
    goods,
    target=16,
    per_total_limit=5
)
```

### required_codes

指定必须包含的商品货号。

`required_codes` 支持三种写法：

```python
required_codes=[
    "C123456",        # 必须包含该货号，采购组数不限
    ["C234567"],      # 必须包含该货号，采购组数不限
    ["C345678", 10],  # 必须包含该货号，并且采购组数必须是 10
]
```

含义如下：

| 写法 | 含义 |
|---|---|
| `"C123456"` | 必须包含 `C123456`，采购组数不限 |
| `["C234567"]` | 必须包含 `C234567`，采购组数不限 |
| `["C345678", 10]` | 必须包含 `C345678`，采购组数必须是 `10` |

如果只写货号，不写数量，则表示该货号必须出现在凑单方案中，但采购组数由脚本自动计算。

如果写成 `["货号", 数量]`，则表示该货号必须出现在凑单方案中，并且采购组数必须等于指定数量。

示例：

```python
orders = find_best_orders(
    goods,
    target=16,
    top_n=5,
    initial_extra=2,
    required_codes=[
        "C123456",
        ["C234567", 10],
        ["C345678"]
    ]
)
```

上面的配置表示：

- `C123456` 必须包含，采购组数不限
- `C234567` 必须包含，采购组数必须是 `10`
- `C345678` 必须包含，采购组数不限

如果指定的货号没有库存、没有可用价格档，或者指定数量不在可购买范围内，脚本会提示并返回空结果。

## 使用示例

### 普通凑单

```python
brand_id = 12131
target_price = 16

goods = calculate(brand_id, target_price)

orders = find_best_orders(
    goods,
    target=target_price,
    top_n=5,
    initial_extra=2
)

print_orders(orders)
```

### 指定必须包含某些货号

```python
brand_id = 12131
target_price = 16

goods = calculate(brand_id, target_price)

orders = find_best_orders(
    goods,
    target=target_price,
    top_n=5,
    initial_extra=2,
    required_codes=[
        "C123456",
        "C234567"
    ]
)

print_orders(orders)
```

### 指定必须包含某些货号，并指定数量

```python
brand_id = 12131
target_price = 16

goods = calculate(brand_id, target_price)

orders = find_best_orders(
    goods,
    target=target_price,
    top_n=5,
    initial_extra=2,
    required_codes=[
        ["C234567", 10],
        ["C345678", 20]
    ]
)

print_orders(orders)
```

## 输出示例

```text
总数量：120
当前第 1 页，已获取 30/120
当前第 2 页，已获取 60/120

可参与计算的货号数量：58

已处理 1/58 个货号，当前状态数：12
已处理 2/58 个货号，当前状态数：48
已处理 3/58 个货号，当前状态数：103

========== 最优凑单方案 ==========

方案 1：总价 = 16.03
  货号：C123456，采购组数：3，单价：2.01，未舍入小计：6.03，结算小计：6.03
  货号：C234567，采购组数：10，单价：1，未舍入小计：10，结算小计：10.00

方案 2：总价 = 16.12
  货号：C345678，采购组数：4，单价：4.03，未舍入小计：16.12，结算小计：16.12
```

## 核心函数说明

### calculate

```python
calculate(brandIdFilter, price)
```

用于获取指定品牌下可参与凑单计算的商品数据。

参数说明：

| 参数 | 说明 |
|---|---|
| `brandIdFilter` | 品牌 ID |
| `price` | 目标价格 |

返回值：

```python
[
    [
        [
            [unit_price, start_qty, end_qty],
            ...
        ],
        product_code
    ],
    ...
]
```

每个商品包含：

- 可用价格档
- 商品货号

### find_best_orders

```python
find_best_orders(
    goods,
    target,
    top_n=5,
    initial_extra=2,
    max_expand_times=6,
    max_total_states=1000000,
    per_total_limit=5,
    required_codes=None
)
```

用于根据商品价格档计算最优凑单方案。

参数说明：

| 参数 | 说明 |
|---|---|
| `goods` | `calculate()` 返回的商品数据 |
| `target` | 目标金额，结果总价需要大于等于该值 |
| `top_n` | 返回方案数量 |
| `initial_extra` | 初始搜索范围 |
| `max_expand_times` | 最大扩大搜索范围次数 |
| `max_total_states` | 动态规划状态数量上限 |
| `per_total_limit` | 同一总价最多保留的组合数量 |
| `required_codes` | 必须包含的货号列表，可选指定采购组数 |

`required_codes` 示例：

```python
required_codes=[
    "C123456",
    ["C234567"],
    ["C345678", 10]
]
```

说明：

| 写法 | 说明 |
|---|---|
| `"C123456"` | 必须包含该货号，采购组数不限 |
| `["C234567"]` | 必须包含该货号，采购组数不限 |
| `["C345678", 10]` | 必须包含该货号，采购组数必须是 `10` |

### print_orders

```python
print_orders(orders)
```

用于打印凑单结果。

输出内容包括：

- 方案编号
- 总价
- 商品货号
- 采购组数
- 单价
- 未舍入小计
- 结算小计

## 注意事项

1. 该工具依赖立创商城网页接口，接口结构变化可能导致脚本失效。
2. 如果请求被拒绝，可能需要浏览器 Cookie。
3. 请求过快可能触发限制，脚本中已加入 `time.sleep(0.2)` 降低请求频率。
4. `required_codes` 中指定的数量表示采购组数，不一定等同于实际单颗数量，具体取决于商品包装和换算比例。
5. 本工具仅用于辅助计算，最终价格和库存请以下单页面为准。

## 常见问题

### 请求失败怎么办？

如果看到类似提示：

```text
接口请求被拒绝，可能需要浏览器 Cookie
```

可能原因包括：

- 接口需要登录态
- 请求头被识别为非浏览器请求
- 访问频率过高
- 立创商城接口发生变化

可以尝试：

- 降低请求频率
- 在请求中加入浏览器 Cookie
- 检查接口返回内容
- 使用浏览器开发者工具重新确认接口参数

### 为什么指定了货号和数量后没有结果？

可能原因包括：

- 指定货号没有库存
- 指定货号不存在可用价格档
- 指定数量低于该商品价格档的起购数量
- 指定数量超过当前库存
- 指定数量对应的小计已经超过当前搜索范围
- 加入指定商品后，无法在当前搜索范围内凑出满足条件的组合

可以尝试：

- 检查货号是否正确
- 调整指定数量
- 增大 `initial_extra`
- 增大 `max_expand_times`
- 减少必须包含的货号数量

### 为什么运行时间比较长？

凑单计算本质上是组合搜索问题。

如果品牌商品数量很多、价格档很多、库存数量较大，动态规划状态会快速增加。

可以尝试：

- 减小 `initial_extra`
- 减小 `top_n`
- 减小 `max_total_states`
- 指定更小的目标范围
- 选择商品数量更少的品牌

## 免责声明

本项目仅用于学习和个人辅助下单计算，不保证接口长期可用，也不保证计算结果与立创商城最终下单价格完全一致。

请以下单页面显示的价格、库存、优惠规则和最终结算金额为准。
