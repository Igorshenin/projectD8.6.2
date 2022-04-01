from django.shortcuts import render
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView # импортируем уже знакомый generic
from django.core.paginator import Paginator  # импортируем класс, позволяющий удобно осуществлять постраничный вывод
from django.shortcuts import redirect
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Post, Category, Author
from .filters import PostFilter  # импортируем недавно написанный фильтр
from .forms import PostForm


# Create your views here.

class PostListView(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'news'
    ordering = ['-created']
    paginate_by = 10  # поставим постраничный вывод в один элемент

    def get_context_data(self,
                         **kwargs):  # забираем отфильтрованные объекты переопределяя метод
                                     # get_context_data у наследуемого класса (привет, полиморфизм,
                                     # мы скучали!!!)
        context = super().get_context_data(**kwargs)
        context['filter'] = PostFilter(self.request.GET,
                                          queryset=self.get_queryset())  # вписываем наш фильтр
                                                                         # в контекст
        context['categories'] = Category.objects.all()
        context['form'] = PostForm()

        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)  # создаём новую форму, забиваем в неё данные из POST-запроса

        if form.is_valid():  # если пользователь ввёл всё правильно и нигде не ошибся, то сохраняем новый товар
            form.save()

        return super().get(request, *args, **kwargs)

class NewDetail(DetailView):
    model = Post  # модель всё та же, но мы хотим получать детали новости
    template_name = 'new.html'  # название шаблона будет new.html
    queryset = Post.objects.all()

class PostCreateView(CreateView):
    template_name = 'news_create.html'
    form_class = PostForm
    permission_required = ('news.add_post',)

    def get(self, request, *args, **kwargs):
        author = Author.objects.get(user=self.request.user)
        now = datetime.now()
        today = now.date()
        count_post = Post.objects.filter(author=author, created__gte=today).count()
        print(count_post)
        if count_post >= 3:
            raise PermissionDenied("Вы не можете оставлять более 3 статей в день!")
        self.object = None
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        author = Author.objects.get(user=self.request.user)
        today = datetime.today().date()
        count_post = Post.objects.filter(author=author, created__gte=today).count()
        print(count_post)
        if count_post >= 3:
            raise PermissionDenied("Вы не можете оставлять более 3 статей в день!")
        self.object = None
        return super().post(request, *args, **kwargs)



# дженерик для редактирования объекта
class PostUpdateView(UpdateView):
    template_name = 'news_update.html'
    form_class = PostForm
    permission_required = ('news.change_post',)

    # метод get_object мы используем вместо queryset, чтобы получить информацию об объекте, который мы собираемся редактировать
    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)


# дженерик для удаления товара
class PostDeleteView(DeleteView):
    template_name = 'news_delete.html'
    queryset = Post.objects.all()
    success_url = '/news/'

    def get_object(self, **kwargs):
        author = Post.objects.get(pk=self.kwargs.get('pk')).author.user
        user = User.objects.get(username=self.request.user)
        if user != author:
            raise PermissionDenied
        return Post.objects.get(pk=self.kwargs.get('pk'))

@login_required
def upgrade_me(request):
    user = request.user
    author_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        author_group.user_set.add(user)
    if not Author.objects.filter(user=user).exists():
        Author.objects.create(user=user)
    return redirect('/')