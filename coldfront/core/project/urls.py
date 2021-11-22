from django.urls import path

import coldfront.core.project.views as project_views

urlpatterns = [
     path('<int:pk>/', project_views.ProjectDetailView.as_view(), name='project-detail'),
     path('<int:pk>/archive', project_views.ProjectArchiveProjectView.as_view(), name='project-archive'),
     path('', project_views.ProjectListView.as_view(), name='project-list'),
     path('project-user-update-email-notification/', project_views.project_update_email_notification, name='project-user-update-email-notification'),
     path('archived/', project_views.ProjectArchivedListView.as_view(), name='project-archived-list'),
     path('create/', project_views.ProjectCreateView.as_view(), name='project-create'),
     path('<int:pk>/update/', project_views.ProjectUpdateView.as_view(), name='project-update'),
     path('<int:pk>/add-users-search/', project_views.ProjectAddUsersSearchView.as_view(), name='project-add-users-search'),
     path('<int:pk>/add-users-search-results/', project_views.ProjectAddUsersSearchResultsView.as_view(), name='project-add-users-search-results'),
     path('<int:pk>/add-users/', project_views.ProjectAddUsersView.as_view(), name='project-add-users'),
     path('<int:pk>/remove-users/', project_views.ProjectRemoveUsersView.as_view(), name='project-remove-users'),
     path('<int:pk>/user-detail/<int:project_user_pk>', project_views.ProjectUserDetail.as_view(), name='project-user-detail'),
     path('<int:pk>/review/', project_views.ProjectReviewView.as_view(), name='project-review'),
     path('project-review-list', project_views.ProjectReviewListView.as_view(),name='project-review-list'),
     # path('project-review-complete/<int:project_review_pk>/', project_views.ProjectReviewCompleteView.as_view(),
     #      name='project-review-complete'),
     # path('project-review/<int:pk>/email', project_views.ProjectReivewEmailView.as_view(), name='project-review-email'),
     path('project-pi-list/', project_views.ProjectPISearchView.as_view(), name='project-pi-list'),
     path('project-send-access-request/', project_views.ProjectRequestAccessEmailView.as_view(),
          name='project-send-access-request'),
     path('<int:pk>/project-activate-request/', project_views.ProjectActivateRequestView.as_view(),
          name="project-activate-request"),
     path('<int:pk>/project-deny-request/', project_views.ProjectDenyRequestView.as_view(),
          name="project-deny-request"),
     path('project-review-approve/<int:pk>/', project_views.ProjectReviewApproveView.as_view(),
          name='project-review-approve'),
     path('project-review-deny/<int:pk>/', project_views.ProjectReviewDenyView.as_view(),
          name='project-review-deny'),
     path('project-review-info/<int:pk>/', project_views.ProjectReviewInfoView.as_view(),
          name='project-review-info')
]
