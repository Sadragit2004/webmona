from django.shortcuts import render
import web.settings as sett
from .models import TextImageBlock
# Create your views here.




def media_admin(request):

    context = {
        'media_url':sett.MEDIA_URL
    }

    return context



def main(request):

    return render(request,'main_app/main.html')



def main_content_view(request):
    contents = TextImageBlock.objects.all()
    return render(request, 'main_app/main_content.html', {'text_image_blocks': contents})