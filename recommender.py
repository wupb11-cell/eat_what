import sqlite3
import json
import random
from datetime import datetime, timedelta
from dateutil.parser import parse

class RecipeRecommender:
    def __init__(self, db_path='eatwhat.db'):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_all_recipes(self, category=None, limit=None):
        conn = self.get_connection()
        c = conn.cursor()

        if category:
            c.execute('SELECT * FROM recipes WHERE category = ? ORDER BY gi_value ASC', (category,))
        else:
            c.execute('SELECT * FROM recipes ORDER BY gi_value ASC')

        recipes = []
        for row in c.fetchall():
            recipes.append(self._row_to_dict(row))

        conn.close()
        return recipes[:limit] if limit else recipes

    def _row_to_dict(self, row):
        return {
            'id': row[0],
            'name': row[1],
            'category': row[2],
            'ingredients': json.loads(row[3]) if isinstance(row[3], str) else row[3],
            'steps': json.loads(row[4]) if isinstance(row[4], str) else row[4],
            'cost': row[5],
            'difficulty': row[6],
            'gi_value': row[7],
            'cook_time': row[8],
            'nutrition_tags': json.loads(row[9]) if isinstance(row[9], str) else (row[9] or []),
            'season': row[10],
            'calories': row[11] if len(row) > 11 else 0,
            'protein': row[12] if len(row) > 12 else 0,
            'carbs': row[13] if len(row) > 13 else 0,
            'fat': row[14] if len(row) > 14 else 0,
            'fiber': row[15] if len(row) > 15 else 0
        }

    def get_recipes_by_category(self, category, limit=20):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM recipes
            WHERE category = ? AND gi_value < 55 AND difficulty <= 3
            ORDER BY RANDOM()
            LIMIT ?
        ''', (category, limit))

        recipes = [self._row_to_dict(row) for row in c.fetchall()]
        conn.close()
        return recipes

    def get_recipes_by_day(self, day_of_week):
        conn = self.get_connection()
        c = conn.cursor()

        season_map = {
            0: 'spring', 1: 'spring', 2: 'summer', 3: 'summer',
            4: 'autumn', 5: 'autumn', 6: 'winter'
        }
        season = season_map.get(day_of_week, 'all')

        c.execute('''
            SELECT * FROM recipes
            WHERE (season = ? OR season = 'all')
            AND gi_value < 55 AND difficulty <= 3
            ORDER BY RANDOM()
            LIMIT 10
        ''', (season,))

        recipes = [self._row_to_dict(row) for row in c.fetchall()]
        conn.close()
        return recipes

    def get_user_preferences(self, openid):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT preferences FROM users WHERE openid = ?', (openid,))
        result = c.fetchone()
        conn.close()

        if result and result[0]:
            return json.loads(result[0])
        return {}

    def get_user_settings(self, openid):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT settings FROM users WHERE openid = ?', (openid,))
        result = c.fetchone()
        conn.close()

        if result and result[0]:
            return json.loads(result[0])
        return {}

    def generate_weekly_menu(self, start_date=None, openid=None):
        if start_date is None:
            today = datetime.now()
            days_until_sunday = (6 - today.weekday()) % 7
            if days_until_sunday == 0:
                days_until_sunday = 7
            start_date = today + timedelta(days=days_until_sunday)

        preferences = {}
        if openid:
            preferences = self.get_user_preferences(openid)

        weekly_menu = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': (start_date + timedelta(days=6)).strftime('%Y-%m-%d'),
            'days': [],
            'total_nutrition': {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0,
                'gi_avg': 0
            }
        }

        used_recipe_ids = set()

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_of_week = current_date.weekday()

            day_menu = {
                'date': current_date.strftime('%Y-%m-%d'),
                'day_name': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][day_of_week],
                'meals': {},
                'day_nutrition': {
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'fiber': 0
                }
            }

            for meal_type in ['breakfast', 'lunch', 'dinner']:
                available_recipes = [
                    r for r in self.get_recipes_by_day(day_of_week)
                    if r['id'] not in used_recipe_ids and r['category'] == meal_type
                ]

                if not available_recipes:
                    available_recipes = [
                        r for r in self.get_recipes_by_category(meal_type)
                        if r['category'] == meal_type
                    ]

                available_recipes = self._filter_by_preferences(available_recipes, preferences)

                if available_recipes:
                    recipe = random.choice(available_recipes)
                    used_recipe_ids.add(recipe['id'])
                    day_menu['meals'][meal_type] = recipe

                    day_menu['day_nutrition']['calories'] += recipe.get('calories', 0)
                    day_menu['day_nutrition']['protein'] += recipe.get('protein', 0)
                    day_menu['day_nutrition']['carbs'] += recipe.get('carbs', 0)
                    day_menu['day_nutrition']['fat'] += recipe.get('fat', 0)
                    day_menu['day_nutrition']['fiber'] += recipe.get('fiber', 0)

            weekly_menu['days'].append(day_menu)

            weekly_menu['total_nutrition']['calories'] += day_menu['day_nutrition']['calories']
            weekly_menu['total_nutrition']['protein'] += day_menu['day_nutrition']['protein']
            weekly_menu['total_nutrition']['carbs'] += day_menu['day_nutrition']['carbs']
            weekly_menu['total_nutrition']['fat'] += day_menu['day_nutrition']['fat']
            weekly_menu['total_nutrition']['fiber'] += day_menu['day_nutrition']['fiber']

        gi_values = []
        for day in weekly_menu['days']:
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type in day['meals']:
                    gi_values.append(day['meals'][meal_type]['gi_value'])

        if gi_values:
            weekly_menu['total_nutrition']['gi_avg'] = round(sum(gi_values) / len(gi_values), 1)

        return weekly_menu

    def _filter_by_preferences(self, recipes, preferences):
        if not preferences:
            return recipes

        filtered = []
        for recipe in recipes:
            include = True

            if 'avoid_tags' in preferences:
                recipe_tags = recipe.get('nutrition_tags', [])
                for tag in preferences['avoid_tags']:
                    if tag in recipe_tags:
                        include = False
                        break

            if 'prefer_tags' in preferences and include:
                recipe_tags = recipe.get('nutrition_tags', [])
                if preferences['prefer_tags']:
                    if not any(tag in recipe_tags for tag in preferences['prefer_tags']):
                        include = False

            if include:
                filtered.append(recipe)

        return filtered if filtered else recipes

    def format_menu_message(self, weekly_menu):
        message = f"🍽️ 下周饮食推荐\n"
        message += f"📅 {weekly_menu['start_date']} 至 {weekly_menu['end_date']}\n\n"

        day_icons = {'breakfast': '🌅', 'lunch': '🌞', 'dinner': '🌙'}
        day_names = {'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐'}

        for day in weekly_menu['days']:
            message += f"【{day['day_name']}】\n"
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type in day['meals']:
                    recipe = day['meals'][meal_type]
                    icon = day_icons[meal_type]
                    gi_status = "✅" if recipe['gi_value'] < 55 else ""
                    message += f"{icon} {day_names[meal_type]}：{recipe['name']}\n"
                    message += f"   💰{recipe['cost']}元 | ⏱️{recipe['cook_time']}分钟 | "
                    message += f"GI:{recipe['gi_value']} {gi_status}\n"
            message += "\n"

        nutrition = weekly_menu.get('total_nutrition', {})
        message += "📊 本周营养总览：\n"
        message += f"   热量：{nutrition.get('calories', 0)}kcal\n"
        message += f"   蛋白质：{nutrition.get('protein', 0)}g\n"
        message += f"   碳水：{nutrition.get('carbs', 0)}g\n"
        message += f"   脂肪：{nutrition.get('fat', 0)}g\n"
        message += f"   纤维：{nutrition.get('fiber', 0)}g\n"
        message += f"   平均GI：{nutrition.get('gi_avg', 0)}\n\n"

        message += "🛒 采购清单：点击获取本周食材购买链接\n"
        message += "回复「今日菜谱」获取当天详细做法\n"
        message += "回复「帮助」查看更多功能\n"

        return message

    def get_recipe_detail(self, recipe_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        recipe = self._row_to_dict(row)

        detail = f"🍳 {recipe['name']}\n"
        detail += f"📂 分类：{recipe['category']}\n"
        detail += f"💰 成本：{recipe['cost']}元\n"
        detail += f"⏱️ 耗时：{recipe['cook_time']}分钟\n"
        detail += f"🔥 难度：{'⭐' * recipe['difficulty']}\n"
        detail += f"📉 GI值：{recipe['gi_value']}\n"
        detail += f"🏷️ 标签：{', '.join(recipe['nutrition_tags'])}\n\n"

        detail += "📝 食材清单：\n"
        for ing in recipe['ingredients']:
            detail += f"• {ing}\n"

        detail += "\n👩‍🍳 做法步骤：\n"
        for i, step in enumerate(recipe['steps'], 1):
            detail += f"{i}. {step}\n"

        detail += "\n📊 营养成分（每份）：\n"
        detail += f"   热量：{recipe.get('calories', 0)}kcal\n"
        detail += f"   蛋白质：{recipe.get('protein', 0)}g\n"
        detail += f"   碳水：{recipe.get('carbs', 0)}g\n"
        detail += f"   脂肪：{recipe.get('fat', 0)}g\n"
        detail += f"   纤维：{recipe.get('fiber', 0)}g\n"

        return detail

    def get_all_ingredients_for_week(self, weekly_menu):
        all_ingredients = {}

        for day in weekly_menu['days']:
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type in day['meals']:
                    recipe = day['meals'][meal_type]
                    for ing in recipe['ingredients']:
                        name, amount = ing.rsplit(':', 1) if ':' in ing else (ing, '适量')
                        name = name.strip()
                        if name in all_ingredients:
                            all_ingredients[name]['count'] += 1
                            all_ingredients[name]['recipes'].append(recipe['name'])
                        else:
                            all_ingredients[name] = {
                                'amount': amount.strip(),
                                'count': 1,
                                'recipes': [recipe['name']]
                            }

        return all_ingredients

    def calculate_daily_nutrition(self, weekly_menu, day_index):
        if day_index < 0 or day_index >= len(weekly_menu['days']):
            return None

        day = weekly_menu['days'][day_index]
        nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'gi_values': []
        }

        for meal_type in ['breakfast', 'lunch', 'dinner']:
            if meal_type in day['meals']:
                recipe = day['meals'][meal_type]
                nutrition['calories'] += recipe.get('calories', 0)
                nutrition['protein'] += recipe.get('protein', 0)
                nutrition['carbs'] += recipe.get('carbs', 0)
                nutrition['fat'] += recipe.get('fat', 0)
                nutrition['fiber'] += recipe.get('fiber', 0)
                nutrition['gi_values'].append(recipe.get('gi_value', 0))

        if nutrition['gi_values']:
            nutrition['gi_avg'] = round(sum(nutrition['gi_values']) / len(nutrition['gi_values']), 1)
        else:
            nutrition['gi_avg'] = 0

        return nutrition

    def get_nutrition_analysis(self, weekly_menu):
        daily_nutritions = []
        for i in range(7):
            daily_nutritions.append(self.calculate_daily_nutrition(weekly_menu, i))

        analysis = {
            'daily': daily_nutritions,
            'weekly_total': weekly_menu.get('total_nutrition', {}),
            'daily_avg': {
                'calories': round(sum(d['calories'] for d in daily_nutritions) / 7, 1),
                'protein': round(sum(d['protein'] for d in daily_nutritions) / 7, 1),
                'carbs': round(sum(d['carbs'] for d in daily_nutritions) / 7, 1),
                'fat': round(sum(d['fat'] for d in daily_nutritions) / 7, 1),
                'fiber': round(sum(d['fiber'] for d in daily_nutritions) / 7, 1),
                'gi_avg': round(sum(d['gi_avg'] for d in daily_nutritions if d['gi_avg']) / 7, 1)
            },
            'recommendations': self._generate_nutrition_recommendations(daily_nutritions)
        }

        return analysis

    def _generate_nutrition_recommendations(self, daily_nutritions):
        recommendations = []

        avg_calories = sum(d['calories'] for d in daily_nutritions) / 7
        if avg_calories < 1500:
            recommendations.append({
                'type': 'warning',
                'message': '每日平均热量摄入偏低，建议适当增加食量'
            })
        elif avg_calories > 2500:
            recommendations.append({
                'type': 'warning',
                'message': '每日平均热量摄入偏高，建议减少高热量食物'
            })

        avg_protein = sum(d['protein'] for d in daily_nutritions) / 7
        if avg_protein < 50:
            recommendations.append({
                'type': 'info',
                'message': '蛋白质摄入略低，建议增加肉类、蛋类、豆制品'
            })

        avg_fiber = sum(d['fiber'] for d in daily_nutritions) / 7
        if avg_fiber < 20:
            recommendations.append({
                'type': 'success',
                'message': '纤维摄入良好，继续保持多吃蔬菜的习惯'
            })

        avg_gi = sum(d['gi_avg'] for d in daily_nutritions if d['gi_avg']) / 7
        if avg_gi < 55:
            recommendations.append({
                'type': 'success',
                'message': f'平均GI值{avg_gi}，非常适合控制血糖'
            })

        return recommendations

if __name__ == '__main__':
    recommender = RecipeRecommender()
    menu = recommender.generate_weekly_menu()
    print(recommender.format_menu_message(menu))

    analysis = recommender.get_nutrition_analysis(menu)
    print("\n📊 营养分析：")
    print(json.dumps(analysis, ensure_ascii=False, indent=2))