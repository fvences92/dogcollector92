from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Dog, Toy, Photo
from .forms import FeedingForm
import uuid
import boto3

# environment variables
S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'dogcollector92'

# Create your views here.


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def dogs_index(request):
    dogs = Dog.objects.all()
    return render(request, 'dogs/index.html', {'dogs': dogs})

# update this view function


def dogs_detail(request, dog_id):
    dog = Dog.objects.get(id=dog_id)
    # instantiate FeedingForm to be rendered in the template
    feeding_form = FeedingForm()

    # displaying unassociated toys
    toys_dog_doesnt_have = Toy.objects.exclude(
        id__in=dog.toys.all().values_list('id'))

    return render(request, 'dogs/detail.html', {
        # include the dog and feeding_form in the context
        'dog': dog,
        'feeding_form': feeding_form,
        'toys': toys_dog_doesnt_have
    })


def add_feeding(request, dog_id):
    form = FeedingForm(request.POST)
    if form.is_valid():
        new_feeding = form.save(commit=False)
        new_feeding.dog_id = dog_id
        new_feeding.save()
    return redirect('detail', dog_id=dog_id)


def assoc_toy(request, dog_id, toy_id):
    # Note that you can pass a toy's id instead of the whole object
    Dog.objects.get(id=dog_id).toys.add(toy_id)
    return redirect('detail', dog_id=dog_id)


def add_photo(request, dog_id):
    photo_file = request.FILES.get('photo_file', None)
    if photo_file:
        s3 = boto3.client('s3', aws_access_key_id='AKIAX2O3MLQNKYYCPMUC',
                          aws_secret_access_key='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')
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # just in case something goes wrong
        try:
            s3.upload_fileobj(photo_file, BUCKET, key)
            # build the full url string
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            # we can assign to dog_id or dog (if you have a dog object)
            photo = Photo(url=url, dog_id=dog_id)
            photo.save()
        except Exception as error:
            print('***********************')
            print(error)
            print('An error occurred uploading file to S3')
            print('***********************')
    return redirect('detail', dog_id=dog_id)


class DogCreate(CreateView):
    model = Dog
    fields = '__all__'
    # success_url = '/dogs/'


class DogUpdate(UpdateView):
    model = Dog
    fields = ('breed', 'description', 'age')


class DogDelete(DeleteView):
    model = Dog
    success_url = '/dogs/'


class ToyCreate(CreateView):
    model = Toy
    fields = ('name', 'color')


class ToyUpdate(UpdateView):
    model = Toy
    fields = ('name', 'color')


class ToyDelete(DeleteView):
    model = Toy
    success_url = '/toys/'


class ToyDetail(DetailView):
    model = Toy
    template_name = 'toys/detail.html'


class ToyList(ListView):
    model = Toy
    template_name = 'toys/index.html'
