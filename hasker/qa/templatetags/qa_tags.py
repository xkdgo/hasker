from django import template
from django.conf import settings
from ..models import Question


register = template.Library()


@register.inclusion_tag('qa/popular_questions.html')
def show_trending():
    questions = Question.cust_objects.popular()[:settings.TRENDING_QUESTIONS_LIMIT]
    return {'questions': questions}

