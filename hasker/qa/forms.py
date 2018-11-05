from django.forms import ModelForm
from .models import Answer, Question


class AnswerForm(ModelForm):
    class Meta:
        model = Answer
        fields = ['content']


class QuestionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['tags'].required = False

    class Meta:
        model = Question
        fields = ['title', 'content', 'tags']


class QuestionFormUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionFormUpdate, self).__init__(*args, **kwargs)
        self.fields['tags'].required = False

    class Meta:
        model = Question
        fields = ['content', 'tags']
