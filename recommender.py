import json
import random
from datetime import datetime, timedelta
from database import load_recipes, load_menus, save_menus, load_users, save_users

class RecipeRecommender:
    def __init__(self):
        self.recipes = load_recipes()

    def get_all_recipes(self, category=None, limit=None):
        recipes = self.recipes
        if category:
            recipes = [r for r in recipes if r.get('category') == category]
        recipes.sort(key=lambda x: x.get('gi_value', 0))
        return recipes[:limit] if limit else recipes

    def get_recipes_by_category(self, category, limit=20):
        recipes = [r for r in self.recipes if r.get('category') == category and r.get('gi_value', 0) < 55 and r.get('difficulty', 0) <= 3]
        random.shuffle(recipes)
        return recipes[:limit]

    def get_recipes_by_day(self, day_of_week):
        season_map = {
            0: 'spring', 1: 'spring', 2: 'summer', 3: 'summer',
            4: 'autumn', 5: 'autumn', 6: 'winter'
        }
        season = season_map.get(day_of_week, 'all')

        recipes = [r for r in self.recipes
                   if (r.get('season') == season or r.get('season') == 'all')
                   and r.get('gi_value', 0) < 55
                   and r.get('difficulty', 0) <= 3]
        random.shuffle(recipes)
        return recipes[:10]

    def get_user_preferences(self, openid):
        users = load_users()
        for user in users:
            if user.get('openid') == openid:
                return user.get('preferences', {})
        return {}

    def get_user_settings(self, openid):
        users = load_users()
        for user in users:
            if user.get('openid') == openid:
                return user.get('settings', {})
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
                    if r['id'] not in used_recipe_ids and r.get('category') == meal_type
                ]

                if not available_recipes:
                    available_recipes = [
                        r for r in self.get_recipes_by_category(meal_type)
                        if r.get('category') == meal_type
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
                    gi_values.append(day['meals'][meal_type].get('gi_value', 0))

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

        return message

    def get_recipe_detail(self, recipe_id):
        for recipe in self.recipes:
            if recipe.get('id') == recipe_id:
                return recipe
        return None

    def get_all_ingredients_for_week(self, weekly_menu):
        all_ingredients = {}

        for day in weekly_menu['days']:
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type in day['meals']:
                    recipe = day['meals'][meal_type]
                    for ing in recipe.get('ingredients', []):
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

        return recommendations

if __name__ == '__main__':
    recommender = RecipeRecommender()
    menu = recommender.generate_weekly_menu()
    print(recommender.format_menu_message(menu))
