#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
马里奥英语单词冒险游乐场 - 本地 PDF 单词自动提取工具
使用方式:
    1. 安装依赖: uv add pypdf
    2. 运行提取: uv run python scripts/extract_words.py <PDF文件路径> [难度级别 1或2]
"""

import sys
import os
import re
import json
import urllib.request
import urllib.parse

# 极简虚词过滤黑名单
STOPWORDS = {
    "the", "and", "you", "that", "was", "for", "are", "with", "his", "they", "this",
    "have", "from", "one", "had", "word", "but", "not", "what", "all", "were", "when",
    "your", "can", "said", "there", "use", "an", "each", "which", "she", "do", "how",
    "their", "if", "will", "up", "other", "about", "out", "many", "then", "them", "these",
    "so", "some", "her", "would", "make", "like", "him", "into", "time", "has", "look",
    "two", "more", "write", "go", "see", "number", "no", "way", "could", "people", "my",
    "than", "first", "been", "call", "who", "its", "now", "find", "long", "down", "day",
    "did", "get", "come", "made", "may", "part", "would", "about", "their", "into"
}

# 预设中小学常见高频词中英字典（在网络环境不可用时提供基础中文释义降级）
COMMON_DICT = {
    "apple": "苹果", "banana": "香蕉", "cat": "猫", "dog": "狗", "orange": "橙子",
    "school": "学校", "teacher": "老师", "student": "学生", "book": "书", "pen": "钢笔",
    "future": "未来", "adventure": "冒险", "challenge": "挑战", "science": "科学",
    "technology": "技术", "history": "历史", "beautiful": "美丽的", "nature": "大自然",
    "family": "家庭", "brother": "兄弟", "sister": "姐妹", "water": "水", "milk": "牛奶",
    "car": "小汽车", "bus": "公共汽车", "bike": "自行车", "plane": "飞机", "run": "跑/跑步"
}

def translate_word_online(word):
    """
    通过免费公共接口在线查词获取中文释义
    """
    # 尝试使用 MyMemory 免费查词接口
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(word)}&langpair=en|zh-CN"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and "responseData" in data and "translatedText" in data["responseData"]:
                trans = data["responseData"]["translatedText"].strip()
                # 过滤包含英文字母的翻译，确保翻译为纯中文
                if trans and not re.search('[a-zA-Z]', trans):
                    return trans
    except Exception as e:
        # 网络异常或接口超时
        pass
    
    # 降级查询本地字典
    return COMMON_DICT.get(word, "")

def extract_text_from_pdf(pdf_path):
    """
    使用 pypdf 提取 PDF 文字内容
    """
    try:
        import pypdf
    except ImportError:
        print("\n[错误] 未找到 pypdf 依赖，请先运行命令安装:")
        print("    uv add pypdf")
        sys.exit(1)
        
    print(f"正在读取并解析 PDF 文件: {pdf_path} ...")
    
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"[错误] 读取 PDF 失败: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("用法: uv run python scripts/extract_words.py <PDF路径> [难度: 1或2]")
        print("  1 - 小学难度 (默认)")
        print("  2 - 初中难度")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    
    level = 1
    if len(sys.argv) >= 3:
        try:
            level = int(sys.argv[2])
            if level not in [1, 2]:
                level = 1
        except ValueError:
            pass
            
    if not os.path.exists(pdf_path):
        print(f"[错误] 找不到指定的 PDF 文件: {pdf_path}")
        sys.exit(1)
        
    # 1. 提取文字
    raw_text = extract_text_from_pdf(pdf_path)
    
    # 2. 正则筛选出英文单词
    print("正在智能提取英文单词...")
    words = re.findall(r'\b[a-zA-Z]{3,15}\b', raw_text)
    
    # 3. 词汇去重和虚词清洗
    unique_words = sorted(list(set(w.lower() for w in words)))
    cleaned_words = [w for w in unique_words if w not in STOPWORDS]
    
    if not cleaned_words:
        print("[警告] 未能从教程文本中提取到任何有效的英文单词！")
        sys.exit(0)
        
    print(f"共检测出 {len(cleaned_words)} 个独立英文单词（已清洗虚词和介词）。")
    print("正在批量匹配释义与翻译（限制前40个高频词汇进行导入）...")
    
    # 限制每次批量导入不超过 40 个，防止接口限制
    target_words = cleaned_words[:40]
    
    words_data = []
    for idx, word in enumerate(target_words):
        print(f"[{idx+1}/{len(target_words)}] 翻译单词: {word} ...")
        cn = translate_word_online(word)
        if not cn:
            cn = "待编辑"
            
        words_data.append({
            "en": word,
            "cn": cn,
            "level": level,
            "example": f"This is a {word}."
        })
        
    # 4. 加载原有 data/words.json，进行合并去重
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    output_path = os.path.join(output_dir, "words.json")
    
    existing_words = []
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_words = existing_data.get("words", [])
        except Exception:
            pass
            
    # 合并（排除英文相同的重复词）
    newly_added = 0
    for new_w in words_data:
        if new_w["cn"] != "待编辑" and not any(ext_w["en"] == new_w["en"] for ext_w in existing_words):
            existing_words.append(new_w)
            newly_added += 1
            
    # 5. 保存数据
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"words": existing_words}, f, ensure_ascii=False, indent=2)
        print(f"\n[成功] 已将提取的单词更新至: {output_path}")
        print(f"本次新导入了 {newly_added} 个独立词汇，当前词库总词数: {len(existing_words)}")
    except Exception as e:
        print(f"[错误] 保存词库 JSON 失败: {e}")

if __name__ == "__main__":
    main()
