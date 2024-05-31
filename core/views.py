# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from core.forms import CVForm
from .models import CV
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from django.contrib import messages
from PIL import Image, ImageOps
import io
from django.db.models import Q
from .models import user_update
import uuid
from django.contrib.auth.models import User
from django.core.mail import send_mail
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.conf import settings
import os




def home(request):
    return render(request, 'core/home.html')

@login_required(login_url='login_user')
def cv_generator(request):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        address = request.POST['address']
        experience = request.POST['experience']
        education = request.POST['education']
        projects = request.POST['projects']
        skills = request.POST['skills']
        awards = request.POST['awards']
        languages = request.POST['languages']
        image = request.FILES.get('image')

        cv = CV(
            user=request.user,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            address=address,
            experience=experience,
            education=education,
            projects=projects,
            skills=skills,
            awards=awards,
            languages=languages,
            image=image
        )
        cv.save()
        messages.success(request, 'CV created successfully!')
        return redirect('cvs_created')
    return render(request, 'core/cv_generator.html')


def process_image(image):
    # Open the uploaded image
    img = Image.open(image)
    
    # Convert image to RGB (if it's in a different mode)
    img = img.convert("RGB")
    
    # Create a new image with white background
    white_bg = Image.new("RGB", img.size, (255, 255, 255))
    
    # Paste the uploaded image onto the white background
    white_bg.paste(img, (0, 0), img)
    
    # Resize the image to passport photo size (591x709 pixels)
    img_resized = white_bg.resize((591, 709), Image.ANTIALIAS)
    
    # Save the image to a BytesIO object
    img_byte_arr = io.BytesIO()
    img_resized.save(img_byte_arr, format='JPEG', quality=85)  # You can adjust the quality if needed
    img_byte_arr.seek(0)
    
    return img_byte_arr


def cv_create(request):
    if request.method == 'POST':
        form = CVForm(request.POST, request.FILES)
        if form.is_valid():
            cv = form.save(commit=False)
            
            if 'image' in request.FILES:
                processed_image = process_image(request.FILES['image'])
                cv.image.save(request.FILES['image'].name, processed_image, save=False)
                
            cv.save()
            return redirect('cvs_created')
    else:
        form = CVForm()
    return render(request, 'core/cv_form.html', {'form': form})


@login_required(login_url='login_user')
def cvs_created(request):
    cvs = CV.objects.filter(user=request.user)
    return render(request, 'core/cvs_created.html', {'cvs': cvs})


@login_required(login_url='login_user')
def cvs_created(request):
    query = request.GET.get('q')
    if query:
        cvs = CV.objects.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query)
        )
    else:
        cvs = CV.objects.all()
    return render(request, 'core/cvs_created.html', {'cvs': cvs})


def cv_view(request, pk):
    cv = get_object_or_404(CV, pk=pk)
    return render(request, 'core/cv_detail.html', {'cv': cv})

def cv_download(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id, user=request.user)

    # Set the filename based on the full name
    filename = f"CV_{cv.full_name.replace(' ', '_')}.pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # Set up some basic document properties
    width, height = A4
    p.setTitle(f"{cv.full_name}'s CV")

    # Adjusted Margins
    margin_x = 0.65 * inch
    margin_y = 0.65 * inch

    # Profile Image
    if cv.image:
        image_path = os.path.join(settings.MEDIA_ROOT, cv.image.name)
        if os.path.exists(image_path):
            p.drawImage(image_path, margin_x, height - margin_y - 2 * inch, width=1.5 * inch, height=1.5 * inch)

    # Personal Information
    text_x = margin_x + 2 * inch  # Adjusted position for text to provide gap
    text_y = height - margin_y - 1 * inch  # Align with profile image

    p.setFont("Helvetica-Bold", 24)
    p.drawString(text_x, text_y, cv.full_name)
    p.setFont("Helvetica", 12)
    p.drawString(text_x, text_y - 0.3 * inch, cv.email)
    p.drawString(text_x, text_y - 0.6 * inch, cv.phone_number)
    p.drawString(text_x, text_y - 0.9 * inch, cv.address)

    # Starting position for sections
    y_position = text_y - 1 * inch

    def add_section(title, content, extra_space=False):
        nonlocal y_position
        if content:
            if extra_space:
                y_position -= 0.5 * inch  # Add extra space before the section

            p.setFont("Helvetica-Bold", 14)
            p.drawString(margin_x, y_position, title)
            p.setLineWidth(1)
            y_position -= 0.2 * inch
            p.line(margin_x, y_position, width - margin_x, y_position)  # Underline
            y_position -= 0.3 * inch

            p.setFont("Helvetica", 12)
            text_object = p.beginText(margin_x, y_position)
            for line in content.split('\n'):
                text_object.textLine(line)
                y_position -= 0.2 * inch
            p.drawText(text_object)
            y_position -= 0.3 * inch  # Space after section

    # Add sections
    add_section('Experience', cv.experience, extra_space=True)  # Extra space before Experience section
    add_section('Education', cv.education)
    add_section('Projects', cv.projects)
    add_section('Skills', cv.skills)
    add_section('Awards', cv.awards)
    add_section('Languages', cv.languages)

    # Finish the PDF
    p.showPage()
    p.save()

    # Get the PDF value and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

def cv_delete(request, cv_id):
    cv = get_object_or_404(CV, id=cv_id)
    cv.delete()
    return redirect('cvs_created')

def profile(request):
    return render(request, 'core/profile.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            new = user_update.objects.get(user=user)
            if new.is_verified:
                login(request, user)
                messages.success(request, 'User Logged in.')
                next_url = request.GET.get('next', 'home')  # Get the 'next' parameter or redirect to 'home'
                return redirect(next_url)
            else:
                messages.warning(request, 'User is not verified.')
                return redirect('login_user')
        else:
            messages.warning(request, 'No User Found')
    return render(request, 'core/login.html')

def register_user(request):
    if request.method == 'POST':
        first = request.POST.get('first')
        last = request.POST.get('last')
        username = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass')
        pass2 = request.POST.get('pass1')

        if pass1 != pass2:
            messages.warning(request, 'Passwords do not match')
            return redirect('register_user')

        if User.objects.filter(username=username).exists():
            messages.warning(request, 'Username already exists')
            return redirect('register_user')

        if User.objects.filter(email=email).exists():
            messages.warning(request, 'Email already exists')
            return redirect('register_user')

        user = User.objects.create_user(first_name=first, last_name=last, username=username, email=email, password=pass1)
        user.set_password(pass1)
        user.save()
        myuuid = uuid.uuid4()
        update = user_update.objects.create(user=user, token=myuuid)
        update.save()
        
        subject = 'CV Generator Web App : Your Email Verification Link'
        message = f'Hi {username}, Thank You For Registering in CV Generator Web App. Click The Verification Link To Verify Your Email: http://127.0.0.1:8000/verify/{myuuid}/' 
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, email_from, recipient_list)
        
        messages.success(request, 'User Registered Successfully. Please Check Your Email To Verify Your Account.')
        return redirect('login_user')
    return render(request, 'core/register.html')

def verify(request, myuuid):
    try:
        user = user_update.objects.get(token=myuuid)
        user.is_verified = True
        user.save()
        messages.success(request, 'Email verified successfully.')
    except user_update.DoesNotExist:
        messages.warning(request, 'Verification failed. Invalid token.')
    return redirect('login_user')

def logout_user(request):
    logout(request)
    return redirect('home')

def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        pass1 = request.POST.get('pass')
        pass2 = request.POST.get('pass1')
        
        if pass1 != pass2:
            messages.warning(request, 'Passwords do not match')
            return redirect('reset_password')

        try:
            user = User.objects.get(email=email)
            user.set_password(pass1)
            user.save()
            messages.success(request, 'Password reset successfully. Please log in with your new password.')
            return redirect('login_user')
        except User.DoesNotExist:
            messages.warning(request, 'User with the provided email does not exist.')
            return redirect('reset_password')
    return render(request, 'core/reset-password.html')

def portfolio_view(request):
    # My Portfolio
    context = {
        'profile_image_url': '/static/images/md-omar-faruk.png',
        'full_name': 'Mohammad Omar Faruk',
        'email': 'md.omar28151@gmail.com',
        'phone_number': '+8801952751879',
        'whatsapp_number': '+8801952751879',
        'facebook_link': 'https://www.facebook.com/Mohammad.Omar.Faruk007/',
        'linkedin_link': 'https://www.linkedin.com/in/mohammad-omar-faruk-5900b7181/',
        'github_link': 'https://github.com/mdOmarfaruk151',
        'skills': 'Django, React, Python, JavaScript, HTML5, CSS, Bootstrap, Tailwind CSS',
        'languages': 'Bengal, English, Hindi',
        'projects': [
            {'name': 'Project One', 'link': 'https://www.example.com/project-one'},
            {'name': 'Project Two', 'link': 'https://www.example.com/project-two'},
            # Add more projects as needed
        ],
    }
    return render(request, 'core/portfolio.html', context)

