import json
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import ListView, UpdateView, DeleteView, FormView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from coldfront.plugins.announcements.models import Announcement, AnnouncementCategoryChoice, AnnouncementMailingListChoice, AnnouncementStatusChoice
from coldfront.plugins.announcements.forms import AnnouncementCreateForm, AnnouncementFilterForm


class AnnouncementListView(LoginRequiredMixin, TemplateView):
    template_name = 'announcements/announcement_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user
        context['categories'] = {category.pk: category.name for category in AnnouncementCategoryChoice.objects.all()}

        announcement_filter_form = AnnouncementFilterForm(self.request.GET)
        if not announcement_filter_form.is_valid():
            announcement_filter_form = AnnouncementFilterForm()

        context['filter_form'] = announcement_filter_form

        return context


class AnnouncementFilteredListView(LoginRequiredMixin, ListView):
    model=Announcement
    template_name = 'announcements/announcement_filtered.html'
    context_object_name = "announcements"
    paginate_by = 5

    def dispatch(self, request, *args, **kwargs):
        if request.META.get('HTTP_REFERER') is None:
            return HttpResponseNotFound(render(request, '404.html', {}))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        announcements = Announcement.objects.all().order_by('-created')

        announcement_filter_form = AnnouncementFilterForm(self.request.GET)
        if announcement_filter_form.is_valid():
            data = announcement_filter_form.cleaned_data
            if data.get('title'):
                announcements = announcements.filter(title__icontains=data.get('title'))
            if data.get('categories'):
                announcements = announcements.filter(categories__in=data.get('categories'))

        return announcements


class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = AnnouncementCreateForm
    template_name = "announcements/announcement_create_form.html"

    def test_func(self):
        if self.request.user.is_superuser:
            return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = {category.pk: category.name for category in AnnouncementCategoryChoice.objects.all()}
        context['mailing_lists'] = {mailing_list.pk: mailing_list.name for mailing_list in AnnouncementMailingListChoice.objects.all()}

        return context
    
    def form_valid(self, form):
        data = form.cleaned_data
        announcement_obj = Announcement.objects.create(
            title = data.get('title'),
            body = data.get('body'),
            status = AnnouncementStatusChoice.objects.get(name='Active'),
            details_url = data.get('details_url'),
        )

        announcement_obj.categories.set(data.get('categories'))
        announcement_obj.mailing_lists.set(data.get('mailing_lists'))


        if data.get('mailing_lists'):
            pass

        return super().form_valid(form)
    
    def get_success_url(self):
        msg = 'Announcement has been created.'
        messages.success(self.request, msg)
        return reverse('announcement-list') 


class AnnouncementUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Announcement
    fields = ['title', 'body', 'categories', 'mailing_lists', 'details_url']
    template_name_suffix='_update_form'

    def test_func(self):
        if self.request.user.is_superuser:
            return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcement_obj = get_object_or_404(Announcement, pk=self.kwargs.get('pk'))

        context['categories'] = {category.pk: category.name for category in AnnouncementCategoryChoice.objects.all()}
        context['initial_categories_selected'] = list(announcement_obj.categories.all().values_list('pk', flat=True))
        context['mailing_lists'] = {mailing_list.pk: mailing_list.name for mailing_list in AnnouncementMailingListChoice.objects.all()}
        context['initial_mailing_lists_selected'] = list(announcement_obj.mailing_lists.all().values_list('pk', flat=True))

        return context
    
    def get_success_url(self):
        return reverse('announcement-list')


class AnnouncementDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model=Announcement
    context_object_name = "announcement"

    def test_func(self):
        pk = self.kwargs.get('pk')
        announcement_obj = get_object_or_404(Announcement, pk=pk)

        if self.request.user.is_superuser:
            return True


class AnnouncementReadView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        if self.request.user.is_superuser:
            return True

    def get(self, request, *args, **kwargs):
        announcement_objs = Announcement.objects.filter(status__name='Active')
        for announcement_obj in announcement_objs:
            announcement_obj.viewed_by.add(request.user)
        return HttpResponseRedirect(reverse('announcement-list'))

    def post(self, request, *args, **kwargs):
        announcement_obj = Announcement.objects.get(pk=request.POST.get('id'))
        announcement_obj.viewed_by.add(request.user)
        return render(request, 'announcements/navbar_announcement_unread.html', {'user': self.request.user})
