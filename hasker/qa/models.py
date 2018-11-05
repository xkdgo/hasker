from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from pytils.translit import translify
from taggit.managers import TaggableManager


class QuestAns(models.Model):
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    rating = models.IntegerField(default=0)

    def likeup(self):
        self.rating += 1
        super().save()

    def likedown(self):
        self.rating -= 1
        super().save()

    class Meta:
        abstract = True


class Question(QuestAns):
    STATUS_CHOICES = (
        ('unanswered', 'Unanswered'),
        ('answered', 'Answered'),
    )
    title = models.CharField(max_length=100, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='q_activity')
    slug = models.SlugField(max_length=100,
                            unique_for_date='date_posted')
    status = models.CharField(max_length=10,
                              choices=STATUS_CHOICES,
                              default='unanswered')
    tags = TaggableManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('question-detail', kwargs={'slug': self.slug,
                                                  "pk": self.pk
                                                  })

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(translify(self.title))
        super(Question, self).save(*args, **kwargs)

    def toggle_status(self):
        if self.status == 'unanswered':
            self.status = 'answered'
        else:
            self.status = 'unanswered'
        self.save()

    def set_answered(self):
        self.status = 'answered'
        self.save()


class Answer(QuestAns):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='a_activity')
    question = models.ForeignKey(Question,
                                 on_delete=models.CASCADE,
                                 related_name='answers')
    right_answer = models.BooleanField(default=False)

    class Meta:
        ordering = ('date_posted',)

    def __str__(self):
        return 'Answered by	{} on {}'.format(self.author, self.question)

    def set_best(self):
        self.right_answer = True
        super().save()

    def unset_best(self):
        self.right_answer = False
        super().save()


class LikeAbstract(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class LikeQuestion(LikeAbstract):
    like_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='ques_likes')


class DisLikeQuestion(LikeAbstract):
    dislike_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='ques_dislikes')


class LikeAnswer(LikeAbstract):
    like_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='ans_likes')


class DisLikeAnswer(LikeAbstract):
    dislike_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='ans_dislikes')
