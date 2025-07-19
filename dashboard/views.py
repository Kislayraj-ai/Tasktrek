from django.shortcuts import render , get_object_or_404 , redirect
from .models import Role , UserRole , Project , ProjectMember , Task , Comment , Notification , Activitylog
from pprint import pprint
from django.contrib.auth.hashers import make_password , check_password
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib import messages
from django.http import   JsonResponse , HttpResponse
import json
from pprint import pformat
from django.db.models import F
from django.contrib.auth import login as alogin , logout as alogout
from django.contrib.auth.forms import UserCreationForm , AuthenticationForm
from django.core.mail import send_mail , EmailMessage , EmailMultiAlternatives
from django.conf  import settings
import traceback
from .form import EmailForm
from datetime import date
from django.db.models.functions import TruncWeek
from django.db.models import Count

## from here the dashboard renders


#home page
def homepage(request):
    try:
        userid = request.user.id
        user = User.objects.get(id=userid)
        getrole = user.myuserrole.role.id
        
        unread = Notification.objects.filter(user=user).count()
        totalusers = User.objects.exclude(id=userid).count()

        totalproject_qs = Project.objects.all()
        task_qs = Task.objects.all()

        completed_tasks = 0
        pending_tasks = 0

        if getrole == 2:  # Manager
            manager_projects = totalproject_qs.filter(manager=user)
            totalproject = manager_projects.count()

            project_ids = manager_projects.values_list('id', flat=True)
            task_qs = task_qs.filter(project__in=project_ids)
            task = task_qs.count()

            completed_tasks = task_qs.filter(status="CP").count()
            pending_tasks = task_qs.filter(status__in=["HD", "IP"]).count()

        elif getrole == 3:
            member_project_ids = ProjectMember.objects.filter(user=user).values_list('project', flat=True)
            totalproject = totalproject_qs.filter(id__in=member_project_ids).count()
            task_qs = task_qs.filter(project__in=member_project_ids)
            task = task_qs.count()

            completed_tasks = task_qs.filter(status="CP").count()
            pending_tasks = task_qs.filter(status__in=["HD", "IP"]).count()

        else:  # Admin (role == 1)
            totalproject = totalproject_qs.count()
            task = task_qs.count()

            completed_tasks = task_qs.filter(status="CP").count()
            pending_tasks = task_qs.filter(status__in=["HD", "IP"]).count()

        return render(request, 'dashboard/index.html', {
            'unread': unread,
            'totalusers': totalusers,
            'totalproject': totalproject,
            'task': task,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks
        })

    except Exception as e:
        print("Error:", e)
        return render(request, 'dashboard/index.html')

def taskchart(request):
    try:
        data = (
            Task.objects.annotate(week=TruncWeek('created_at'))
            .values('week')
            .annotate(total=Count('id'))
            .order_by('week')
        )

        labels = [d['week'].strftime('%Y-%m-%d') for d in data]
        counts = [d['total'] for d in data]

        return JsonResponse({
            'labels': labels,
            'counts': counts
        })

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        return JsonResponse({'error': str(e)})


## EMAIl sending function
def send_custom_email(
    to_email,
    subject,
    message_text='',
    html_content=None,
    from_email=None,
    cc=None,
    bcc=None,
    attachments=None,
    request=None
):
    """
    Sends email with optional HTML, CC, BCC, and attachments.

    Parameters:
    - to_email: str or list of str
    - subject: str
    - message_text: fallback plain text
    - html_content: HTML version (optional)
    - from_email: optional override of sender
    - cc: list of emails (optional)
    - bcc: list of emails (optional)
    - attachments: list of tuples (filename, content, mimetype)
    - request: pass `request` only if you want to set messages
    """

    if isinstance(to_email, str):
        to_email = [to_email]

    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    try:
        email = EmailMessage(
            subject=subject,
            body=message_text,
            from_email=from_email,
            to=to_email,
            cc=cc,
            bcc=bcc,
        )

        if html_content:
            email.content_subtype = "html"
            email.body = html_content

        # Add attachments if any
        if attachments:
            for name, content, mimetype in attachments:
                email.attach(name, content, mimetype)

        email.send(fail_silently=False)

        # if request:
            # from django.contrib import messages
            # messages.success(request, "Email sent successfully.")

        return True

    except Exception as e:
        print("EMAIL SEND ERROR:", traceback.format_exc())
        if request:
            from django.contrib import messages
            messages.error(request, f"Email send failed: {e}")
        return False


def create_user(request):
    roles = Role.objects.all()
    # pprint(roles)
    return render(request , 'dashboard/create_user.html' , {'roles' : roles})

def submituserdata(request):
    try:
        if request.method == "POST":
            # print(request.POST)

            with transaction.atomic():

                
                name = request.POST.get('name')
                email = request.POST.get('email')
                password =  request.POST.get('password')
                phone = request.POST.get('phone')
                image = request.FILES.get('image')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                
                user =  User()
                user.username  = name
                user.first_name  = first_name
                user.last_name  = last_name
                user.email =  email
                user.password =  make_password(password)
                user.save()

                profile = user.profile
                profile.phone = phone
                profile.image = image
                profile.save()

                ## create user role
                userRole = UserRole()
                userRole.user  =  user
                userRole.role = Role.objects.get(id=request.POST.get('type'))
                userRole.save()


                ## get role
                role =  Role.objects.get(id=request.POST.get('type'))

                ## Log the activity
                Activitylog.objects.create(
                    user=user,
                    usertype= role.id ,
                    title="User created",
                    description=f"User created with username '{user.username}'."
                )

                ## now send notification to the user  here
                html_content = f"""
                    <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                        <h2>🎉 Congratulations!</h2>
                        <p>Your account has been <strong>successfully created</strong>.</p>

                        <p><strong>Username:</strong> {name}</p>
                        <p><strong>Password:</strong> {password}</p>
                        <p><strong>Role:</strong> {role.name}</p>

                        <p>You can now login using these credentials.</p>

                        <br>
                        <p>Regards,<br><strong>Team TrekTask</strong></p>
                    </div>
                """

                send_custom_email(
                    to_email=[email],
                    subject='Your Account Created!',
                    message_text='',
                    html_content=html_content,
                    from_email=settings.EMAIL_HOST_USER,
                    cc=[request.user.email],
                    request=request,
                )
                
                # ✅ Notification for the new user
                user_notification = Notification()
                user_notification.user = user
                user_notification.title = 'Account Created!'
                user_notification.detail = '''
                    🎉 Congratulations!
                    Your account has been successfully created.
                    <storng>Role:</strong> {role.name}
                    Please login using your credentials.
                '''
                user_notification.is_read=False
                user_notification.save()


                # ✅ Notification for the admin (create a new one)
                Notification.objects.create(
                    user=request.user,
                    title='New User Account Created!',
                    detail=f'''
                        A new user account has been created.<br>
                        <strong>Username:</strong> {name} and <storng>Role:</strong> {role.name}
                    ''' ,
                    is_read=False
                )
                


                messages.success(request ,'User Created Successfully')
                return redirect('create_user')


        messages.error(request, 'Invalid request method')
        return redirect('create_user')
    
    except Exception as e:
        # print(f"Error {e}")
        messages.error(request , f"Some Error Occurred :- {e}")
        return redirect('create_user')


def user_list(request):
    return render(request , 'dashboard/user_list.html')
    

def fetchUsers(request):

    userrole =  request.user.myuserrole.role.id
    rolesshow = []

    if userrole == 1:
        rolesshow = [1,2,3,4]
    else:
        rolesshow = [3,4]

    users = User.objects.exclude(id__in=[request.user.id]).filter(myuserrole__role__id__in=rolesshow).order_by('-id')
    
    data = []

    for user in  users:
        try:
            role_name =  user.myuserrole.role.name
        except:
            role_name = "N/A"

        
        try:
            phone = user.profile.phone
        except:
            phone = 'N/A'

        try:
            image_url = user.profile.image.url if user.profile.image else 'N/A'
        except:
            image_url = 'N/A'

        data.append({
                'userid' : user.id ,
                'username': user.username,
                'email': user.email,
                'role': role_name ,
                'first_name':  user.first_name or 'N/A',
                'last_name': user.last_name or '',
                'phone': phone,
                'image': image_url,
        })

    return JsonResponse({
        'data': data, 
        'success': True,
        'count': len(data)
    }, safe=False)

def editUsers(request , userid):
    user =  User.objects.get(id=userid)
    roles = Role.objects.all()

    if request.method == "POST" :
        try:
                # userid = request.POST.get('userid')
                name = request.POST.get('name')
                email = request.POST.get('email')
                type =  request.POST.get('type')
                phone = request.POST.get('phone')
                image = request.FILES.get('image')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')

                user =  User.objects.get(id=userid)
                user.username  = name
                user.email =  email
                user.first_name  = first_name
                user.last_name  = last_name
                user.save()

                profile = user.profile
                profile.phone = phone
                # profile.image = image
                if image:
                    profile.image = image
                profile.save()
                

                userrole = UserRole.objects.get(user_id=userid)
                userrole.role = Role.objects.get(id=type)
                userrole.save()

                ## activity log for user
                Activitylog.objects.create(
                    user=user,
                    usertype= int(type) ,
                    title="User updated",
                    description=f"User updated with username '{user.username}'."
                )


                messages.success(request ,'User Updated Successfully')
                return redirect('edit_users' , userid=userid)

        except Exception as e:
            messages.error(request , f"Some Error Occurred {e}")
            return redirect('edit_users' , userid=userid)

    return render(request , 'dashboard/edituser.html' , {'user' : user , 'roles' : roles })


def chageUserPassword(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            new_password = data.get("password")

            user = User.objects.get(id=user_id)
            user.password = make_password(new_password)
            user.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


### project management

def addNewProject(request):
    # getManager =  
    manager  = User.objects.filter(myuserrole__role__id=2)
    # print(manager)

    return render(request ,'dashboard/add_project.html' , {'manager' : manager})


def submitProject(request):
    try:
        if request.method == "POST":
            # print(request.POST)

            with transaction.atomic():
                name = request.POST.get('name')
                status = request.POST.get('status')
                manager =  request.POST.get('manager')
                detail =  request.POST.get('details')
                deadline =  request.POST.get('deadline')

                user =  User.objects.get(id=manager)

                project =  Project()
                project.name  = name
                project.status  = status
                project.manager  = user 
                project.details  = detail
                project.deadline  = deadline

                project.save()

                ## activity log for user
                # Activitylog.objects.create(
                #     user=user,
                #     usertype= user.myuserrole.role.id ,
                #     title="Project created",
                #     description=f"New Project created with name '{user.username}'."
                # )


                html_content = f"""
                    <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                        <h2>Dear {user.first_name} {user.last_name} !</h2>
                        <p>You have been assinged as an <strong>Manager</strong> to {name} project. </p>
                        <p>You can now login using these credentials.</p>
                        <br>
                        <p>Regards,<br><strong>Team TrekTask</strong></p>
                    </div>
                """
                
                send_custom_email(
                    to_email=[user.email],
                    subject='Project assinged !',
                    message_text='',
                    html_content=html_content,
                    from_email=settings.EMAIL_HOST_USER,
                    cc=[request.user.email],
                    request=request,
                )

                Notification.objects.create(
                    user= user ,
                    title='Project assinged !',
                    detail=f'''
                    You have been assinged as an <strong>Manager</strong> to {name} project.
                    ''' ,
                    is_read=False
                )

                Notification.objects.create(
                    user= request.user ,
                    title='New Project added !',
                    detail=f'''
                        New Project {name} has been added to the system for  {user.first_name} {user.last_name} .
                    ''' ,
                    is_read=False
                )
                

                messages.success(request ,'Project Created Successfully')
                return redirect('addNewProject')


        messages.error(request, 'Invalid request method')
        return redirect('addNewProject')
    
    except Exception as e:
        print(f"Error {e}")
        messages.error(request , "Some Error Occurred")
        return redirect('addNewProject')



def projectlist(request):
    return render(request , 'dashboard/project_list.html')


## fetch projects
def fetchProject(request):

    userrole =  request.user.myuserrole.role.id
    userid  = request.user.id
    projects = []
    data = []


    if userrole == 1:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(manager_id=userid)


    for pro in projects:
        print("project " , pro)
        try:
            manager = pro.manager.username
        except:
            manager = 'N/A'

        today = date.today()
        deadline = pro.deadline

        days_diff = (deadline - today).days
        due_by = ''

        if days_diff < 0:
            due_status = True
            due_by = f"Overdue by {abs(days_diff)} day(s)"
        elif days_diff == 0:
            due_status = False
            due_by = "Due Today"
        else:
            due_status = False
            due_by = f"Due in {days_diff} day(s)"

        data.append({
            'id' : pro.id ,
            'name': pro.name,
            'manager': manager,
            'details': pro.details,
            'deadline': pro.deadline,
            'status': pro.get_status_display(),
            'statusShort' : pro.status ,
            'due_by' : due_by ,
            'due_status' : due_status 
        })

    return JsonResponse(data , safe=False)

def memberproject(request):

    return render(request , 'dashboard/member_project.html')

## members project
def fetchmemberProject(request):
    
    userrole =  request.user.myuserrole.role.id
    userid  = request.user.id
    projects = []
    data = []


    if userrole == 3 :
        promember =  ProjectMember.objects.filter(user_id=userid).values_list('project_id' , flat=True)
        # return JsonResponse({
        #     'promember' : list(promember)
        # })
        projects = Project.objects.filter(id__in=[promember])


    for pro in projects:
        # print("project " , pro)
        try:
            manager = pro.manager.username
        except:
            manager = 'N/A'

        today = date.today()
        deadline = pro.deadline

        days_diff = (deadline - today).days
        due_by = ''

        if days_diff < 0:
            due_status = True
            due_by = f"Overdue by {abs(days_diff)} day(s)"
        elif days_diff == 0:
            due_status = False
            due_by = "Due Today"
        else:
            due_status = False
            due_by = f"Due in {days_diff} day(s)"

        data.append({
            'id' : pro.id ,
            'name': pro.name,
            'manager': manager,
            'details': pro.details,
            'deadline': pro.deadline,
            'status': pro.get_status_display(),
            'statusShort' : pro.status ,
            'due_by' : due_by ,
            'due_status' : due_status  
            
        })

    return JsonResponse(data , safe=False)


def editProject(request , proid):
    project =  Project.objects.get(id=proid)
    manager  = User.objects.filter(myuserrole__role__id=2)


        
    if request.method == "POST":
        try:
            with transaction.atomic():
                name = request.POST.get('name')
                status = request.POST.get('status')
                manager =  request.POST.get('manager')
                detail =  request.POST.get('details')
                deadline =  request.POST.get('deadline')

                project =  Project.objects.get(id=proid)
                project.name  = name
                project.status  = status
                project.manager  = User.objects.get(id=manager)
                project.details  = detail
                project.deadline  = deadline

                project.save()


                messages.success(request ,'Project Updated Successfully')
                return redirect('edit_project' , proid=proid)

            messages.error(request, 'Invalid request method')
            return redirect('edit_project' , proid=proid)
    
        except Exception as e:
            print(f"Error {e}")
            messages.error(request , "Some Error Occurred")
            return redirect('edit_project' , proid=proid)


    return render(request , 'dashboard/edit_project.html' , {'pro' : project , 'manager' : manager} )



def updateProjectStatus(request):

    try:
            id =  request.POST.get('id')
            newstatus = request.POST.get('status')

            project =   Project.objects.get(id=id)

            project.status =  newstatus
            project.save()

            manager =  User.objects.get(id=project.manager)

            html_content = f"""
                    <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                        <h2>Dear {manager.first_name} {manager.last_name} !</h2>
                        <p>You project {project.name} status has changed to {newstatus} . </p>

                        <p>Regards,<br><strong>Team TrekTask</strong></p>
                    </div>
                """
                
            send_custom_email(
                    to_email=[manager.email],
                    subject='Project status changed !',
                    message_text='',
                    html_content=html_content,
                    from_email=settings.EMAIL_HOST_USER,
                    cc=[request.user.email],
                    request=request,
                )

            Notification.objects.create(
                    user= manager  ,
                    title='Project status changed !',
                    detail=f'''
                    You project {project.name} status has changed to {newstatus}
                    ''' ,
                    is_read=False
                )

            Notification.objects.create(
                    user= request.user ,
                    title='Project status change !',
                    detail=f'''
                         Project {project.name} has been changed to  {newstatus} .
                    ''' ,
                    is_read=False
                )

            return  JsonResponse({
                'success' : True
            })
    except Exception as e:
         return  JsonResponse({
                'success' : False
            })


def assingmember(request):

    manager =  User.objects.filter(myuserrole__role__id = 2)

    return render(request , 'dashboard/assign_members.html'  ,{ 'manager' : manager})



## add the project members
# def assingmembersubmit(request):
#         if request.method == "POST":
#             try:

#                 project_id =  request.POST.get('project_dropdown')
#                 user_ids =  request.POST.getlist('user_dropdown')


#                 if not project_id or not user_ids:
#                     messages.error(request, "Project and users selection are required!")
#                     return redirect('assign_member')

#                 try:
#                     project = Project.objects.get(id=project_id)
#                 except Project.DoesNotExist:
#                     messages.error(request, "Selected project doesn't exist!")
#                     return redirect('assign_member')
            
#                 # Check for existing assignments
#                 existing_users = []
#                 for user_id in user_ids:
#                     try:
#                         user = User.objects.get(id=user_id)
#                         if ProjectMember.objects.filter(user=user, project=project).exists():
#                             user = User.objects.get(id=user_id)
#                             existing_users.append(user.username)
#                     except User.DoesNotExist:
#                         continue

#                 if existing_users:
#                     messages.warning(request, f"These users are already assigned: {', '.join(existing_users)}")
#                     return redirect('assign_member')

                
#                 created_count = 0
#                 for user_id in user_ids:
#                     try:
#                         user = User.objects.get(id=user_id)
#                         ProjectMember.objects.create(
#                             project=project,
#                             user=user
#                         )
#                         created_count += 1
#                     except User.DoesNotExist:
#                         continue

#                 if created_count > 0:
#                     messages.success(request, f"Successfully assigned {created_count} user(s) to project!")
#                 else:
#                     messages.warning(request, "No valid users were assigned!")
                
#                 return redirect('assign_member')

#             except Exception as e:
#                 messages.error(request, f"An error occurred: {str(e)}")
#                 return redirect('assign_member')


def assingmembersubmit(request):
        if request.method == "POST":
            try:

                project_id =  request.POST.get('projectid')
                user_ids =  request.POST.getlist('user_dropdown')


                if not project_id or not user_ids:
                    messages.error(request, "Project and users selection are required!")
                    return redirect('project_details' , proid=project_id)

                try:
                    project = Project.objects.get(id=project_id)
                except Project.DoesNotExist:
                    messages.error(request, "Selected project doesn't exist!")
                    return redirect('project_details' , proid=project_id)
            
                # Check for existing assignments
                existing_users = []
                for user_id in user_ids:
                    try:
                        user = User.objects.get(id=user_id)
                        if ProjectMember.objects.filter(user=user, project=project).exists():
                            user = User.objects.get(id=user_id)
                            existing_users.append(user.username)
                    except User.DoesNotExist:
                        continue

                if existing_users:
                    messages.warning(request, f"These users are already assigned: {', '.join(existing_users)}")
                    return redirect('project_details' , proid=project_id)

                
                created_count = 0
                for user_id in user_ids:
                    try:
                        user = User.objects.get(id=user_id)
                        ProjectMember.objects.create(
                            project=project,
                            user=user
                        )
                        created_count += 1

                        ## Log the activity
                        Activitylog.objects.create(
                            user=user,
                            usertype= user.myuserrole.role.id ,
                            title="Members assigned !!",
                            description=f"Member {user.username} assinged to the project {project.name}"
                        )


                        html_content = f"""
                            <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                                <h2>Dear {user.first_name} {user.last_name} </h2>
                                <p>You have been successfully assigned the role of <strong>Member</strong> for the project <strong>{project.name}</strong>. Your leadership is crucial to the project's success.</p>
                                <br>
                                <p>Regards,<br><strong>Team TrekTask</strong></p>
                            </div>
                        """
                        
                        send_custom_email(
                            to_email=[user.email],
                            subject="You've Been Assigned to a Project ",
                            message_text='',
                            html_content=html_content,
                            from_email=settings.EMAIL_HOST_USER,
                            cc=[request.user.email],
                            request=request,
                        )

                        Notification.objects.create(
                            user= user ,
                            title="You've Been Added to a Project ",
                            detail = f'''
                                You have been successfully assigned the role of <strong>Member</strong> for the project <strong>{project.name}</strong>. Your leadership is crucial to the project's success.
                                ''',
                            is_read=False
                        )

                        Notification.objects.create(
                            user= request.user ,
                            title='New member added to Project',
                            detail=f'''
                               New member {user.first_name} {user.last_name} has been added to project {project.name} .
                            ''' ,
                            is_read=False
                        )
                    except User.DoesNotExist:
                        continue

                if created_count > 0:
                    messages.success(request, f"Successfully assigned {created_count} user(s) to project!")
                else:
                    messages.warning(request, "No valid users were assigned!")
                
                return redirect('project_details' , proid=project_id)

            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('project_details' , proid=project_id)


def fetchProjectAndUsers(request):
    try:
        proid = request.GET.get('projectid')
        projects = Project.objects.filter(id=proid)

        # print("project ", projects)
        # Corrected: use project__in for QuerySet
        promember = ProjectMember.objects.filter(project__in=projects).values_list('user', flat=True)

        users = User.objects.filter(myuserrole__role__id=3, id__in=promember)

        project_list = []
        user_list = []

        # Process projects like you process users
        # for project in projects:
        #     project_list.append({
        #         'projectid': project.id,
        #         'name': project.name,
        #         'status': project.get_status_display(),
        #         'deadline': project.deadline.strftime('%Y-%m-%d')
        #     })

        for user in users:
            try:
                role_name = user.myuserrole.role.name
            except Exception:
                role_name = "N/A"

            user_list.append({
                'userid': user.id,
                'username': user.username,
                'email': user.email,
                'role': role_name
            })

        data = {
            # 'projects': project_list,
            'users': user_list,
            'ids': list(promember)
        }

        return JsonResponse(data, safe=False)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)




def projectdtails(request , proid):
    project =  Project.objects.get(id=proid)
    members = project.project_main.select_related('user').values(
                'id',
                'created_at',
                'project_id',
                'user_id',
                'user__username',
                'user__myuserrole__role__name'
            )

    # print("hrre " , members)
    print(project.status)  # Should be 'IP', 'CP', or 'HD'
    print(project.get_status_display())  # Should be 'InProgress', etc.

    return render(request , 'dashboard/project_details.html' , {'project' : project ,
                                            'member' : members ,
                                            'proid' : proid , 
                                            'members_debug': pformat(list(members))})

def removeProjectMemeber(request):

    if request.method == "POST" :
        projectid =  request.POST.get('projectId')
        memberid =  request.POST.get('memberId')

        project  = ProjectMember.objects.get(user_id=memberid , project_id=projectid)
        
        if project:
            project.delete()
            return JsonResponse({'success' : True ,  'msg' : 'Member removed successfully !!'})
        else:
            return JsonResponse({'success' : False ,  'msg' : 'Project not found'})
        
    return JsonResponse({'success' : False , 'msg' : 'Invalid Request method'})




## task management

def addNewTask(request):

    try:
        user =  request.user
        getuser  = User.objects.get(id=user.id)
        role = user.myuserrole.role.id

        project = Project.objects

        if role == 2:
            project = project.filter(manager=getuser)
        elif role == 3:
            getmembers  = ProjectMember.objects.filter(user=user).values_list('project_id' , flat=True)
            project =  project.filter(id__in=getmembers)
            # pass

        else:
            project =  project.all()

        return render(request , 'dashboard/add_task.html' , {'project' : project})
    
    except  Exception as e:
        messages.error(request , f"Error {e}")
        return render(request , 'dashboard/add_task.html' , {'project' : []})



    


def fetchTask(request):

    try:

        userid =  request.user.id
        user =  User.objects.get(id=userid)

        role = user.myuserrole.role.id



        alltask  = Task.objects.select_related('user' , 'project').values(
                'id',
                
                'name' , 'created_at' , 'priority' ,
                
                username=F('user__username'),       
                role=F('user__myuserrole__role__name'),
                project_name=F('project__name'),                    
                statusname=F('status'),
            ).annotate(userid=F('user__id'))

        if role == 2 :
            # show all the data
            projectid = Project.objects.filter(manager=user).values_list('id', flat=True)

            alltask =  alltask.filter(project__in=projectid)

        elif role == 3 :
            # only show his related project 
            alltask =  alltask.filter(user=user)


        return JsonResponse({
            'alltask' : list(alltask) ,
            'success' : True
        } , safe=False)

    except Exception as e:
        
        return JsonResponse({
            'msg' : f"Error {e}",
             'success' : False
        } , safe=False)



def fetchProjectUsers(request):

    project_id = request.GET.get('projectid')

    # Get IDs of users already added to the project
    added_user_ids = ProjectMember.objects.filter(project_id=project_id  ).values_list('user_id', flat=True)

    # Fetch users not in the project
    users = User.objects.exclude(id__in=added_user_ids).filter(
        myuserrole__role__id=3).values(
        'id',
        'username',
        'email',
        role=F('myuserrole__role__name')
    )

    return JsonResponse({
        'success': True,
        'users': list(users)
    })



def submittask(request):
    if request.method == "POST":
        try:
            project_id = request.POST.get('project')
            assignee_id = request.POST.get('assignee')
            
            if not all([project_id, assignee_id, request.POST.get('task_name')]):
                messages.error(request, "Missing required fields")
                return redirect('add_new_task')

            task = Task(
                name=request.POST.get('task_name'),
                project=get_object_or_404(Project, id=project_id),
                user=get_object_or_404(User, id=assignee_id),
                description=request.POST.get('description', ''),
                priority=request.POST.get('priority', 'medium'),
                status=request.POST.get('status', 'in_progress')
            )
            task.save()

            getuser =  User.objects.get(id=assignee_id)

            ## Log the activity
            Activitylog.objects.create(
                user= getuser ,
                usertype= getuser.myuserrole.role.id ,
                title="Task assigned !!",
                description=f"Task created  with {task.name}"
            )

            getuser = User.objects.get(id=assignee_id)
            project = Project.objects.get(id=project_id)

            status = "Assigned"


            html_content = f"""
                <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                    <h2>Dear {getuser.first_name} {getuser.last_name},</h2>
                    <p>A task under the project <strong>{project.name}</strong> has been created for you.</p>
                    <br>
                    <p>Regards,<br><strong>Team TrekTask</strong></p>
                </div>
            """

            print(  
                "email" , getuser.email
            )
            send_custom_email(
                to_email=[getuser.email],
                subject='Task Created',
                message_text='',
                html_content=html_content,
                from_email=settings.EMAIL_HOST_USER,
                cc=[request.user.email],
                request=request,
            )

            # Notification for the assignee
            Notification.objects.create(
                user=getuser,
                title='New Task Assigned',
                detail=f'''
                    A new task under the project <strong>{project.name}</strong> has been assigned to you.
                ''',
                is_read=False
            )

            # Notification for the task creator
            Notification.objects.create(
                user=request.user,
                title='New Task Created',
                detail=f'''
                    Task under the project <strong>{project.name}</strong> has been created and its status set to <strong>{status}</strong>.
                ''',
                is_read=False
            )

            messages.success(request, 'Task created successfully!')
            return redirect('add_new_task')
            
        except Exception as e:
            messages.error(request, f"Error creating task: {str(e)}")
            return redirect('add_new_task')
    
    messages.error(request, "Invalid request method")
    return redirect('add_new_task')



def updateTaskStatus(request):
    try:
            id =  request.POST.get('id')
            newstatus = request.POST.get('status')

            project =   Task.objects.get(id=id)

            project.status =  newstatus
            project.save()

            user =  project.user

            html_content = f"""
                    <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                        <h2>Dear {user.first_name} {user.last_name} !</h2>
                        <p>You task  <strong>{project.name}</strong> status has been changed to {newstatus}. </p>
                        <br>
                        <p>Regards,<br><strong>Team TrekTask</strong></p>
                    </div>
                """
                
            send_custom_email(
                    to_email=[user.email],
                    subject='Task status changed',
                    message_text='',
                    html_content=html_content,
                    from_email=settings.EMAIL_HOST_USER,
                    cc=[request.user.email],
                    request=request,
                )

            Notification.objects.create(
                    user= user ,
                    title='Task status changed',
                    detail=f'''
                    You task  <strong>{project.name}</strong> status has been changed to {newstatus}.
                    ''' ,
                    is_read=False
                )

            Notification.objects.create(
                    user= request.user ,
                    title='Task status changed',
                    detail=f'''
                        Task  <strong>{project.name}</strong> status has been changed to {newstatus}..
                    ''' ,
                    is_read=False
                )

            return  JsonResponse({
                'success' : True
            })
    except Exception as e:
         return  JsonResponse({
                'success' : False,
                'error' : f"Error {e}"
            })
    

def removeTask(request):

    if request.method == "POST" :
        id =  request.POST.get('id')

        task  = Task.objects.get(id=id )
        
        if task:
            user =  User.objects.get(id=task.user)

            ## Log the activity
            Activitylog.objects.create(
                user= user ,
                usertype= user.myuserrole.role.id ,
                title="Task removed !!",
                description=f"Task {task.name} has been removed "
            )

            task.delete()
            
            return JsonResponse({'success' : True ,  'msg' : 'Task removed successfully !!'})
        else:
            return JsonResponse({'success' : False ,  'msg' : 'Task not found'})
        
    return JsonResponse({'success' : False , 'msg' : 'Invalid Request method'})


def taskdetails(request , taskid):
        task = Task.objects.get(id=taskid)

        comments = task.comment_task.all()

        return render(request, 'dashboard/task_details.html' , {
            'taskid' : taskid ,
            'task': task,
            'comments': comments,
            'priority_display': task.get_priority_display(),
            'status_display': task.get_status_display()
        })


def submitComment(request):

    taskid =  request.POST.get('taskid')
    com =  request.POST.get('comment')
    file   = request.FILES.get('file')

    if request.method == 'POST' :
        try:
            # Basic v   alidation
            if not taskid or not com:
                messages.error(request , 'Invalid task or comment is empty !!')
                return redirect('task_details' , taskid=taskid)

            comsave = Comment()
            comsave.comment_text = com
            comsave.task =  Task.objects.get(id=taskid)
            comsave.doc_file =  file

            comsave.save()

            gettask =  Task.objects.get(id=taskid)
            user =  User.objects.get(id=gettask.user.id)

            ## Log the activity
            Activitylog.objects.create(
                user= user ,
                usertype= user.myuserrole.role.id ,
                title="Comment added!!",
                description=f"Comment added on task  {gettask.name} "
            )


            getuser = gettask.user
            project = Project.objects.get(id=gettask.project.id)

            html_content = f"""
                <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                    <h2>Dear {getuser.first_name} {getuser.last_name},</h2>
                    <p>Please check the new comment added to your task: <strong>{gettask.name}</strong>.</p>
                    <p>This task is part of the project: <strong>{project.name}</strong>.</p>
                    <br>
                    <p>Regards,<br><strong>Team TrekTask</strong></p>
                </div>
            """

            send_custom_email(
                to_email=[getuser.email],
                subject='New Comment on Your Task',
                message_text='',
                html_content=html_content,
                from_email=settings.EMAIL_HOST_USER,
                cc=[request.user.email],
                request=request,
            )

            Notification.objects.create(
                user=getuser,
                title='New Comment on Task',
                detail=f'''
                    A new comment has been added to your task <strong>{gettask.name}</strong> under project <strong>{project.name}</strong>.
                ''',
                is_read=False
            )

            Notification.objects.create(
                user=request.user,
                title='Comment Added to Task',
                detail=f'''
                    You have added a comment to task <strong>{gettask.name}</strong> assigned to <strong>{getuser.first_name} {getuser.last_name}</strong>.
                ''',
                is_read=False
            )

            messages.success(request , 'Comment added successfully.')
            return redirect('task_details' , taskid=taskid)


        # fileuploads
        except Exception as e:
            messages.error(request , f"LAst Error {e}")
            return redirect('task_details' , taskid=taskid)
        
    else :
            messages.error(request , 'Invalid request !!')
            return redirect('task_details' , taskid=taskid)



## login page

def loginpage(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            alogin(request, user)
            return redirect('home_page')
    else:
        form = AuthenticationForm(request)
    
    
    return render(request, 'dashboard/login.html', {
        'form': form
    })



# def logout_view(request):
#     authLogout(request)
#     return redirect('login')


def logoutuser(request):
    alogout(request)
    return redirect('loginpage')

def profileview(request):

    user =  User.objects.get(id=request.user.id)

    if request.method == 'POST' :
        first =  request.POST.get('first_name')
        last =  request.POST.get('last_name')
        image  =request.FILES.get('image')
        phone = request.POST.get('phone')

        user.first_name = first
        user.last_name = last


        user.save()

        ## uddate profile
        profile =  user.profile
        profile.phone =  phone
        
        print("image file " ,image)
        if image :
            profile.image = image

        profile.save()

    return render(request , 'dashboard/profile.html' , {'user' : user})


def changepersonalpassword(request):
    

    if request.method == "POST":
        try:

            newpassword = request.POST.get('newpassword')
            currentpassword = request.POST.get('currentpassword')

            # Verify current password
            if not check_password(currentpassword, request.user.password):
                return JsonResponse({
                    'success': False,
                    'msg': 'Current password is incorrect'
                })
        
            user =  User.objects.get(id=request.user.id)
            user.password =  make_password(newpassword)
            user.save()

            # return render(request , 'dashboard/profile.html')

            return JsonResponse({
                'success' : True ,
                'msg' : 'Password changed successfully !!'
            })

        except Exception as e:

            return JsonResponse({
                'success' : False ,
                'msg' : f'Error {e}'
            })

## email inbox

def emailbox(request):

    user  = User.objects.get(id=request.user.id)
    notificatons  =  Notification.objects.filter(user=user)

    return render(request , 'dashboard/email/inbox.html' ,{'data' : notificatons})


def fetchemailinboxdetail(request):
    try:
        msgid = request.GET.get('msgid')
        if not msgid:
            return JsonResponse({'success': False, 'error': 'No message ID provided'}, status=400)
            
        notify = Notification.objects.get(id=msgid)
        notify.is_read = True
        notify.save()
        
        return JsonResponse({
            'success': True,
            'notify': {
                'id': notify.id,
                'title': notify.title,
                'details': notify.detail,
                'created_at': notify.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': notify.is_read ,
                'emailid' : notify.user.email
            }
        })

    except Exception as e :
        return JsonResponse({
            'success' : False ,
            'msg' : f"Error {e}"
        })



def emailcompose(request):


    if request.method == "POST":
            
            try:
                
                emailto_ids = request.POST.getlist('emalto')
                emailcc_raw = request.POST.get('emalcc', '')
                emailbcc_raw = request.POST.get('emalbcc', '')
                emailsubject = request.POST.get('emailsubject', '')
                emailcontent = request.POST.get('emailcontent', '')

                emailcc = [e.strip() for e  in emailcc_raw.split(',') if e.split()]
                emailbcc = [e.strip() for e in emailbcc_raw.split(',') if e.strip()]


                for user_id in emailto_ids:
                    try:
                        getuser = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        continue 

                    html_content = f"""
                        <div style="font-family: Arial, sans-serif; padding: 10px; color: #333;">
                            <p>{emailcontent}</p>
                        </div>
                    """
                    send_custom_email(
                        to_email=[getuser.email] ,
                        subject=emailsubject,
                        message_text='',
                        html_content=html_content,
                        from_email=settings.EMAIL_HOST_USER,
                        cc=emailcc,
                        bcc=emailbcc ,
                        request=request,
                    )
                    
                    user_notification = Notification()
                    user_notification.user = getuser
                    user_notification.title = emailsubject
                    user_notification.detail = emailcontent
                    user_notification.is_read=False
                    user_notification.save()

                    messages.success(request , "Email send successfully !!")
                    return render(request , 'dashboard/email/email_compose.html')

            except Exception as e :
                messages.error(request , f'Error {e}')

    return render(request , 'dashboard/email/email_compose.html')


def activitylog(request):

    return render(request , 'dashboard/activity_log.html')

def fetchactivitylog(request):

    try:

        limit =  request.GET.get('limit')
        userrole =  request.user.myuserrole.id
        activity =  Activitylog.objects
        data = []

        if userrole == 1:
            activity =  activity.all().order_by('-id')

            if limit and int(limit) > 0:
                activity = activity[:int(limit)]

        elif userrole == 2:

            managed_projects = request.user.managed_projects.values_list('id', flat=True)

            members =  ProjectMember.objects.filter(project__in=managed_projects).values_list('user'  , flat=True)

            activity = Activitylog.objects.filter(user__in=members).order_by('-id')

            # Apply limit if valid
            if limit and int(limit) > 0:
                activity = activity[:int(limit)]

        for a in activity:

          role =  Role.objects.get(id=a.usertype)

          data.append({
              'title' : a.title ,
              'description' : a.title ,
              'user' : a.user.username ,
              'usertype' : role.name ,
              'created_at'  : a.created_at.strftime("%Y-%m-%d")
          })  


        # print(data)
        

        return JsonResponse({
            'success' : False ,
            'data' : data
        })

    except Exception as e :
        return JsonResponse({
            'success' : False ,
            'error' : f"Error {e}"
        })