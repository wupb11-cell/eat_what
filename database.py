import json
import os
from datetime import datetime, timedelta

RECIPES_FILE = 'recipes_data.json'
MENUS_FILE = 'menus_data.json'
USERS_FILE = 'users_data.json'

def get_default_recipes():
    return [
        {
            "id": 1, "name": "小米粥", "category": "breakfast",
            "ingredients": ["小米:50g", "水:500ml", "枸杞:5g"],
            "steps": ["小米洗净备用", "锅中加水烧开", "放入小米大火煮开", "转小火熬20分钟", "加入枸杞即可"],
            "cost": 5.0, "difficulty": 1, "gi_value": 55, "cook_time": 25,
            "nutrition_tags": ["低GI", "养胃", "简单"], "season": "all",
            "calories": 180, "protein": 5.0, "carbs": 38.0, "fat": 1.5, "fiber": 2.0
        },
        {
            "id": 2, "name": "鸡蛋燕麦粥", "category": "breakfast",
            "ingredients": ["燕麦:40g", "鸡蛋:1个", "牛奶:200ml", "蜂蜜:5g"],
            "steps": ["燕麦加水煮开", "打入鸡蛋搅拌", "加入牛奶稍煮", "关火后加蜂蜜"],
            "cost": 8.0, "difficulty": 1, "gi_value": 42, "cook_time": 15,
            "nutrition_tags": ["低GI", "高蛋白", "减脂"], "season": "all",
            "calories": 280, "protein": 15.0, "carbs": 35.0, "fat": 8.0, "fiber": 4.0
        },
        {
            "id": 3, "name": "全麦三明治", "category": "breakfast",
            "ingredients": ["全麦面包:2片", "鸡蛋:1个", "生菜:2片", "番茄:半个"],
            "steps": ["鸡蛋煎熟", "番茄切片", "面包依次放生菜、番茄、鸡蛋", "合上面包即可"],
            "cost": 6.0, "difficulty": 1, "gi_value": 45, "cook_time": 10,
            "nutrition_tags": ["低GI", "高纤维", "快捷"], "season": "all",
            "calories": 220, "protein": 12.0, "carbs": 28.0, "fat": 8.0, "fiber": 5.0
        },
        {
            "id": 4, "name": "玉米糊", "category": "breakfast",
            "ingredients": ["玉米面:30g", "水:300ml", "盐:1g"],
            "steps": ["玉米面加水调匀", "锅中烧水", "倒入玉米面水不停搅拌", "煮开即可"],
            "cost": 3.0, "difficulty": 1, "gi_value": 48, "cook_time": 10,
            "nutrition_tags": ["低GI", "粗粮", "简单"], "season": "all",
            "calories": 120, "protein": 3.0, "carbs": 25.0, "fat": 1.0, "fiber": 2.0
        },
        {
            "id": 5, "name": "菠菜鸡蛋汤", "category": "breakfast",
            "ingredients": ["菠菜:100g", "鸡蛋:1个", "盐:2g", "香油:3ml"],
            "steps": ["菠菜洗净切段", "锅中烧水", "水开打入鸡蛋", "放入菠菜煮沸", "加盐香油调味"],
            "cost": 5.0, "difficulty": 1, "gi_value": 15, "cook_time": 10,
            "nutrition_tags": ["低GI", "富含铁", "清爽"], "season": "all",
            "calories": 130, "protein": 10.0, "carbs": 5.0, "fat": 8.0, "fiber": 3.0
        },
        {
            "id": 6, "name": "番茄炒蛋", "category": "lunch",
            "ingredients": ["番茄:2个", "鸡蛋:2个", "油:10ml", "盐:2g", "糖:3g"],
            "steps": ["番茄切块", "鸡蛋打散加少许盐", "热油炒鸡蛋盛出", "另起油炒番茄出汁", "加入鸡蛋翻炒", "加盐糖调味"],
            "cost": 10.0, "difficulty": 1, "gi_value": 20, "cook_time": 15,
            "nutrition_tags": ["低GI", "维C丰富", "家常"], "season": "all",
            "calories": 220, "protein": 14.0, "carbs": 15.0, "fat": 12.0, "fiber": 3.0
        },
        {
            "id": 7, "name": "清炒西兰花", "category": "lunch",
            "ingredients": ["西兰花:200g", "蒜:3瓣", "油:10ml", "盐:2g"],
            "steps": ["西兰花切小朵洗净", "蒜切末", "热油爆香蒜末", "放入西兰花翻炒", "加少许水焖煮", "加盐调味"],
            "cost": 8.0, "difficulty": 1, "gi_value": 15, "cook_time": 12,
            "nutrition_tags": ["低GI", "高纤维", "抗癌"], "season": "all",
            "calories": 150, "protein": 6.0, "carbs": 12.0, "fat": 9.0, "fiber": 6.0
        },
        {
            "id": 8, "name": "糙米饭", "category": "lunch",
            "ingredients": ["糙米:100g", "水:200ml"],
            "steps": ["糙米提前浸泡2小时", "放入电饭煲", "加水煮熟"],
            "cost": 4.0, "difficulty": 1, "gi_value": 50, "cook_time": 45,
            "nutrition_tags": ["低GI", "粗粮", "饱腹"], "season": "all",
            "calories": 180, "protein": 4.0, "carbs": 38.0, "fat": 1.5, "fiber": 3.5
        },
        {
            "id": 9, "name": "鸡胸肉沙拉", "category": "lunch",
            "ingredients": ["鸡胸肉:100g", "生菜:50g", "黄瓜:50g", "番茄:50g", "橄榄油:5ml", "柠檬汁:10ml"],
            "steps": ["鸡胸肉煮熟撕成丝", "生菜黄瓜番茄洗净切好", "混合蔬菜和鸡肉", "淋上橄榄油柠檬汁"],
            "cost": 18.0, "difficulty": 2, "gi_value": 20, "cook_time": 20,
            "nutrition_tags": ["低GI", "高蛋白", "减脂", "清爽"], "season": "summer",
            "calories": 250, "protein": 32.0, "carbs": 10.0, "fat": 10.0, "fiber": 4.0
        },
        {
            "id": 10, "name": "红烧豆腐", "category": "lunch",
            "ingredients": ["豆腐:200g", "生抽:10ml", "糖:5g", "葱:5g", "油:10ml"],
            "steps": ["豆腐切块", "热油煎至两面金黄", "加生抽糖调味", "加水焖煮", "撒葱花出锅"],
            "cost": 8.0, "difficulty": 2, "gi_value": 15, "cook_time": 20,
            "nutrition_tags": ["低GI", "植物蛋白", "补钙"], "season": "all",
            "calories": 200, "protein": 15.0, "carbs": 12.0, "fat": 10.0, "fiber": 2.0
        },
        {
            "id": 11, "name": "清蒸鲈鱼", "category": "dinner",
            "ingredients": ["鲈鱼:200g", "姜:5g", "葱:5g", "蒸鱼豉油:15ml"],
            "steps": ["鲈鱼洗净划刀", "姜丝葱段铺在鱼上", "大火蒸10分钟", "取出倒掉汤汁", "淋上蒸鱼豉油", "热油浇鱼"],
            "cost": 25.0, "difficulty": 2, "gi_value": 0, "cook_time": 15,
            "nutrition_tags": ["低GI", "高蛋白", "鲜嫩", "少油"], "season": "all",
            "calories": 180, "protein": 35.0, "carbs": 3.0, "fat": 4.0, "fiber": 0.5
        },
        {
            "id": 12, "name": "蒜蓉青菜", "category": "dinner",
            "ingredients": ["青菜:200g", "蒜:5g", "油:10ml", "盐:2g"],
            "steps": ["青菜洗净", "蒜切末", "热油爆香蒜末", "放入青菜大火翻炒", "加盐调味即可"],
            "cost": 5.0, "difficulty": 1, "gi_value": 15, "cook_time": 8,
            "nutrition_tags": ["低GI", "高纤维", "清爽", "简单"], "season": "all",
            "calories": 100, "protein": 3.0, "carbs": 8.0, "fat": 6.0, "fiber": 4.0
        },
        {
            "id": 13, "name": "紫薯粥", "category": "dinner",
            "ingredients": ["紫薯:100g", "大米:50g", "水:500ml"],
            "steps": ["紫薯去皮切块", "大米洗净", "一起放入锅中加水", "煮至粥稠即可"],
            "cost": 6.0, "difficulty": 1, "gi_value": 45, "cook_time": 40,
            "nutrition_tags": ["低GI", "花青素", "粗粮"], "season": "all",
            "calories": 200, "protein": 4.0, "carbs": 45.0, "fat": 1.0, "fiber": 3.0
        },
        {
            "id": 14, "name": "凉拌黄瓜", "category": "dinner",
            "ingredients": ["黄瓜:200g", "蒜:3g", "醋:10ml", "香油:3ml", "盐:2g"],
            "steps": ["黄瓜拍碎切块", "蒜切末", "加醋香油盐拌匀", "冰箱冷藏10分钟味道更佳"],
            "cost": 4.0, "difficulty": 1, "gi_value": 10, "cook_time": 10,
            "nutrition_tags": ["低GI", "解暑", "爽口", "简单"], "season": "summer",
            "calories": 80, "protein": 2.0, "carbs": 6.0, "fat": 4.0, "fiber": 2.0
        },
        {
            "id": 15, "name": "番茄鸡蛋面", "category": "dinner",
            "ingredients": ["番茄:1个", "鸡蛋:1个", "面条:80g", "葱:3g", "盐:2g"],
            "steps": ["番茄切块", "鸡蛋打散", "煮面条至八成熟", "另起锅炒番茄鸡蛋", "加水煮开", "放入面条撒葱花"],
            "cost": 10.0, "difficulty": 1, "gi_value": 30, "cook_time": 20,
            "nutrition_tags": ["低GI", "快捷", "家常"], "season": "all",
            "calories": 320, "protein": 14.0, "carbs": 48.0, "fat": 8.0, "fiber": 3.0
        },
        {
            "id": 16, "name": "虾仁豆腐羹", "category": "dinner",
            "ingredients": ["虾仁:50g", "豆腐:100g", "鸡蛋:1个", "葱:3g", "盐:2g", "淀粉:5g"],
            "steps": ["虾仁洗净", "豆腐切块", "锅中加水烧开", "放入虾仁豆腐", "鸡蛋打散倒入", "水淀粉勾芡", "加盐葱花调味"],
            "cost": 15.0, "difficulty": 2, "gi_value": 15, "cook_time": 15,
            "nutrition_tags": ["低GI", "高蛋白", "补钙", "鲜美"], "season": "all",
            "calories": 200, "protein": 22.0, "carbs": 8.0, "fat": 9.0, "fiber": 1.0
        },
        {
            "id": 17, "name": "清炒藕片", "category": "dinner",
            "ingredients": ["莲藕:150g", "蒜:3g", "葱:3g", "油:10ml", "盐:2g", "醋:5ml"],
            "steps": ["莲藕去皮切片", "泡水中防氧化", "热油爆香蒜葱", "捞出藕片翻炒", "加醋盐调味", "快速出锅保持脆感"],
            "cost": 8.0, "difficulty": 1, "gi_value": 30, "cook_time": 10,
            "nutrition_tags": ["低GI", "清热", "爽脆"], "season": "summer",
            "calories": 140, "protein": 3.0, "carbs": 22.0, "fat": 5.0, "fiber": 3.0
        },
        {
            "id": 18, "name": "木耳炒肉", "category": "dinner",
            "ingredients": ["木耳:50g", "瘦肉:100g", "青椒:50g", "蒜:3g", "油:10ml", "盐:2g"],
            "steps": ["木耳泡发撕小朵", "瘦肉切片", "青椒切块", "热油炒肉片", "加木耳青椒翻炒", "加盐调味"],
            "cost": 15.0, "difficulty": 1, "gi_value": 25, "cook_time": 15,
            "nutrition_tags": ["低GI", "补铁", "清血管"], "season": "all",
            "calories": 220, "protein": 20.0, "carbs": 10.0, "fat": 12.0, "fiber": 5.0
        },
        {
            "id": 19, "name": "薏米红豆粥", "category": "breakfast",
            "ingredients": ["薏米:30g", "红豆:30g", "水:600ml", "冰糖:10g"],
            "steps": ["薏米红豆提前浸泡4小时", "放入锅中加水", "大火煮开转小火", "熬至软烂加冰糖"],
            "cost": 8.0, "difficulty": 1, "gi_value": 40, "cook_time": 60,
            "nutrition_tags": ["低GI", "祛湿", "美容", "粗粮"], "season": "all",
            "calories": 220, "protein": 8.0, "carbs": 42.0, "fat": 2.0, "fiber": 5.0
        },
        {
            "id": 20, "name": "蒸蛋羹", "category": "breakfast",
            "ingredients": ["鸡蛋:2个", "温水:150ml", "盐:2g", "生抽:3ml", "香油:2ml"],
            "steps": ["鸡蛋打散", "加温水盐搅匀", "撇去泡沫", "盖保鲜膜", "上锅蒸10分钟", "淋生抽香油"],
            "cost": 4.0, "difficulty": 1, "gi_value": 10, "cook_time": 15,
            "nutrition_tags": ["低GI", "高蛋白", "嫩滑", "易消化"], "season": "all",
            "calories": 150, "protein": 14.0, "carbs": 3.0, "fat": 9.0, "fiber": 0.0
        }
    ]

def load_recipes():
    if os.path.exists(RECIPES_FILE):
        with open(RECIPES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        recipes = get_default_recipes()
        save_recipes(recipes)
        return recipes

def save_recipes(recipes):
    with open(RECIPES_FILE, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

def load_menus():
    if os.path.exists(MENUS_FILE):
        with open(MENUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_menus(menus):
    with open(MENUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(menus, f, ensure_ascii=False, indent=2)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def init_db():
    load_recipes()
    load_menus()
    load_users()

if __name__ == '__main__':
    init_db()
    print("数据库初始化完成！")
