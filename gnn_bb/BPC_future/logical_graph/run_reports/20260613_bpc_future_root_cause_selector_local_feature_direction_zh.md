# Root Cause Selector Local Feature Direction 报告

日期：2026-06-13

## 目标

本报告只读分析 context-collision mixed groups 内部的列局部特征方向，
检查是否可以用“true-RC 更低”或“cost 更低”这类简单单调规则分开
improved 与 noop。不运行 BPC，不修改 solver。

## 关键结果

```text
row_count = 280
task_set_true_rc_direction_counts = {'improved_lower_mean': 2, 'noop_lower_mean': 4}
task_sequence_true_rc_direction_counts = {'noop_lower_mean': 3, 'improved_lower_mean': 2}
task_set_cost_direction_counts = {'improved_lower_mean': 1, 'noop_lower_mean': 3, 'equal_mean': 2}
task_sequence_cost_direction_counts = {'equal_mean': 3, 'noop_lower_mean': 2}
```

## 示例

```json
{
  "task_flags": [
    {
      "context_count": 2,
      "dataset_count": 3,
      "direction": "improved_lower_mean",
      "improved_mean": -136.48485057142858,
      "improved_range": [
        -137.15071,
        -135.597038
      ],
      "key": [
        "4,5,8",
        "True",
        "False",
        "False"
      ],
      "label_counts": {
        "improved": 7,
        "noop": 3
      },
      "noop_mean": -70.359444,
      "noop_range": [
        -70.359444,
        -70.359444
      ],
      "overlap": false
    },
    {
      "context_count": 5,
      "dataset_count": 3,
      "direction": "noop_lower_mean",
      "improved_mean": -34.8665505,
      "improved_range": [
        -34.8665505,
        -34.8665505
      ],
      "key": [
        "5,12,18",
        "True",
        "False",
        "False"
      ],
      "label_counts": {
        "improved": 1,
        "noop": 6
      },
      "noop_mean": -67.74362370833333,
      "noop_range": [
        -128.547499,
        -5.95738825
      ],
      "overlap": true
    },
    {
      "context_count": 2,
      "dataset_count": 1,
      "direction": "noop_lower_mean",
      "improved_mean": -3.918124923,
      "improved_range": [
        -3.918124923,
        -3.918124923
      ],
      "key": [
        "2,7,10,17",
        "True",
        "False",
        "False"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -34.525806,
      "noop_range": [
        -34.525806,
        -34.525806
      ],
      "overlap": false
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "direction": "noop_lower_mean",
      "improved_mean": -72.94184266666667,
      "improved_range": [
        -72.970624,
        -72.927452
      ],
      "key": [
        "4,12,14",
        "True",
        "False",
        "False"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -73.864202,
      "noop_range": [
        -73.864202,
        -73.864202
      ],
      "overlap": false
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "direction": "noop_lower_mean",
      "improved_mean": -119.52196566666667,
      "improved_range": [
        -119.550747,
        -119.507575
      ],
      "key": [
        "4,12,17",
        "True",
        "False",
        "False"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -121.65470999999998,
      "noop_range": [
        -121.65471,
        -121.65471
      ],
      "overlap": false
    }
  ],
  "task_sequence": [
    {
      "context_count": 2,
      "dataset_count": 1,
      "direction": "noop_lower_mean",
      "improved_mean": -3.918124923,
      "improved_range": [
        -3.918124923,
        -3.918124923
      ],
      "key": [
        "2,7,10,17",
        "10-17-2-7"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -34.525806,
      "noop_range": [
        -34.525806,
        -34.525806
      ],
      "overlap": false
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "direction": "noop_lower_mean",
      "improved_mean": -72.94184266666667,
      "improved_range": [
        -72.970624,
        -72.927452
      ],
      "key": [
        "4,12,14",
        "14-12-4"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -73.864202,
      "noop_range": [
        -73.864202,
        -73.864202
      ],
      "overlap": false
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "direction": "noop_lower_mean",
      "improved_mean": -119.52196566666667,
      "improved_range": [
        -119.550747,
        -119.507575
      ],
      "key": [
        "4,12,17",
        "17-12-4"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -121.65470999999998,
      "noop_range": [
        -121.65471,
        -121.65471
      ],
      "overlap": false
    },
    {
      "context_count": 2,
      "dataset_count": 2,
      "direction": "improved_lower_mean",
      "improved_mean": -135.597038,
      "improved_range": [
        -135.597038,
        -135.597038
      ],
      "key": [
        "4,5,8",
        "5-8-4"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -70.359444,
      "noop_range": [
        -70.359444,
        -70.359444
      ],
      "overlap": false
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "direction": "improved_lower_mean",
      "improved_mean": -133.018537,
      "improved_range": [
        -133.018537,
        -133.018537
      ],
      "key": [
        "5,12,15",
        "12-5-15"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -0.586,
      "noop_range": [
        -0.586,
        -0.586
      ],
      "overlap": false
    }
  ],
  "task_set": [
    {
      "context_count": 2,
      "dataset_count": 3,
      "direction": "improved_lower_mean",
      "improved_mean": -136.48485057142858,
      "improved_range": [
        -137.15071,
        -135.597038
      ],
      "key": [
        "4,5,8"
      ],
      "label_counts": {
        "improved": 7,
        "noop": 3
      },
      "noop_mean": -70.359444,
      "noop_range": [
        -70.359444,
        -70.359444
      ],
      "overlap": false
    },
    {
      "context_count": 5,
      "dataset_count": 3,
      "direction": "noop_lower_mean",
      "improved_mean": -34.8665505,
      "improved_range": [
        -34.8665505,
        -34.8665505
      ],
      "key": [
        "5,12,18"
      ],
      "label_counts": {
        "improved": 1,
        "noop": 6
      },
      "noop_mean": -67.74362370833333,
      "noop_range": [
        -128.547499,
        -5.95738825
      ],
      "overlap": true
    },
    {
      "context_count": 2,
      "dataset_count": 1,
      "direction": "noop_lower_mean",
      "improved_mean": -3.918124923,
      "improved_range": [
        -3.918124923,
        -3.918124923
      ],
      "key": [
        "2,7,10,17"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -34.525806,
      "noop_range": [
        -34.525806,
        -34.525806
      ],
      "overlap": false
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "direction": "noop_lower_mean",
      "improved_mean": -72.94184266666667,
      "improved_range": [
        -72.970624,
        -72.927452
      ],
      "key": [
        "4,12,14"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -73.864202,
      "noop_range": [
        -73.864202,
        -73.864202
      ],
      "overlap": false
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "direction": "noop_lower_mean",
      "improved_mean": -119.52196566666667,
      "improved_range": [
        -119.550747,
        -119.507575
      ],
      "key": [
        "4,12,17"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "noop_mean": -121.65470999999998,
      "noop_range": [
        -121.65471,
        -121.65471
      ],
      "overlap": false
    }
  ]
}
```

## 解释

在 mixed task-set / sequence groups 内，true-RC 与 cost 的方向并不稳定：有些组 improved row 的 true-RC 更低，有些组 noop row 的 true-RC 更低。因此不能通过一个简单的列局部单调规则修复 selector。

注意：把 exact task-set / sequence / true-RC / cost 全部作为 lookup key 时
可以减少混合，但那等价于 replay-context 记忆，不是 production selector。
总 threshold frontier 也已经显示没有单一 true-RC 阈值能同时消除 false
positive 与 false negative。
