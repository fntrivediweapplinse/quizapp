from django import forms
from .models import Category, Question

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class QuestionForm(forms.ModelForm):
    correct_answer = forms.CharField(
        max_length=255,
        help_text="Enter the correct answer exactly as one of the options above.",
        widget=forms.TextInput(attrs={'placeholder': 'Type the correct option exactly as above'})
    )
    class Meta:
        model = Question
        fields = ['category', 'text', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['correct_answer'].choices = [
            ('option1', 'Option 1'),
            ('option2', 'Option 2'),
            ('option3', 'Option 3'),
            ('option4', 'Option 4'),
        ]

class QuizStartForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), label="Select Category")
    num_questions = forms.IntegerField(min_value=1, max_value=20, initial=5, label="Number of Questions") 