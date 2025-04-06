import os
import json
import re
import argparse

def parse_key_vdf(key_file_path):
    """解析Key.vdf文件获取解密密钥"""
    depot_keys = {}
    current_depot = None
    
    with open(key_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # 查找depot ID
            if re.match(r'^"\d+"$', line):
                current_depot = line.strip('"')
            # 查找DecryptionKey
            elif current_depot and '"DecryptionKey"' in line:
                key = line.split('"')[3]
                depot_keys[current_depot] = key
    
    return depot_keys

def find_manifest_files(directory):
    """查找并解析manifest文件名"""
    manifest_info = {}
    
    for filename in os.listdir(directory):
        if filename.endswith('.manifest'):
            parts = filename.split('_')
            if len(parts) == 2:
                depot_id = parts[0]
                manifest_id = parts[1].split('.')[0]
                manifest_info[depot_id] = manifest_id
    
    return manifest_info

def generate_lua_script(config_path, key_vdf_path, output_dir):
    """生成Lua脚本文件"""
    # 读取config.json
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    app_id = config.get('appId')
    depots = config.get('depots', [])
    dlcs = config.get('dlcs', [])
    
    # 生成以appid为文件名的lua文件路径
    output_path = os.path.join(output_dir, f"{app_id}.lua")
    
    # 获取密钥信息
    depot_keys = parse_key_vdf(key_vdf_path)
    
    # 获取manifest信息
    manifest_info = find_manifest_files(os.path.dirname(config_path))
    
    # 生成Lua脚本
    with open(output_path, 'w') as f:
        # 添加主应用ID
        f.write(f"addappid({app_id})\n\n")
        
        # 添加depot信息
        for depot_id in depots:
            depot_id_str = str(depot_id)
            
            if depot_id_str in depot_keys:
                key = depot_keys[depot_id_str]
                f.write(f'addappid({depot_id_str}, 0, "{key}") -- 设置manifest ID\n')
            else:
                f.write(f'addappid({depot_id_str})\n')
            
            if depot_id_str in manifest_info:
                manifest_id = manifest_info[depot_id_str]
                f.write(f"setmanifestid({depot_id_str}, {manifest_id})\n\n")
            else:
                f.write("\n")
        
        # 添加DLC信息
        for dlc_id in dlcs:
            dlc_id_str = str(dlc_id)
            
            if dlc_id_str in manifest_info:
                manifest_id = manifest_info[dlc_id_str]
                
                if dlc_id_str in depot_keys:
                    key = depot_keys[dlc_id_str]
                    f.write(f'addappid({dlc_id_str}, 0, "{key}")\n')
                else:
                    f.write(f'addappid({dlc_id_str})\n')
                
                f.write(f"setmanifestid({dlc_id_str}, {manifest_id})\n\n")
            else:
                f.write(f"addappid({dlc_id_str})\n\n")
            
    print(f"Lua脚本已生成到: {output_path}")
    return app_id

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='生成Steam下载用的Lua脚本')
    parser.add_argument('-d', '--dir', dest='directory', 
                        help='指定包含manifest和配置文件的目录 (默认为当前目录)')
    args = parser.parse_args()
    
    # 确定工作目录
    work_dir = args.directory if args.directory else os.path.dirname(os.path.abspath(__file__)) or "."
    output_dir = work_dir
    
    # 确保目录存在
    if not os.path.exists(work_dir):
        print(f"错误：指定的目录 '{work_dir}' 不存在")
        exit(1)
        
    # 设置文件路径
    config_path = os.path.join(work_dir, "config.json")
    key_vdf_path = os.path.join(work_dir, "Key.vdf")
    
    # 检查文件是否存在
    if not os.path.exists(config_path):
        print(f"错误：在 '{work_dir}' 中找不到 config.json 文件")
        exit(1)
    
    if not os.path.exists(key_vdf_path):
        print(f"错误：在 '{work_dir}' 中找不到 Key.vdf 文件")
        exit(1)
    
    # 生成Lua脚本
    app_id = generate_lua_script(config_path, key_vdf_path, output_dir)
    print(f"已创建 {app_id}.lua 文件") 