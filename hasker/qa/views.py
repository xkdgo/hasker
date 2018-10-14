from django.shortcuts import (
    render,
    get_object_or_404,
    reverse,
    redirect,
    Http404,

)
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
)
from django.contrib.auth.decorators import login_required

from django.db import models
from .models import (
    Question,
    Answer,
    LikeQuestion,
    DisLikeQuestion,
    LikeAnswer,
    DisLikeAnswer,
)
from .forms import AnswerForm
from functools import reduce


class QuestionListView(ListView):
    model = Question
    template_name = 'hasker/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'questions'
    ordering = ['-date_posted']
    paginate_by = 5


class QuestionDetailViewGet(DetailView):
    model = Question

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        answers_list = context['object'].answers.all().order_by('date_posted').order_by('-rating')
        paginator = Paginator(answers_list, 5)  # Show 5 answers per page
        page = self.request.GET.get('page')
        context['answers_list'] = paginator.get_page(page)
        context['form'] = AnswerForm
        return context


class AddAnswer(SingleObjectMixin, FormView):
    template_name = 'qa/question_detail.html'
    form_class = AnswerForm
    model = Answer

    def post(self, request, *args, **kwargs):
        question = get_object_or_404(Question, pk=kwargs['pk'])
        form = self.form_class(request.POST)
        if question.answers.filter(author=request.user.id):
            messages.warning(request, f'You already answered this question')
            return HttpResponseRedirect(self.request.path_info)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.author = request.user
            answer.save()
            messages.success(request, f'Thank You for Answer')
            return HttpResponseRedirect(self.request.path_info)
        else:
            return HttpResponseRedirect(self.request.path_info)


class QuestionDetailView(View):

    def get(self, request, *args, **kwargs):
        view = QuestionDetailViewGet.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = AddAnswer.as_view()
        return view(request, *args, **kwargs)


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class QuestionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Question
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class QuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Question
    fields = ['content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        question = self.get_object()
        if self.request.user == question.author:
            return True
        return False


class VoteView(View):

    @transaction.atomic
    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            messages.warning(self.request, f'You need login to vote')
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])
        if self.kwargs['vote'] not in ('like', 'dislike'):
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])
        instance = get_object_or_404(self.get_instance_model(), pk=self.kwargs['pk'])
        if instance.author == self.request.user:
            messages.warning(self.request, f'You cant vote for your own')
            # return JsonResponse({'rating': instance.rating})
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])
        mark_model, like_method = self.get_mark_model_method(self.kwargs['vote'])
        print(mark_model, like_method)
        new_like_or_dislike, created = mark_model.objects.get_or_create(user=self.request.user,
                                                                        **self.like_procedure(
                                                                            self.kwargs['vote'], instance.id))
        if not created:
            # the user already liked this question before
            messages.warning(self.request, f"You already {self.kwargs['vote']}d this question")
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])
        else:
            like_method(instance)
            messages.success(self.request, f'Thank you for your vote')
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])

    @staticmethod
    def get_instance_model():
        raise NotImplementedError

    @staticmethod
    def get_mark_model_method(vote):
        raise NotImplementedError

    @staticmethod
    def like_procedure(vote, value):
        raise NotImplementedError


class QuestionVote(VoteView):

    @staticmethod
    def get_instance_model():
        return Question

    @staticmethod
    def get_mark_model_method(vote):
        if vote == 'like':
            return LikeQuestion, Question.likeup
        if vote == 'dislike':
            return DisLikeQuestion, Question.likedown

    @staticmethod
    def like_procedure(vote, value):
        if vote == 'like':
            return {"like_question_id": value}
        if vote == 'dislike':
            return {"dislike_question_id": value}


class AnswerVote(VoteView):

    @staticmethod
    def get_instance_model():
        return Answer

    @staticmethod
    def get_mark_model_method(vote):
        if vote == 'like':
            return LikeAnswer, Answer.likeup
        if vote == 'dislike':
            return DisLikeAnswer, Answer.likedown

    @staticmethod
    def like_procedure(vote, value):
        if vote == 'like':
            return {"like_answer_id": value}
        if vote == 'dislike':
            return {"dislike_answer_id": value}


class BestAnswer(View):
    @transaction.atomic
    def get(self, *args, **kwargs):
        answer_id = kwargs['pk']
        answer = Answer.objects.filter(pk=answer_id).first()
        if not answer.question.author == self.request.user:
            return HttpResponseForbidden()
        if not answer:
            return HttpResponseForbidden()
        try:
            prev_best = answer.question.answers.get(right_answer=True)
        except:
            self.set_best_status(answer)
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])
        if answer == prev_best:
            self.clear_best_status(answer)
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])
        else:
            prev_best.unset_best()
            self.set_best_status(answer)
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])

    @staticmethod
    def set_best_status(answer):
        answer.set_best()
        answer.question.set_answered()

    @staticmethod
    def clear_best_status(answer):
        answer.unset_best()
        answer.question.toggle_status()