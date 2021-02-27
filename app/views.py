from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.urls.base import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from app import forms

from app.models import User, Event, Recipient, Idea

# Create your views here.

# Request Method Types

def home(request):
    if request.user.is_authenticated:
        events = Event.objects.exclude(members__id=request.user.id)
    else:
        events = Event.objects.all()
    context = {
        'events': events,
    }
    return render(request, 'app/home.html', context)

def register(request):
    if request.method == 'POST':
        form = forms.SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = forms.SignupForm()
    context = {
        'form': form,
    }
    return render(request, 'registration/register.html', context)
        
def event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.POST.get('delete'):
        event.delete()
        return redirect('home')
    context = {
        'event': event
    }
    return render(request, 'app/event.html', context)

def event_add_edit(request, pk=None):
    if pk:
        event = get_object_or_404(Event, pk=pk)
        if request.method == 'POST':
            form = forms.EventForm(request.POST, instance=event)
            if form.is_valid():
                form.save()
                messages.success(request, "Event saved.")
                return redirect('event', event.id)
        else:
            form = forms.EventForm(instance=event)
    else:
        if request.method == 'POST':
            form = forms.EventForm(request.POST)
            if form.is_valid:
                new_event = form.save(commit=False)
                new_event.organizer_id = request.user.id
                new_event.save()
                new_event.members.add(request.user)
                messages.success(request, "Event added.")
                return redirect('event', new_event.id)
        else:
            form = forms.EventForm()
    context = {
        'form': form
    }
    return render(request, 'app/event_add_edit.html', context)

@login_required
def event_membership(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.members.filter(id=request.user.id).exists():
        if request.user == event.organizer:
            messages.error(request, "You are the organizer, you cannot leave this event.")
            return redirect('event', pk)
        event.members.remove(request.user)
        return redirect('home')
    else:
        event.members.add(request.user)
        return redirect('event', pk)
    
def recipient(request, event_id, pk):
    recipient = get_object_or_404(Recipient, pk=pk)
    ideas = recipient.ideas.select_related('creator').all()

    context = {
        'recipient' : recipient,
        'ideas': ideas
    }
    return render(request, 'app/recipient.html', context)

def idea(request, event_id, recipient_id, pk):
    idea = get_object_or_404(Idea, pk=pk)
    context = {
        'idea' : idea
    }
    return render(request, 'app/idea.html', context)

def idea_add_edit(request, event_id, recipient_id, pk=None):
    idea = None

    if pk:
        idea = get_object_or_404(Idea, pk=pk)
        if request.method == 'POST':
            form = forms.IdeaForm(request.POST, instance=idea)
            if form.is_valid():
                form.save()
                messages.success(request, "Idea saved.")
                return redirect('recipient', event_id, recipient_id)
        else:
            form = forms.IdeaForm(instance=idea)
    else:
        if request.method == 'POST':
            form = forms.IdeaForm(request.POST)
            if form.is_valid:
                new_idea = form.save(commit=False)
                new_idea.recipient_id = recipient_id
                new_idea.save()
                messages.success(request, "Idea added.")
                return redirect('recipient', event_id, recipient_id)
        else:
            form = forms.IdeaForm()

    context = {
        'idea' : idea,
        'form': form,
        'back': reverse('recipient', args=[event_id, recipient_id])
    }
    return render(request, 'app/idea_add_edit.html', context)

# flag auto-add recipient when they join the group
# later add support for unsuspecting recipient
# 