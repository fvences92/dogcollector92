from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from .models import Dog, Toy, Photo
from .forms import FeedingForm
import boto3
import uuid


# environment variables
S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'dogcollector92'

# Create your views here.


def signup(request):
    # handle POST Requests (signing up)
    error_message = ''
    if request.method == 'POST':
        # <= fills out the form with the form values from the request
        form = UserCreationForm(request.POST)
        # validate form inputs
        if form.is_valid():
            # save the new user to the database
            user = form.save()
            # log the user in
            login(request, user)
            # redirect the user to the dogs index
            return redirect('index')
        else:
            # if the user form is invalid - show an error message
            error_message = 'invalid credentials - please try again'
    # handle GET Requests (navigating the user to the signup page)
    # present the user with a fresh signup form
    form = UserCreationForm()
    context = {'form': form, 'error': error_message}
    return render(request, 'registration/signup.html', context)


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


@login_required
def dogs_index(request):
    dogs = Dog.objects.filter(user=request.user)
    return render(request, 'dogs/index.html', {'dogs': dogs})

# update this view function


@login_required
def dogs_detail(request, dog_id):
    dog = Dog.objects.get(id=dog_id)
    if dog.user._id != request.user.id:
        return redirect('index')
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


@login_required
def add_feeding(request, dog_id):
    form = FeedingForm(request.POST)
    if form.is_valid():
        new_feeding = form.save(commit=False)
        new_feeding.dog_id = dog_id
        new_feeding.save()
    return redirect('detail', dog_id=dog_id)


@login_required
def assoc_toy(request, dog_id, toy_id):
    # Note that you can pass a toy's id instead of the whole object
    Dog.objects.get(id=dog_id).toys.add(toy_id)
    return redirect('detail', dog_id=dog_id)


@login_required
def add_photo(request, dog_id):
    photo_file = request.FILES.get('photo_file', None)
    if photo_file:
        s3 = boto3.client('s3', aws_access_key_id='AKIAX2O3MLQNO7TM7M64',
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
    fields = ('name', 'breed', 'description', 'age')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    # success_url = '/dogs/'


class DogUpdate(LoginRequiredMixin, UpdateView):
    model = Dog
    fields = ('breed', 'description', 'age')


class DogDelete(LoginRequiredMixin, DeleteView):
    model = Dog
    success_url = '/dogs/'


class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = ('name', 'color')


class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    fields = ('name', 'color')


class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'


class ToyDetail(LoginRequiredMixin, DetailView):
    model = Toy
    template_name = 'toys/detail.html'


class ToyList(LoginRequiredMixin, ListView):
    model = Toy
    template_name = 'toys/index.html'
