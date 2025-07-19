from django.urls import path , include
from . import views



urlpatterns = [
    path('' , views.loginpage , name='loginpage' ),
    path('logout' , views.logoutuser , name='logoutuser' ),
    path('home' , views.homepage , name='home_page' ),
    #user
    path('add-new-user/' , views.create_user , name='create_user'),
    path('submituserdata' , views.submituserdata , name='submituserdata'),
    path('uers-list' , views.user_list , name='users_list'),
    path('fetch-users' , views.fetchUsers , name='fetch_users'),
    path('edit-user/<int:userid>/', views.editUsers, name='edit_users'),
    path('change_user_password' , views.chageUserPassword , name='chageUserPassword'),
    path('add-new-project' , views.addNewProject , name='addNewProject'),

    path('submitProject' , views.submitProject , name='submitProject'),
    path('project-list' , views.projectlist , name='projectlist'),
    path('fetch-project' , views.fetchProject , name='fetch_project'),
    path('edit-project/<int:proid>/', views.editProject, name='edit_project'),
    path('update-project-status/', views.updateProjectStatus, name='update_project_status'),
    path('assign-member/', views.assingmember, name='assign_member'),

    ##projects
    path('fetch-project-users-task/', views.fetchProjectAndUsers, name='fetch_project_users_task'),
    path('assingmembersubmit/', views.assingmembersubmit, name='assingmembersubmit'),
    path('project-details/<int:proid>', views.projectdtails, name='project_details'),
    path('my-project/' , views.memberproject , name='member_project'),
    path('fetch-member-project/' , views.fetchmemberProject , name='fetch_member_project'),


    path('remove-project-memeber', views.removeProjectMemeber, name='remove_project_memeber'),
    path('add-new-task', views.addNewTask, name='add_new_task'),
    path('fetch-task', views.fetchTask, name='fetch_task'),
    path('fetch-project-users', views.fetchProjectUsers, name='fetch_project_users'),
    path('submit-task', views.submittask, name='submittask'),
    path('update-task-status', views.updateTaskStatus, name='update_task_status'),
    path('remove-task', views.removeTask, name='remove_task'),
    path('task-details/<int:taskid>', views.taskdetails, name='task_details'),
    path('task-chart/', views.taskchart, name='taskchart'),


    path('submit-comment', views.submitComment, name='submit_comment'),
    path('profile', views.profileview, name='profile_view'),
    path('changepersonalpassword', views.changepersonalpassword, name='changepersonalpassword'),

    #email part
    path('email-inbox', views.emailbox, name='emailbox'),
    path('fetch-email-inbox-detail', views.fetchemailinboxdetail, name='fetch_emai_inbox_detail'),
    path('email_compose', views.emailcompose, name='email_compose'),
    path('summernote/', include('django_summernote.urls')),
    
    ## activyt log
     path('activity-log', views.activitylog, name='activity_log'),
     path('fetch-activity-log' , views.fetchactivitylog , name="fetch_activity_log")
    
]


# 
