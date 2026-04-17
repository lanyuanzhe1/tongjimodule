import os
import shutil

# 定义源文件夹和目标文件夹
source_dir = "e:\\code\\tongjimodule\\data\\碳核算数据库\\ceads_excel_downloads"
target_dir = "e:\\code\\tongjimodule\\data\\碳核算数据库\\data_ceads_used"

# 如果目标文件夹不存在则创建它
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 复制文件计数器
copied_count = 0

# 遍历源文件夹下的所有文件
for filename in os.listdir(source_dir):
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        # 检查文件名中是否包含2011到2024之间的年份
        # 单独处理年份范围类的文件（比如 1997-2022 这种）
        should_copy = False
        
        # 提取年份相关逻辑
        for year in range(2011, 2025): # 2011 ~ 2024
            if str(year) in filename:
                should_copy = True
                break
                
        # 执行复制
        if should_copy:
            src_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(target_dir, filename)
            shutil.copy2(src_path, dest_path)
            print(f"已复制: {filename}")
            copied_count += 1

print(f"\n筛选完成！共将 {copied_count} 个 2011-2024 年间的数据文件复制到了 data_ceads_used 文件夹。")
