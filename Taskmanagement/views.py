# from django.core.mail import send_mail
# from django.http import HttpRequest , HttpResponse
# from django.conf import settings



# def mainform(request):
#     subject = 'Testing Mail'
#     message = '<p>This is the <strong>testing</strong> mail<p>'
#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = ['']

#     send_mail(
#         subject,
#         message,
#         from_email,
#         recipient_list,
#         fail_silently=False,
#     )

#     return HttpResponse("send")
