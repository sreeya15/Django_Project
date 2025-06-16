from django.urls import path
from . import views

urlpatterns = [
    path('', views.demand_list, name='demand_list'),
    path('add/', views.add_demand, name='add_demand'),
    path('edit/<int:demand_id>/', views.edit_demand, name='edit_demand'),
    path('delete/<int:demand_id>/', views.delete_demand, name='delete_demand'),
    path('update_stage/', views.update_stage, name='update_stage'),
    path('edit_stage_dates/', views.edit_stage_dates, name='edit_stage_dates'),
]

