from django.shortcuts import render,get_object_or_404
from .models import Blog,Group_blog,Meta_tag
from django.views import View
from django.core.paginator import Paginator

# Create your views here.

# show all blog in main page
class Show_All_blog(View):
    def get(self,request,*args, **kwargs):
        blogs = Blog.objects.filter(is_active = True).order_by('-register_data')[:10]
        return render(request,'blog_app/blog_main.html',{'blogs':blogs})


# show detail blog
class Blog_detail(View):
    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']

        # واکشی مقاله اصلی
        blog = get_object_or_404(Blog, slug=slug)

        blog.view+=1
        blog.save()

        # واکشی مقالات مرتبط با گروه مقاله اصلی
        related_articles = Blog.objects.filter(grop_blog=blog.grop_blog).exclude(id=blog.id)

        # واکشی مقالات فعال بر اساس تعداد ویو
        blog_pop = Blog.objects.filter(is_active=True).order_by('view')

        # واکشی تمام دسته‌بندی‌ها و مقالات مرتبط با هر دسته‌بندی
        categories = Group_blog.objects.filter(is_active=True).prefetch_related('group_of_blog')
        meta_tag = Meta_tag.objects.filter(blog = blog).first()


        context = {
            'blog': blog,
            'related_articles': related_articles,
            'popular_blog': blog_pop,
            'categories': categories,
            'meta_tag':meta_tag
        }

        return render(request, 'blog_app/blog.html', context)


# blog in all blog
class BlogsView(View):
    def get(self, request, *args, **kwargs):
        # دریافت تمام بلاگ‌های فعال
        blogs = Blog.objects.filter(is_active=True)

        # بررسی پارامتر sort
        sort = request.GET.get('sort')
        if sort == "1":  # جدیدترین
            blogs = blogs.order_by('-register_data')
        elif sort == "2":  # پربازدیدترین
            blogs = blogs.order_by('-view')

        # دریافت دسته‌بندی‌ها
        categories = Group_blog.objects.filter(is_active=True).prefetch_related('group_of_blog')


        # اعمال Pagination
        paginator = Paginator(blogs, 10)  # هر صفحه شامل 10 بلاگ باشد
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # ارسال داده‌ها به قالب
        return render(request, 'blog_app/blog_list.html', {

            'blogs':blogs,
            'page_obj': page_obj,
            'categories': categories,
            'sort': sort,  # ارسال پارامتر sort به قالب
        })



