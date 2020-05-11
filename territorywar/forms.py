from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import TerritoryWar

class TerritoryWarHistoryListForm(forms.Form):

	tw = forms.ChoiceField(label=_('Date'), required=True)

	def __init__(self, *args):

		tws = TerritoryWar.objects.all()
		self.fields['tw'].choices = ( (tw.pk, tw.get_name(), tw.get_date()) for tw in tws )
