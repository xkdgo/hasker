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
from taggit.models import Tag
from .forms import (
    AnswerForm,
    QuestionForm,
    QuestionFormUpdate
)
from functools import reduce
import operator


class QuestionListView(ListView):
    model = Question
    template_name = 'hasker/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'questions'
    ordering = ['-date_posted']
    paginate_by = 2

    def get(self, request, *args, **kwargs):
        self.tag_slug = kwargs.get("tag_slug", None)
        return super().get(self, request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        self.tag = None
        if self.tag_slug:
            self.tag = get_object_or_404(Tag, slug=self.tag_slug)
            queryset = queryset.filter(tags__in=[self.tag])
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.tag:
            context['tag'] = self.tag
        return context


class SearchQuestionListView(ListView):
    model = Question
    template_name = 'hasker/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'questions'
    ordering = ['-date_posted']
    paginate_by = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_condition = "icontains"
        self.int_query_fields = []
        self.query_fields = ["%s__%s" % (f.name, self.query_condition)
                             for f in self.model._meta.fields
                             if (isinstance(f, models.CharField) or
                                 isinstance(f, models.TextField))]

    def get_Q(self, query_list):
        """
        Prepare Q statement for query
        """

        def get_q(f):
            if "__" not in f:
                return "%s__%s" % (f, self.query_condition)
            else:
                return f

        # Next statement combines two solutions
        # first: find word in any char field an text field
        # q = reduce(lambda x, y: x | Q(**{get_q(y): query}),
        #            self.query_fields[1:],
        #            Q(**{get_q(self.query_fields[0]): query}))

        # second: find all of list's words in any char field an text field
        # query_list = query.split()
        # result = result.filter(
        #     reduce(operator.and_,
        #            (Q(title__icontains=q) for q in query_list)) |
        #     reduce(operator.and_,
        #            (Q(content__icontains=q) for q in query_list))
        # )

        q = reduce(lambda x, y: x | reduce(operator.and_,
                   (Q(**{get_q(y): query}) for query in query_list)), self.query_fields[1:],
                   reduce(operator.and_,
                          (Q(**{get_q(self.query_fields[0]): query}) for query in query_list))
                   )

        if self.int_query_fields and isinstance(query_list[0], int):
            v = int(query_list[0])
            for f in self.int_query_fields:
                q |= Q(**{f: v})
        return q

    def get_queryset(self):
        search_term = ''
        if 'navsearch' in self.request.GET:
            search_term = self.request.GET['navsearch']
            if not search_term.startswith("tag:"):
                # search in text and char field of model
                query_list = search_term.split()
                if search_term and self.query_fields:
                    return self.model.objects.filter(self.get_Q(query_list)).order_by('-rating', '-date_posted')
                else:
                    messages.warning(self.request, f"Nothing finded for {search_term}")
                    return super().get_queryset()
            # search by tags tag: tag1 tag2
            # remove tag: keyword from query
            query_tag_name_list = search_term[4:].split()
            queryset = super().get_queryset()
            try:
                tag_obj_list = [get_object_or_404(Tag, name=tag_name) for tag_name in query_tag_name_list]
            except Http404:
                messages.warning(self.request, f"Nothing finded for {search_term}")
                return super().get_queryset()
            tag_obj_list = list(set(tag_obj_list))
            queryset = queryset.filter(tags__in=tag_obj_list).distinct()
            return queryset
        # if empty search
        messages.warning(self.request, f"Nothing finded for {search_term}")
        return super().get_queryset()


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
    form_class = QuestionForm

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
    form_class = QuestionFormUpdate

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
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])
        mark_model, like_method = self.get_mark_model_method(self.kwargs['vote'])
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
