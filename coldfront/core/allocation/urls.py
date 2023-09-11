from django.urls import path

import coldfront.core.allocation.views as allocation_views

urlpatterns = [
    path('', allocation_views.AllocationListView.as_view(), name='allocation-list'),
    path('project/<int:project_pk>/create',
         allocation_views.AllocationCreateView.as_view(), name='allocation-create'),
    path('<int:pk>/', allocation_views.AllocationDetailView.as_view(),
         name='allocation-detail'),
    path('change-request/<int:pk>/', allocation_views.AllocationChangeDetailView.as_view(),
         name='allocation-change-detail'),
    path('<int:pk>/activate-request', allocation_views.AllocationActivateRequestView.as_view(),
         name='allocation-activate-request'),
    path('<int:pk>/deny-request', allocation_views.AllocationDenyRequestView.as_view(),
         name='allocation-deny-request'),
    path('<int:pk>/activate-change-request', allocation_views.AllocationChangeActivateView.as_view(),
         name='allocation-activate-change'),
    path('<int:pk>/deny-change-request', allocation_views.AllocationChangeDenyView.as_view(),
         name='allocation-deny-change'),
    path('<int:pk>/delete-attribute-change', allocation_views.AllocationChangeDeleteAttributeView.as_view(),
         name='allocation-attribute-change-delete'),
    path('<int:pk>/add-users', allocation_views.AllocationAddUsersView.as_view(),
         name='allocation-add-users'),
    path('<int:pk>/remove-users', allocation_views.AllocationRemoveUsersView.as_view(),
         name='allocation-remove-users'),
    path('request-list', allocation_views.AllocationRequestListView.as_view(),
         name='allocation-request-list'),
    path('change-list', allocation_views.AllocationChangeListView.as_view(),
         name='allocation-change-list'),
    path('<int:pk>/renew', allocation_views.AllocationRenewView.as_view(),
         name='allocation-renew'),
    path('<int:pk>/allocationattribute/add',
         allocation_views.AllocationAttributeCreateView.as_view(), name='allocation-attribute-add'),
    path('<int:pk>/change-request',
         allocation_views.AllocationChangeView.as_view(), name='allocation-change'),
    path('<int:pk>/allocationattribute/delete',
         allocation_views.AllocationAttributeDeleteView.as_view(), name='allocation-attribute-delete'),
    path('<int:pk>/allocationattribute/update',
         allocation_views.AllocationAttributeUpdateView.as_view(), name='allocation-attribute-update'),
    path('<int:pk>/allocationnote/add',
         allocation_views.AllocationNoteCreateView.as_view(), name='allocation-note-add'),
    path('<int:allocation_pk>/allocationnote/<int:pk>/update',
         allocation_views.AllocationNoteUpdateView.as_view(), name='allocation-note-update'),
    path('allocation-invoice-list', allocation_views.AllocationInvoiceListView.as_view(),
         name='allocation-invoice-list'),
    path('allocation-all-invoices-list', allocation_views.AllocationAllInvoicesListView.as_view(),
         name='allocation-all-invoices-list'),
    path('<int:pk>/allocation-all-invoices-detail', allocation_views.AllocationAllInvoicesDetailView.as_view(),
         name='allocation-all-invoices-detail'),
    path('<int:pk>/invoice/', allocation_views.AllocationInvoiceDetailView.as_view(),
         name='allocation-invoice-detail'),
    path('allocation/<int:pk>/add-invoice-note',
         allocation_views.AllocationAddInvoiceNoteView.as_view(), name='allocation-add-invoice-note'),
    path('allocation-invoice-note/<int:pk>/update',
         allocation_views.AllocationUpdateInvoiceNoteView.as_view(), name='allocation-update-invoice-note'),
    path('allocation/<int:pk>/invoice/delete/',
         allocation_views.AllocationDeleteInvoiceNoteView.as_view(), name='allocation-delete-invoice-note'),
    path('add-allocation-account/', allocation_views.AllocationAccountCreateView.as_view(),
         name='add-allocation-account'),
    path('allocation-account-list/', allocation_views.AllocationAccountListView.as_view(),
         name='allocation-account-list'),
    path('invoice-export/', allocation_views.AllocationInvoiceExportView.as_view(),
         name='invoice-export'),
    path('all-invoices-export/', allocation_views.AllocationAllInvoicesExportView.as_view(),
         name='all-invoices-export'),
    path('allocation-user-request-list', allocation_views.AllocationUserRequestListView.as_view(),
         name='allocation-user-request-list'),
    path('allocation-user/<int:pk>/approve', allocation_views.AllocationUserApproveRequestView.as_view(),
         name='allocation-user-approve-request'),
    path('allocation-user/<int:pk>/deny', allocation_views.AllocationUserDenyRequestView.as_view(),
         name='allocation-user-deny-request'),
    path('allocation-user/<int:pk>/info', allocation_views.AllocationUserRequestInfoView.as_view(),
         name='allocation-user-request-info'),
    path('allocation-export/', allocation_views.AllocationExportView.as_view(),
         name='allocation-export'),
    path('<int:pk>/allocation-remove/', allocation_views.AllocationRemoveView.as_view(),
         name='allocation-remove'),
    path('removal-list/', allocation_views.AllocationRemovalListView.as_view(),
         name='allocation-removal-request-list'),
    path('<int:pk>/allocation-approve-removal/', allocation_views.AllocationApproveRemovalRequestView.as_view(),
         name='allocation-approve-removal-request'),
    path('<int:pk>/allocation-deny-removal/', allocation_views.AllocationDenyRemovalRequestView.as_view(),
         name='allocation-deny-removal-request')
]
