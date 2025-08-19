import os

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO


def return_img_bytes(plt):
    # 保存图表到字节流
    img_bytes = BytesIO()
    plt.savefig(img_bytes , format='png')
    img_bytes.seek(0)
    # 清空图表
    plt.close()
    # 返回图片字节流
    return img_bytes


def draw_biotop(file_path="biotop_data.csv", img_path="./kylinApp/static/img/biotop", tp="png"):
    # 使用 Pandas 读取 CSV 文件并按照 'I/O' 操作次数排序
    df = pd.read_csv(file_path)
    df_sorted = df.sort_values(by='I/O', ascending=False)  # 按照 'I/O' 操作次数降序排序

    # 设置 Seaborn 风格
    sns.set(style="whitegrid")
    plt.figure(dpi=300)
    # 创建图表
    fig, axs = plt.subplots( ncols=2, figsize=(12, 5))

    # 图表1：每个进程的 IO 操作次数（按照降序排列）
    sns.barplot(x='I/O', y='COMM', data=df_sorted, ax=axs[0], palette='Blues_d')
    axs[0].set_title('IO Operations Count by Process')
    axs[0].tick_params(axis='y', rotation=0)
    # 图表2：每个进程的总千字节数（按照降序排列）
    sns.barplot(x='Kbytes', y='COMM', data=df_sorted, ax=axs[1], palette='Greens_d')

    axs[1].set_title('Total Kbytes by Process')
    axs[1].tick_params(axis='y', rotation=0)

    plt.tight_layout()
    plt.savefig(f'{img_path}.{tp}')


def draw_xfsslower(file_path="xfsslower_data.csv",  img_path="./kylinApp/static/img/xfsslower", tp="png"):
    # 读取文件
    df = pd.read_csv(file_path)
    df_sort = df.sort_values(by='LAT', ascending=False)
    sns.set(style="whitegrid")
    # 使用Seaborn绘制柱状图

    plt.figure(figsize=(6, 5),dpi=300)
    sns.barplot(x='COMM', y='LAT(ms)', data=df_sort, palette='viridis')
    plt.xlabel('The name of the process')
    plt.ylabel('Delay (ms)')
    plt.title('Latency of different processes')
    plt.xticks(rotation=45)
    plt.tight_layout()
    # 显示图表
    plt.savefig(f'{img_path}.{tp}')
