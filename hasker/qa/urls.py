from django.urls import path
from .views import (
    QuestionCreateView,
    QuestionDetailView,
    QuestionListView,
    QuestionDeleteView,
    QuestionUpdateView,
    QuestionVote,
    AnswerVote,
    BestAnswer,
)

# from hasker.config import views as hasker_views


urlpatterns = [
    path('question/new', QuestionCreateView.as_view(), name='question-create'),
    path('question/<str:slug>/<int:pk>', QuestionDetailView.as_view(), name='question-detail'),
    path('question/<str:slug>/<int:pk>/delete', QuestionDeleteView.as_view(), name='question-delete'),
    path('question/<str:slug>/<int:pk>/update', QuestionUpdateView.as_view(), name='question-update'),
    path('question/<int:pk>/ld/<str:vote>', QuestionVote.as_view(), name='question-vote'),
    path('answer/<int:pk>/ld/<str:vote>', AnswerVote.as_view(), name='answer-vote'),
    path('answer/<int:pk>/best', BestAnswer.as_view(), name='answer-best'),
    path('', QuestionListView.as_view(template_name="hasker/home.html"), name='hasker-home'),
]
