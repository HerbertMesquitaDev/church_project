from django import forms
from django.core.exceptions import ValidationError
from .models import Booking, Location


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('title', 'location', 'date', 'start_time', 'end_time',
                  'ministry', 'notes')
        widgets = {
            'title':      forms.TextInput(attrs={'class': 'form-input',
                                                  'placeholder': 'Ex: Reunião de Oração, Ensaio do Coral...'}),
            'location':   forms.Select(attrs={'class': 'form-input'}),
            'date':       forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'end_time':   forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'ministry':   forms.TextInput(attrs={'class': 'form-input',
                                                  'placeholder': 'Ex: Louvor, Jovens, EBD...'}),
            'notes':      forms.Textarea(attrs={'class': 'form-input', 'rows': 3,
                                                 'placeholder': 'Observações adicionais (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.filter(active=True)
        self.fields['ministry'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned = super().clean()
        location = cleaned.get('location')
        date = cleaned.get('date')
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')

        if start and end and start >= end:
            self.add_error('end_time',
                           "O horário de término deve ser após o início.")
            return cleaned

        if location and date and start and end:
            conflicts = Booking.objects.filter(
                location=location,
                date=date,
                status__in=['pending', 'approved'],
                start_time__lt=end,
                end_time__gt=start,
            )
            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                c = conflicts.first()
                raise ValidationError(
                    f"⚠️ Conflito detectado: '{c.title}' já ocupa {location} "
                    f"no dia {date.strftime('%d/%m/%Y')} das "
                    f"{c.start_time.strftime('%H:%M')} às {c.end_time.strftime('%H:%M')}. "
                    f"Escolha outro local ou horário."
                )
        return cleaned


class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
        }


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ('name', 'address', 'capacity', 'description', 'active')
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-input'}),
            'address':     forms.TextInput(attrs={'class': 'form-input'}),
            'capacity':    forms.NumberInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
