# Reddit AI Trend Report 补充生成工具

此目录包含用于补充生成特定日期范围内缺失报告的工具。这些工具不会修改现有代码，而是通过调用现有的report_generation.py脚本并传递特定日期参数来实现。

## 文件说明

- `backfill_reports.py`: 主要的补充生成脚本，用于生成特定日期范围内缺失的报告。
- `check_missing_reports.py`: 用于检查特定日期范围内缺失的报告。
- `backfill.log`: 补充生成过程的日志文件。
- `check_missing.log`: 检查缺失报告过程的日志文件。

## 使用方法

### 检查缺失的报告

使用以下命令检查特定日期范围内缺失的报告：

```bash
python backfill/check_missing_reports.py --start 2023-01-01 --end 2023-01-31
```

参数说明：
- `--start`: 开始日期 (YYYY-MM-DD)
- `--end`: 结束日期 (YYYY-MM-DD)
- `--interval`: 报告间隔小时数，默认为24小时
- `--output`: 输出文件路径，如果提供则将结果写入文件

示例：
```bash
# 检查2023年1月缺失的报告，并将结果写入文件
python backfill/check_missing_reports.py --start 2023-01-01 --end 2023-01-31 --output backfill/missing_reports_jan_2023.txt
```

### 补充生成缺失的报告

使用以下命令补充生成特定日期范围内缺失的报告：

```bash
python backfill/backfill_reports.py --start 2023-01-01 --end 2023-01-31
```

参数说明：
- `--start`: 开始日期 (YYYY-MM-DD)
- `--end`: 结束日期 (YYYY-MM-DD)
- `--interval`: 报告间隔小时数，默认为24小时
- `--push`: 是否推送报告到GitHub，默认为否
- `--force`: 是否强制重新生成已存在的报告，默认为否

示例：
```bash
# 补充生成2023年1月缺失的报告，并推送到GitHub
python backfill/backfill_reports.py --start 2023-01-01 --end 2023-01-31 --push

# 强制重新生成2023年1月的所有报告
python backfill/backfill_reports.py --start 2023-01-01 --end 2023-01-31 --force
```

## 工作原理

1. 检查缺失报告：
   - 从MongoDB获取所有已存在的报告日期
   - 检查指定日期范围内哪些日期缺失报告
   - 输出缺失的日期列表

2. 补充生成报告：
   - 如果不是强制模式，先检查哪些日期缺失报告
   - 对于每个缺失的日期，调用report_generation.py脚本生成报告
   - 报告生成后会保存到MongoDB和文件系统
   - 如果指定了--push参数，还会推送到GitHub

## 注意事项

- 这些工具依赖于现有的report_generation.py脚本，确保该脚本能正常工作。
- 补充生成过程中会创建临时文件，脚本会在完成后自动清理这些文件。
- 如果遇到问题，请查看日志文件(backfill.log或check_missing.log)获取详细信息。
- 强制模式会重新生成指定日期范围内的所有报告，即使它们已经存在。
- 推送到GitHub功能依赖于现有的GitHub集成，确保已正确配置GitHub相关设置。 