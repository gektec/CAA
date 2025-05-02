import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


def report_removed_row(
    df: pd.DataFrame,
    idx: int,
    label_col: Optional[str],
    reason: str
) -> Dict[str, Any]:
    """
    打印并返回被剔除行的信息和原因：
      - 打印行的 label、剔除原因，以及该行的非零字段及其值（不含标签列）
      - 返回包含 label、reason 和非零字段值的字典

    参数:
        df: 原始 DataFrame
        idx: 行索引
        label_col: 标签列名称（若为 None 则用行索引作为 label）
        reason: 本次剔除的原因描述

    返回:
        dict: {
          "label": 行标签,
          "reason": 剔除原因,
          "values": {字段: 值, ...}
        }
    """
    row = df.loc[idx]
    label = row[label_col] if (label_col and label_col in df.columns) else idx

    # 取非零字段（排除标签列）
    non_zero = row[row != 0]
    if label_col and label_col in non_zero.index:
        non_zero = non_zero.drop(label_col)

    info = {
        "label": label,
        "reason": reason,
        "values": non_zero.to_dict()
    }
    print(f"\n--- 剔除行 {label} 原因：{reason}")
    print(f"    非零字段: {info['values']}")
    return info


def clean_by_balance(
    infile: str,
    outfile: str,
    threshold: float = 1.0,
    label_col: Optional[str] = None
) -> None:
    """
    均衡清洗流程：
      1. 读 CSV；
      2. 各列绝对值均值（跳过 0）→ inv_mean；
      3. 计算每行 score = ∑(value * inv_mean)；
      4. 丢弃 score 超出 [-threshold, +threshold] 的行、打印原因和值；
      5. 写出保留行。
    """
    df = pd.read_csv(infile)
    print(f"\n=== clean_by_balance: 原始行数 = {len(df)} ===")

    # 计算各列（非零）绝对值均值
    mean_abs = df.replace(0, np.nan).abs().mean()
    inv_mean = 1.0 / mean_abs.replace(0, np.nan)
    inv_mean = inv_mean.fillna(0.0)

    # 计算每行 score
    scores = df.mul(inv_mean, axis=1).sum(axis=1)

    # 筛选
    keep_mask = scores.between(-threshold, threshold)
    dropped_idx = df.index[~keep_mask]

    # 打印剔除信息
    removed_info = []
    for idx in dropped_idx:
        sc = scores.at[idx]
        reason = f"score={sc:.4f} 不在 [-{threshold}, +{threshold}]"
        removed_info.append(
            report_removed_row(df, idx, label_col, reason)
        )

    kept = df[keep_mask]
    print(f"\nclean_by_balance: 剔除 {len(removed_info)} 行，保留 {len(kept)} 行")
    kept.to_csv(outfile, index=False)
    print(f"清洗后数据已写入: {outfile}")


def clean_special_rows(
    infile: str,
    outfile: str,
    label_col: Optional[str] = None
) -> None:
    """
    剔除全正行、全负行、重复行、完全相反行，
    调用方式与 clean_verbose 完全一致：传入 infile/outfile/label_col，不返回，写文件并打印日志。
    """
    df = pd.read_csv(infile)
    print(f"\n=== clean_special_rows: 原始行数 = {len(df)} ===")

    # 1. 全正数行 & 全负数行
    for cond, desc in [(df.gt(0).all(axis=1), "全正数行"),
                       (df.lt(0).all(axis=1), "全负数行")]:
        for idx in df.index[cond]:
            report_removed_row(df, idx, label_col, desc)
        df = df[~cond]

    # 2. 重复行（保留首次出现）
    dup_mask = df.duplicated(keep='first')
    for idx in df.index[dup_mask]:
        report_removed_row(df, idx, label_col, "重复行")
    df = df[~dup_mask]

    # 3. 完全相反行
    # seen = set()
    # to_drop = []
    # for idx, row in df.iterrows():
    #     tup = tuple(row.values)
    #     opp_tup = tuple((-row.values).tolist())
    #     if opp_tup in seen:
    #         to_drop.append(idx)
    #     else:
    #         seen.add(tup)
    # for idx in to_drop:
    #     report_removed_row(df, idx, label_col, "完全相反行")
    # if to_drop:
    #     df = df.drop(index=to_drop)

    print(f"\nremove_special_rows: 最终剩余行数 = {len(df)}")
    df.to_csv(outfile, index=False)
    print(f"清洗后数据已写入: {outfile}")



def clean_verbose(
    infile: str,
    outfile: str,
    label_col: Optional[str] = None
) -> None:
    """
    详细清洗流程：
      1. 读 CSV；
      2. 计算各列非零绝对值均值 → mean_abs；
      3. 对每个单元格，若 val!=0 且 abs(val) 不在 [0.5*mean, 2.0*mean]，则剔除该行；
      4. 剔除全正行、全负行、重复行、完全相反行，打印原因和值；
      5. 写出最终结果。
    """
    df = pd.read_csv(infile)
    print(f"\n=== clean_verbose: 原始行数 = {len(df)} ===")

    # 各列非零绝对值均值
    mean_abs = df.replace(0, pd.NA).abs().mean(skipna=True)
    lower = 0.4 * mean_abs
    upper = 2.5 * mean_abs

    # 标记每行是否保留
    keep_rows = pd.Series(True, index=df.index)

    # 逐行逐列检查异常值
    for idx, row in df.iterrows():
        if not keep_rows.at[idx]:
            continue
        for col in df.columns:
            m = mean_abs[col]
            val = row[col]
            if pd.isna(m) or val == 0:
                continue
            if not (lower[col] <= abs(val) <= upper[col]):
                reason = (
                    f"列'{col}' val={val} 不在区间"
                    f"[{lower[col]:.3f}, {upper[col]:.3f}]"
                )
                report_removed_row(df, idx, label_col, reason)
                keep_rows.at[idx] = False
                break


if __name__ == "__main__":
    # 示例调用
    clean_by_balance("results.csv", "results1.csv", threshold=1.0, label_col="id")
    clean_special_rows("results1.csv", "results1.csv", label_col="id")
    clean_verbose("results1.csv", "results1.csv", label_col="id")
