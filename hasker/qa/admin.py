from django.contrib import admin
from .models import (
    Answer, Question,
    LikeQuestion, DisLikeQuestion,
    LikeAnswer, DisLikeAnswer,
)

admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(LikeAnswer)
admin.site.register(DisLikeAnswer)
admin.site.register(LikeQuestion)
admin.site.register(DisLikeQuestion)
