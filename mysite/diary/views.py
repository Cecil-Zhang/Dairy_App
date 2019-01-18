from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import ModelForm
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from .serializers import DiarySerializer
from .models import Diary
import logging
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('dairy.users.views')

@api_view(['GET', 'POST'])
@login_required
def diary_list(request):
    # logger.debug(repr(DiarySerializer()))
    user_id = request.user.id
    if request.method == 'GET':
        diaries = Diary.objects.all().filter(author=user_id).order_by('-datetime')
        if request.GET.get('year', '') != '':
            diaries = diaries.filter(year=request.GET.get('year'))
        if request.GET.get('month', '') != '':
            logger.debug('month={}'.format(request.GET.get('month')))
            diaries = diaries.filter(month=request.GET.get('month'))
        if request.GET.get('search', '') != '':
            diaries = diaries.filter(content__icontains=request.GET.get('search'))
        page = request.GET.get('page')
        if page is None:
            serializer = DiarySerializer(diaries, many=True)
        else:
            years = Diary.objects.all().values('year').distinct()
            paginator = Paginator(diaries, request.GET.get('page_size', 10))
            serializer = DiarySerializer(paginator.page(page), many=True)
        return JsonResponse({
            'data': serializer.data,
            'num_pages': paginator.num_pages,
            'years': list(years)
            }, safe=False)

    elif request.method == 'POST':
        data = request.data
        data['author'] = request.user.id
        serializer = DiarySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
@login_required
def diary_detail(request, pk):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        diary = Diary.objects.get(pk=pk)
    except Diary.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = DiarySerializer(diary)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        serializer = DiarySerializer(diary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        diary.delete()
        return HttpResponse(status=204)

@api_view(['POST'])
@login_required
def write_dairy(request):
    if request.method == 'POST':
        form = DiaryForm(request.POST)
        if form.is_valid():
            model_instance = form.save(commit=False)
            now = timezone.now()
            model_instance.datetime = now
            model_instance.year = now.year
            model_instance.month = now.month
            model_instance.day = now.day
            model_instance.save()
            return redirect('diary:index')
