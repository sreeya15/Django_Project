from django import forms
from .models import Demand, DemandStagePeriod
from datetime import datetime, timedelta

class DemandForm(forms.ModelForm):
    start_date = forms.DateField(
        label='Start Date (t0)', 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    duration_months = forms.IntegerField(
        label='Duration in Months (end)', 
        min_value=1, 
        help_text='Total duration of the demand in months'
    )
    
    class Meta:
        model = Demand
        fields = ['name', 'start_date', 'duration_months']
        
    def save(self, commit=True):
        demand = super().save(commit=False)
        if commit:
            demand.save()
        return demand

class DemandStagePeriodForm(forms.ModelForm):
    class Meta:
        model = DemandStagePeriod
        fields = ['demand', 'stage', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure end_date is not before start_date
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date cannot be before start date')
        
        return cleaned_data
