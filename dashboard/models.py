from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.functions import Lower
# from django.contrib.auth.models import AbstractUser
# from django.conf import settings

# Create your models here.

class Role(models.Model):
    name = models.CharField(max_length=100 ,null=False)

class Project(models.Model):
    class StatusPro(models.TextChoices):
        IN_PROGRESS =  'IP' , 'InProgress'
        COMPLETED =     'CP'  , 'Completed'
        HOLD =        'HD'   , 'Hold'

    name = models.CharField(max_length=255 , null=False)
    manager = models.ForeignKey(User , on_delete=models.CASCADE , related_name='managed_projects')
    # members = models.ManyToManyField(User, related_name='project_members')
    details =  models.TextField()
    deadline = models.DateField()
    status =  models.CharField(
        max_length=2,
        choices=StatusPro.choices,
        default=StatusPro.IN_PROGRESS
    )
    created_at =  models.DateTimeField(default=timezone.now)


    # def __str__(self):
    #     return self.name
    
    class Meta:
        ordering =  [Lower('name')]
        get_latest_by =  'created_at'
        constraints = [
            models.UniqueConstraint(
                fields = ['name'] , 
                name='unique_project_name',
                violation_error_message='Same name project existed before !!'
            )            
        ]



class Task(models.Model):
    class Statustask(models.TextChoices):
        IN_PROGRESS =  'IP' , 'InProgress'
        COMPLETED =     'CP'  , 'Completed'
        HOLD =        'HD'   , 'Hold'

    class Priority(models.TextChoices):
        LOW =  'LW' , 'Low'
        MEDIUM =     'MM'  , 'Medium'
        HIGH =        'HH'   , 'High'
        CRITICAL =   'CL' , 'Critical'

    name = models.CharField(max_length=255 , null=False)
    project =  models.ForeignKey(Project , on_delete=models.CASCADE , related_name='task_project')
    user =  models.ForeignKey(User, on_delete=models.CASCADE , related_name='task_user')
    # doc_file =  models.FileField(upload_to='fileuploads/')
    description =  models.TextField(null=True , default='N/A')
    priority =  models.CharField(
        max_length=2 ,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    status =  models.CharField(
        max_length=2 ,
        choices=Statustask.choices,
        default=Statustask.IN_PROGRESS
    )
    created_at =  models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    comment_text = models.TextField()
    task =  models.ForeignKey(Task , on_delete=models.CASCADE , related_name='comment_task')
    doc_file =  models.FileField(upload_to='fileuploads/' , default='')
    created_at =  models.DateTimeField(default=timezone.now , db_index=True )

    class Meta:
        ordering = ['-created_at'] 

class Activity(models.Model):
    user =  models.ForeignKey(User, on_delete=models.CASCADE , related_name='activity_user')
    details =  models.TextField()

class UserRole(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE , related_name='myuserrole')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    

class ProjectMember(models.Model):
    project =  models.ForeignKey(Project, on_delete=models.CASCADE , related_name='project_main')
    user =  models.ForeignKey(User ,on_delete=models.CASCADE ,  related_name='project_members' , null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('project', 'user')] 

    # class Meta:
    #     unique_together = ('project', 'user')

    # def __str__(self):
    #     return f"{self.user.username} in {self.project.name}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)


class Notification(models.Model):
    user =  models.ForeignKey(User , on_delete=models.CASCADE)
    title =  models.CharField(max_length=255)
    detail =  models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)


class Activitylog(models.Model):
    user = models.ForeignKey(User , on_delete=models.CASCADE , related_name="user_activity")
    usertype = models.IntegerField(default=1)
    title = models.CharField(max_length=255)
    description =  models.TextField(default='' ,  null=True)
    created_at =  models.DateTimeField(auto_now_add=True)