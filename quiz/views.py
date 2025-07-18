from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Question, QuizAttempt, QuizAnswer
from .forms import CategoryForm, QuestionForm, QuizStartForm
from django.utils import timezone
import random
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Q

from django.contrib.staticfiles import finders # Import finders to check for static files
from django.templatetags.static import static # Import static to get static file URLs
from django.template.defaultfilters import slugify # Import slugify

# Create your views here.

@login_required
def dashboard(request):
    categories = Category.objects.all()
    questions = Question.objects.all()
    return render(request, 'quiz/dashboard.html', {
        'categories': categories,
        'questions': questions
    })

@login_required
def category_list(request):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')

    categories = Category.objects.all()
    categories_with_images = []
    default_image_url = static('images/categories/default_category.png') # Updated default image URL path

    for category in categories:
        # Construct potential image path based on category name (lowercase, replace spaces with underscores, add .png)
        image_filename = slugify(category.name).replace('-', '_') + '.png'
        potential_image_path = f'images/categories/{image_filename}'

        # Check if the static file exists
        if finders.find(potential_image_path):
            # If it exists, use its URL
            image_url = static(potential_image_path)
        else:
            # If not, use the default image URL
            image_url = default_image_url

        # Append a dictionary with category object and image_url
        categories_with_images.append({
            'category': category,
            'image_url': image_url
        })

    return render(request, 'quiz/category_list.html', {'categories': categories_with_images})

@login_required
def category_create(request):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'quiz/category_form.html', {'form': form})

@login_required
def category_edit(request, slug):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'quiz/category_form.html', {'form': form})

@login_required
def category_delete(request, slug):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('category_list')
    return render(request, 'quiz/category_confirm_delete.html', {'category': category})

@login_required
def question_list(request):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')
    questions = Question.objects.all()
    return render(request, 'quiz/question_list.html', {'questions': questions})

@login_required
def question_create(request):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question created successfully.')
            return redirect('question_list')
    else:
        form = QuestionForm()
    return render(request, 'quiz/question_form.html', {'form': form})

@login_required
def question_edit(request, pk):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully.')
            return redirect('question_list')
    else:
        form = QuestionForm(instance=question)
    return render(request, 'quiz/question_form.html', {'form': form})

@login_required
def question_delete(request, pk):
    if not request.user.is_superuser:
        return render(request, 'quiz/admin_login.html')
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('question_list')
    return render(request, 'quiz/question_confirm_delete.html', {'question': question})

def admincrud(request):
    # Handle POST request for login
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password) # Use username for email field in authenticate

        if user is not None and user.is_active and user.is_superuser:
            login(request, user)
            # Redirect to the admin dashboard after successful login
            return redirect('admincrud') # Redirect back to the admin dashboard URL name
        else:
            # Authentication failed or user is not a superuser/active
            messages.error(request, 'Invalid credentials or not a superuser.')
            # Fall through to render the login form again with an error message

    # Handle GET request
    if request.user.is_authenticated and request.user.is_superuser:
        # If user is logged in and is a superuser, render the admin dashboard
        return render(request, 'quiz/admincrud.html')
    else:
        # If user is not authenticated or not a superuser, render the custom admin login template
        # Pass messages to the template context
        return render(request, 'quiz/admin_login.html', {'messages': messages.get_messages(request)})

@login_required
def quiz_dashboard(request):
    categories = Category.objects.all()
    return render(request, 'quiz/quiz_dashboard.html', {'categories': categories})

@login_required
def quiz_start(request):
    if request.method == 'POST':
        form = QuizStartForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            num_questions = form.cleaned_data['num_questions']

            # Check for an existing incomplete attempt for this user and category
            existing_attempt = QuizAttempt.objects.filter(
                user=request.user,
                category=category,
                completed=False
            ).first()

            if existing_attempt:
                # If an incomplete attempt exists, resume it
                messages.info(request, 'Resuming your previous quiz attempt.')
                return redirect('quiz_question', category_id=category.id)

            # If no incomplete attempt exists, create a new one
            # Get all questions for the category
            all_questions = list(Question.objects.filter(category=category))
            
            if not all_questions:
                messages.error(request, 'No questions available for this category.')
                return redirect('quiz_dashboard')

            # Select random questions, up to num_questions or available questions
            num_to_select = min(num_questions, len(all_questions))
            random_questions = random.sample(all_questions, num_to_select)
            random_question_ids = [q.id for q in random_questions]

            # Create a new QuizAttempt
            attempt = QuizAttempt.objects.create(
                user=request.user,
                category=category,
                total_questions=num_to_select, # Store the actual number of questions selected
                started_at=timezone.now(),
                completed=False,
                question_order_ids=random_question_ids # Store the ordered list of IDs
            )

            # Set the first question for the attempt
            if random_questions:
                attempt.current_question = random_questions[0]
                attempt.save()

            return redirect('quiz_question', category_id=category.id)
    else:
        form = QuizStartForm()
    return render(request, 'quiz/quiz_start.html', {'form': form})

@login_required
def quiz_question(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    # Get the user's current incomplete quiz attempt for this category
    attempt = QuizAttempt.objects.filter(
        user=request.user,
        category=category,
        completed=False
    ).first()
    
    if not attempt:
        # If no attempt exists, redirect to start
        messages.error(request, 'No active quiz attempt found. Please start a new quiz.')
        return redirect('quiz_dashboard')

    # Get the ordered list of question IDs for this attempt
    question_order_ids = attempt.question_order_ids
    
    # If for some reason question_order_ids is empty or None, delete the attempt and redirect
    if not question_order_ids:
         messages.error(request, 'No questions found for this quiz attempt. Please start a new quiz.')
         attempt.delete()
         return redirect('quiz_dashboard')

    # Fetch the questions in the correct order
    from django.db.models import Case, When, Value, IntegerField
    ordered_questions = Question.objects.filter(id__in=question_order_ids).order_by(Case(
        *[When(id=q_id, then=pos) for pos, q_id in enumerate(question_order_ids)],
        default=len(question_order_ids),
        output_field=IntegerField()
    ))
    
    total_questions = ordered_questions.count()
    
    # Determine the current question based on the attempt's current_question field
    current_question_index = -1
    if attempt.current_question:
        try:
             current_question_index = list(ordered_questions).index(attempt.current_question)
        except ValueError:
             # Handle case where the current question is not in the ordered list
             messages.error(request, "Error finding current question in the quiz list.")
             attempt.delete()  # Delete the attempt and start fresh
             return redirect('quiz_dashboard')

    # If current_question is not set or is beyond the last question, redirect to result
    if not attempt.current_question or current_question_index >= total_questions:
         attempt.completed = True
         if not attempt.finished_at:
             attempt.finished_at = timezone.now()
         attempt.save()
         return redirect('leaderboard', category_id=category.id)

    current_question = attempt.current_question
    
    # Get options from the current question model
    options = [
        current_question.option1,
        current_question.option2,
        current_question.option3,
        current_question.option4,
    ]
    random.shuffle(options)
    
    # Calculate progress
    current_question_number = current_question_index + 1
    progress = (current_question_number / total_questions) * 100 if total_questions > 0 else 0

    # Define the timer duration (in seconds)
    quiz_timer_duration = 30

    if request.method == 'POST':
        selected_option = request.POST.get('selected_option', '')  # Default to empty string if no option selected
        
        # Save answer - use get_or_create to prevent duplicates on refresh
        answer, created = QuizAnswer.objects.get_or_create(
            attempt=attempt,
            question=current_question,
            defaults={
                'selected_option': selected_option,
                'is_correct': selected_option == current_question.correct_answer
            }
        )
        
        # Update score only if the answer was just created AND it's correct
        if created and selected_option == current_question.correct_answer:
            attempt.score += 1
            attempt.save()

        # Determine the next question index
        next_question_index = current_question_index + 1

        # Update the current_question for the attempt to the next question in the ordered list
        if next_question_index < total_questions:
            attempt.current_question = ordered_questions[next_question_index]
            attempt.save()
            next_url = reverse('quiz_question', args=[category_id])
        else:
            # Quiz completed
            attempt.completed = True
            if not attempt.finished_at:
                attempt.finished_at = timezone.now()
            attempt.save()
            # Redirect to the main leaderboard page after quiz completion with category ID as GET parameter
            next_url = reverse('leaderboard_main') + f'?category={category_id}' # Pass category_id as GET parameter

        # Handle AJAX request for immediate feedback and next question URL
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return JsonResponse({
                'is_correct': selected_option == current_question.correct_answer,
                'correct_option': current_question.correct_answer,
                'next_url': next_url,
                'score': attempt.score,
                'current_question_number': current_question_number,
                'total_questions': total_questions,
                'quiz_timer_duration': quiz_timer_duration,
             })

        # Redirect for non-AJAX requests (fallback)
        return redirect(next_url)
    
    context = {
        'question': current_question,
        'options': options,
        'category': category,
        'progress': progress,
        'current_question_number': current_question_number,
        'total_questions': total_questions,
        'score': attempt.score,
        'quiz_timer_duration': quiz_timer_duration,
    }
    
    return render(request, 'quiz/quiz_question.html', context)

@login_required
def quiz_result(request, category_id=None):
    # You might want to retrieve the latest completed attempt for the user and category
    # If category_id is not provided, maybe show results for all categories or latest attempt
    latest_attempt = None
    # Ensure category_id is provided for fetching specific quiz result
    if category_id is None:
         messages.error(request, "Quiz result URL requires a category ID.")
         return redirect('quiz_dashboard') # Redirect if category_id is missing

    latest_attempt = QuizAttempt.objects.filter(
        user=request.user,
        category_id=category_id,
        completed=True
    ).order_by('-finished_at').first() # <-- Changed to get the latest attempt

    if not latest_attempt:
        messages.info(request, "No completed quiz attempts found for this category.")
        return redirect('quiz_dashboard') # Redirect if no result found

    context = {
        'attempt': latest_attempt,
        'category': latest_attempt.category,
        'score': latest_attempt.score,
        'total_questions': latest_attempt.total_questions,
        'percentage': (latest_attempt.score / latest_attempt.total_questions) * 100 if latest_attempt.total_questions > 0 else 0,
         # Fetch answers for review if needed in the result template
        'answers': latest_attempt.answers.select_related('question').all(),
    }
    return render(request, 'quiz/quiz_result.html', context)

@login_required
def leaderboard_main(request):
    categories = Category.objects.all()
    selected_category = None
    top_attempts = None

    category_id = request.GET.get('category')
    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id)
            # Get completed attempts for this category, ordered by score descending and then by finish time ascending
            top_attempts = QuizAttempt.objects.filter(
                category=selected_category,
                completed=True
            ).order_by('-score', 'finished_at')[:10] # Top 10, adjust as needed

        except Category.DoesNotExist:
            messages.error(request, "Selected category does not exist.")

    context = {
        'categories': categories,
        'selected_category': selected_category,
        'top_attempts': top_attempts,
    }
    return render(request, 'quiz/leaderboard_main.html', context)

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home') # Redirect to your desired logout destination (e.g., home page or login page)
