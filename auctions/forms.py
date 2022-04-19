from django import forms


class ListingForm(forms.Form):
    title = forms.CharField(max_length=64)
    description = forms.CharField(max_length=300, widget=forms.Textarea)
    price = forms.DecimalField(min_value=1, max_digits=10, decimal_places=2)
    photo = forms.URLField(required=False, widget=forms.URLInput(
        attrs={
            'placeholder': 'Image address'
        }
    ))