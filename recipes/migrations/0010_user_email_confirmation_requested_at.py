from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0009_recipe_calories_recipe_carbs_recipe_fats_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_confirmation_requested_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
