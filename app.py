from flask import Flask, request, jsonify
import sqlite3
import json
import requests
from datetime import datetime
from recommender import RecipeRecommender

app = Flask(__name__)
recommender = RecipeRecommender()

WECHAT_APPID = 'wxd62492c53c19438c'
WECHAT_APPSECRET = 'a2b5c47646887bc09885e34578bab6e9'

def init_database():
    from database import init_db
    init_db()

init_database()

def get_db():
    return sqlite3.connect('eatwhat.db')

@app.route('/')
def index():
    return 'EatWhat 饮食推荐助手 - 小程序后端API'

@app.route('/api/login', methods=['POST'])
def login():
    code = request.json.get('code')

    if not code:
        return jsonify({'success': False, 'message': '缺少code参数'})

    url = f'https://api.weixin.qq.com/sns/jscode2session?appid={WECHAT_APPID}&secret={WECHAT_APPSECRET}&js_code={code}&grant_type=authorization_code'

    try:
        response = requests.get(url)
        data = response.json()

        if 'openid' in data:
            openid = data['openid']
            save_user(openid)
            return jsonify({
                'success': True,
                'openid': openid
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取openid失败',
                'error': data
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        })

def save_user(openid):
    db = get_db()
    c = db.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (openid, created_at, updated_at)
        VALUES (?, datetime('now'), datetime('now'))
    ''', (openid,))
    db.commit()
    db.close()

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    openid = request.args.get('openid')

    if not openid:
        return jsonify({'success': False, 'message': '缺少openid'})

    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT nickname, avatar_url, settings, preferences, subscribed, created_at
        FROM users WHERE openid = ?
    ''', (openid,))
    result = c.fetchone()
    db.close()

    if not result:
        return jsonify({'success': False, 'message': '用户不存在'})

    return jsonify({
        'success': True,
        'data': {
            'nickname': result[0] or '',
            'avatar_url': result[1] or '',
            'settings': json.loads(result[2]) if result[2] else {},
            'preferences': json.loads(result[3]) if result[3] else {},
            'subscribed': result[4] == 1,
            'created_at': result[5]
        }
    })

@app.route('/api/user/settings', methods=['POST'])
def update_settings():
    data = request.json
    openid = data.get('openid')
    settings = data.get('settings', {})

    if not openid:
        return jsonify({'success': False, 'message': '缺少openid'})

    db = get_db()
    c = db.cursor()
    c.execute('''
        UPDATE users
        SET settings = ?, updated_at = datetime('now')
        WHERE openid = ?
    ''', (json.dumps(settings), openid))
    db.commit()
    db.close()

    return jsonify({'success': True, 'message': '设置已更新'})

@app.route('/api/user/preferences', methods=['POST'])
def update_preferences():
    data = request.json
    openid = data.get('openid')
    preferences = data.get('preferences', {})

    if not openid:
        return jsonify({'success': False, 'message': '缺少openid'})

    db = get_db()
    c = db.cursor()
    c.execute('''
        UPDATE users
        SET preferences = ?, updated_at = datetime('now')
        WHERE openid = ?
    ''', (json.dumps(preferences), openid))
    db.commit()
    db.close()

    return jsonify({'success': True, 'message': '偏好已更新'})

@app.route('/api/user/subscribe', methods=['POST'])
def subscribe_message():
    data = request.json
    openid = data.get('openid')
    enabled = data.get('enabled', True)

    if not openid:
        return jsonify({'success': False, 'message': '缺少openid'})

    db = get_db()
    c = db.cursor()
    c.execute('''
        UPDATE users
        SET subscribed = ?, updated_at = datetime('now')
        WHERE openid = ?
    ''', (1 if enabled else 0, openid))
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'message': '订阅设置已更新'
    })

@app.route('/api/weekly_menu', methods=['GET'])
def get_weekly_menu():
    openid = request.args.get('openid')

    menu = recommender.generate_weekly_menu(openid=openid)
    save_menu(menu)

    return jsonify({
        'success': True,
        'data': menu
    })

@app.route('/api/today_menu', methods=['GET'])
def get_today_menu():
    openid = request.args.get('openid')
    today = datetime.now().strftime('%Y-%m-%d')

    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT menu_data FROM weekly_menus
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY created_at DESC LIMIT 1
    ''', (today, today))
    result = c.fetchone()
    db.close()

    if result:
        menu_data = json.loads(result[0])
        for day in menu_data['days']:
            if day['date'] == today:
                return jsonify({
                    'success': True,
                    'data': day
                })

    menu = recommender.generate_weekly_menu(openid=openid)
    save_menu(menu)
    for day in menu['days']:
        if day['date'] == today:
            return jsonify({
                'success': True,
                'data': day
            })

    return jsonify({
        'success': False,
        'message': 'No menu found'
    })

@app.route('/api/recipe/<int:recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    recipe = recommender.get_recipe_detail(recipe_id)
    if recipe:
        return jsonify({
            'success': True,
            'data': recipe
        })
    return jsonify({
        'success': False,
        'message': 'Recipe not found'
    })

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    category = request.args.get('category')
    limit = request.args.get('limit', 20, type=int)

    recipes = recommender.get_recipes_by_category(category) if category else recommender.get_all_recipes(limit=limit)

    return jsonify({
        'success': True,
        'data': recipes
    })

@app.route('/api/purchase_list', methods=['GET'])
def get_purchase_list():
    today = datetime.now().strftime('%Y-%m-%d')

    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT menu_data FROM weekly_menus
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY created_at DESC LIMIT 1
    ''', (today, today))
    result = c.fetchone()
    db.close()

    if not result:
        return jsonify({
            'success': False,
            'message': 'No menu found'
        })

    menu_data = json.loads(result[0])
    ingredients = recommender.get_all_ingredients_for_week(menu_data)

    meituan_keywords = '+'.join(list(ingredients.keys())[:10])
    jd_keywords = '+'.join(list(ingredients.keys())[:10])

    return jsonify({
        'success': True,
        'data': {
            'ingredients': ingredients,
            'meituan_link': f'https://www.meituan.com/afood/search?keyword={meituan_keywords}',
            'jd_link': f'https://search.jd.com/Search?keyword={jd_keywords}&enc=utf-8'
        }
    })

@app.route('/api/nutrition_analysis', methods=['GET'])
def get_nutrition_analysis():
    today = datetime.now().strftime('%Y-%m-%d')

    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT menu_data FROM weekly_menus
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY created_at DESC LIMIT 1
    ''', (today, today))
    result = c.fetchone()
    db.close()

    if not result:
        menu = recommender.generate_weekly_menu()
        save_menu(menu)
        menu_data = menu
    else:
        menu_data = json.loads(result[0])

    analysis = recommender.get_nutrition_analysis(menu_data)

    return jsonify({
        'success': True,
        'data': analysis
    })

@app.route('/api/nutrition_today', methods=['GET'])
def get_nutrition_today():
    today = datetime.now().strftime('%Y-%m-%d')

    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT menu_data FROM weekly_menus
        WHERE start_date <= ? AND end_date >= ?
        ORDER BY created_at DESC LIMIT 1
    ''', (today, today))
    result = c.fetchone()
    db.close()

    if not result:
        return jsonify({
            'success': False,
            'message': 'No menu found'
        })

    menu_data = json.loads(result[0])

    day_index = None
    for i, day in enumerate(menu_data['days']):
        if day['date'] == today:
            day_index = i
            break

    if day_index is None:
        return jsonify({
            'success': False,
            'message': 'Today not in current menu week'
        })

    nutrition = recommender.calculate_daily_nutrition(menu_data, day_index)

    return jsonify({
        'success': True,
        'data': {
            'date': today,
            'nutrition': nutrition,
            'meals': menu_data['days'][day_index]['meals']
        }
    })

@app.route('/api/subscribe', methods=['POST'])
def handle_subscribe():
    openid = request.json.get('openid')

    if not openid:
        return jsonify({'success': False, 'message': '缺少openid'})

    return jsonify({
        'success': True,
        'message': '订阅消息功能已开启',
        'reminder': '每周日18:00会自动推送下周菜谱'
    })

def save_menu(menu):
    db = get_db()
    c = db.cursor()
    c.execute('''
        INSERT INTO weekly_menus (start_date, end_date, menu_data, created_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (menu['start_date'], menu['end_date'], json.dumps(menu, ensure_ascii=False)))
    db.commit()
    db.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("EatWhat 饮食推荐助手 - 小程序后端API")
    print("=" * 50)
    print("API接口列表：")
    print("  认证相关：")
    print("    - POST /api/login - 小程序登录")
    print("    - GET  /api/user/profile - 获取用户信息")
    print("    - POST /api/user/settings - 更新设置")
    print("    - POST /api/user/preferences - 更新偏好")
    print("    - POST /api/user/subscribe - 订阅消息设置")
    print("")
    print("  菜谱相关：")
    print("    - GET  /api/weekly_menu - 获取本周菜谱")
    print("    - GET  /api/today_menu - 获取今日菜谱")
    print("    - GET  /api/recipe/<id> - 获取菜谱详情")
    print("    - GET  /api/recipes - 获取菜谱列表")
    print("")
    print("  营养分析：")
    print("    - GET  /api/nutrition_analysis - 获取本周营养分析")
    print("    - GET  /api/nutrition_today - 获取今日营养摄入")
    print("")
    print("  采购相关：")
    print("    - GET  /api/purchase_list - 获取采购清单")
    print("")
    print("  其他：")
    print("    - GET  /api/health - 健康检查")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=True)
