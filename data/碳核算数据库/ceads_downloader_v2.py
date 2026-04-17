import requests
from bs4 import BeautifulSoup
import os
import time
import urllib.parse

# 目标网址与下载基础接口
base_url = "https://www.ceads.net.cn/data/province/"
download_api = "https://www.ceads.net/user/dl.php" # 真实的下载接口

# 创建一个文件夹来保存下载的Excel文件
download_dir = r"E:\code\tongjimodule\data\碳核算数据库\ceads_excel_downloads"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# =========================================================================
# 【关键步骤】：请在这里填入您的 Cookie
# 请在浏览器的 Network 面板中，找到任意一个真实的网页请求（比如您刚才截图的 category_tree.php 或 default_config.content.json 的同级请求），
# 查看右下角的 Request Headers (请求标头) 区域，找到 `Cookie: xxxxxx` 这一整行，
# 复制冒号后面的所有内容，粘贴到下面引号内。
# =========================================================================
YOUR_COOKIE = "__51vcke__Jeoilr6pp16XyuUv=2a422bae-6752-5617-a390-2ec5f466393b; __51vuft__Jeoilr6pp16XyuUv=1775962483220; PHPSESSID=4h69h5n5hqrg6h5o9oul93aomm; __51uvsct__Jeoilr6pp16XyuUv=3; __vtins__Jeoilr6pp16XyuUv=%7B%22sid%22%3A%20%2273539b88-9b81-5c1c-b700-07ab9087c005%22%2C%20%22vd%22%3A%203%2C%20%22stt%22%3A%2018492%2C%20%22dr%22%3A%2013253%2C%20%22expires%22%3A%201775972709597%2C%20%22ct%22%3A%201775970909597%7D"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
    'Cookie': YOUR_COOKIE
}

def bypass_and_download(file_id, filename):
    """根据ID伪造下载请求"""
    local_path = os.path.join(download_dir, f"{filename}.xlsx") # 默认保存为xlsx
    try:
        print(f"正在尝试下载: {filename} (ID: {file_id})")
        # 尝试直接请求下载接口，这里假设后端通过 id 参数控制文件吐出
        download_url = f"{download_api}?id={file_id}&lang=cn"
        
        response = requests.get(download_url, headers=headers, stream=True, timeout=30)
        
        # 检查是否因为没登录被重定向回了登录页
        if "login" in response.url.lower():
            print("  ❌ Cookie 无效或已过期，请重新获取 Cookie！")
            return False
            
        response.raise_for_status() 
        
        # 获取真实的文件扩展名 (如果服务器在请求头返回了 filename)
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            # 解析出真正的文件名并进行URL解码
            real_name = content_disposition.split('filename=')[-1].strip('"\'')
            real_name = urllib.parse.unquote(real_name)
            local_path = os.path.join(download_dir, real_name)
            
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"  ✅ 已保存至: {local_path}")
        return True
    except Exception as e:
        print(f"  ❌ 下载失败: ID {file_id}, 错误: {e}")
        return False

def main():
    print("开始获取省级清单列表的文档 ID 映射...")
    try:
        response = requests.get(base_url, headers={'User-Agent': headers['User-Agent']}, timeout=30)
        response.encoding = 'utf-8' 
        response.raise_for_status()
    except Exception as e:
        print(f"无法访问页面: {base_url}, 错误: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # 从页面上抓取带 data-id 的 A 标签 (因为真实文件由 JS 跳转触发)
    all_links = soup.find_all('a', href=True)
    target_files = []
    
    seen_ids = set()
    for link in all_links:
        data_id = link.get('data-id')
        link_text = link.get_text(strip=True)
        # 只要带 data-id 并且有名字的我们都抓取
        if data_id and link_text and data_id not in seen_ids:
            # 简单过滤非相关内容名字的长度
            if "清单" in link_text or "20" in link_text:
                target_files.append((data_id, link_text))
                seen_ids.add(data_id)

    print(f"共解析到 {len(target_files)} 个待下载的数据集（基于 ID 映射）。\n")
    
    if not YOUR_COOKIE:
        print("❗ 警告：您还没有在代码中配置 YOUR_COOKIE ! 未登录状态下文件由于后台权限限制是无法下载的。")
        print("请在浏览器中抓取 Cookie 并填入脚本后再执行！")
        return

    # 开始下载
    success_count = 0
    for idx, (file_id, file_name) in enumerate(target_files, 1):
        # 净化文件名
        safe_name = file_name.replace('/', '_').replace('\\', '_')
        print(f"[{idx}/{len(target_files)}] ", end='')
        
        if bypass_and_download(file_id, safe_name):
            success_count += 1
            
        time.sleep(1.5) # 给服务器喘息时间

    print(f"\n下载完成！成功: {success_count} 个, 失败: {len(target_files) - success_count} 个。")
    print(f"请检查目录: {os.path.abspath(download_dir)}")

if __name__ == "__main__":
    main()
