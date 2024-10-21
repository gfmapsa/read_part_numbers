from django import forms

class LoadPdf(forms.Form):
    pdf = forms.FileField(
        label="Archivo PDF", 
        required=True, 
        widget=forms.ClearableFileInput(attrs={'accept': 'application/pdf'})
        )