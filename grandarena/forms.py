from django import forms

class AllyCodeForm(forms.Form):
	ally_code = forms.CharField(label='Your allycode', max_length=11)
