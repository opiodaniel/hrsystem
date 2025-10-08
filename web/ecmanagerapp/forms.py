from django import forms
from .models import Client, Payment, Land, ClientLand, EmployeePaymentRecord
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import (UserCreationForm)
from django.contrib.auth import get_user_model
from .models import (Employees)
from django.contrib.auth.models import User
from django.db.models import Q
import re


def normalize_phone_number(phone_number):
    return re.sub(r'\D', '', phone_number)


class ClientForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phoneNumber1 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phoneNumber2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'required': False}))
    location = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    is_archived = forms.BooleanField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Client
        fields = ('name', 'phoneNumber1', 'phoneNumber2', 'location', 'is_archived',)

    def clean_phoneNumber1(self):
        phone_number1 = normalize_phone_number(self.cleaned_data['phoneNumber1'])
        if Client.objects.filter(phoneNumber1=phone_number1).exists() or Client.objects.filter(phoneNumber2=phone_number1).exists():
            raise forms.ValidationError('Client with the same phone number already exists.')
        return phone_number1

    def clean_phoneNumber2(self):
        phone_number2 = self.cleaned_data.get('phoneNumber2')
        if phone_number2:
            phone_number2 = normalize_phone_number(phone_number2)
            if len(phone_number2) < 7:
                raise forms.ValidationError("Phone number must be at least 7 characters long.")
            if Client.objects.filter(phoneNumber1=phone_number2).exists() or Client.objects.filter(phoneNumber2=phone_number2).exists():
                raise forms.ValidationError('Client with the same phone number already exists.')
        return phone_number2

    def clean(self):
        cleaned_data = super().clean()
        phone_number1 = cleaned_data.get("phoneNumber1")
        phone_number2 = cleaned_data.get("phoneNumber2")

        if phone_number1 and phone_number2 and phone_number1 == phone_number2:
            raise forms.ValidationError("Phone number 1 and phone number 2 cannot be the same.")

        return cleaned_data


class ClientEditForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('name', 'phoneNumber1', 'phoneNumber2', 'location')

    def __init__(self, *args, **kwargs):
        super(ClientEditForm, self).__init__(*args, **kwargs)
        if self.instance and not self.instance.is_editable():
            self.fields['phoneNumber1'].disabled = True
            self.fields['phoneNumber2'].disabled = True

    def clean_phoneNumber1(self):
        phoneNumber1 = self.cleaned_data['phoneNumber1']
        if Client.objects.exclude(id=self.instance.id).filter(Q(phoneNumber1=phoneNumber1) | Q(phoneNumber2=phoneNumber1)).exists():
            raise forms.ValidationError("A client with the same phone number already exists.")
        return phoneNumber1

    def clean_phoneNumber2(self):
        phoneNumber2 = self.cleaned_data['phoneNumber2']
        if phoneNumber2:
            if len(phoneNumber2) < 7:
                raise forms.ValidationError("Phone number must be at least 7 characters long.")
            if Client.objects.exclude(id=self.instance.id).filter(Q(phoneNumber1=phoneNumber2) | Q(phoneNumber2=phoneNumber2)).exists():
                raise forms.ValidationError("A client with the same phone number already exists.")
        return phoneNumber2

    def clean(self):
        cleaned_data = super().clean()
        phoneNumber1 = cleaned_data.get("phoneNumber1")
        phoneNumber2 = cleaned_data.get("phoneNumber2")

        if phoneNumber1 and phoneNumber2 and phoneNumber1 == phoneNumber2:
            raise forms.ValidationError("Phone number 1 and phone number 2 cannot be the same.")

        return cleaned_data


class EmployeeLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder':'op@gmail.com'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'opio'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'daniel'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'opio'}))
    password1 = forms.Field(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder':'password1'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder':'password2'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose a different one.")
        return username

    class Meta:
        model = get_user_model()
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        )

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user

    class LoginForm(AuthenticationForm):
        password = forms.CharField(widget=forms.PasswordInput)


class UserEditForm(forms.ModelForm):

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = get_user_model()
        fields = (
            'first_name',
            'last_name',
            'email'
        )


class ProfileEditForm(forms.ModelForm):
    profile_pic = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.CharField(widget=forms.TextInput(attrs={'type': 'date', 'class': 'form-control'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    zip = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Employees
        fields = ('profile_pic', 'date_of_birth',
                  'address', 'zip', 'city', 'country',
                  'phone',)  #'short_bio', 'bio',


class CommaSeparatedIntegerField(forms.IntegerField):
    def to_python(self, value):
        if value is None:
            return None
        # Remove commas from the input value and convert to integer
        if isinstance(value, str):
            value = value.replace(',', '')  # Remove commas
        try:
            return int(value)
        except (ValueError, TypeError):
            raise forms.ValidationError('Enter a valid integer.')


# class CommaSeparatedNumberInput(forms.TextInput):
#     def __init__(self, attrs=None):
#         super().__init__(attrs={'class': 'form-control amount-input', 'oninput': 'formatAmount(this)', **(attrs or {})})
#
#     def format_value(self, value):
#         if value is None:
#             return ''
#         return f'{value:,}'  # Format the value with commas

class CommaSeparatedNumberInput(forms.TextInput):
    def __init__(self, attrs=None):
        super().__init__(attrs={'class': 'form-control amount-input', 'oninput': 'formatAmount(this)', **(attrs or {})})

    def format_value(self, value):
        if value is None or value == '':
            return ''
        try:
            return f'{int(value):,}'  # Format the value with commas
        except (ValueError, TypeError):
            return value  # In case the value is not a number, return as is


class ClientLandForm(forms.ModelForm):
    class Meta:
        model = ClientLand
        fields = ['client', 'land']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'land': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ClientLandForm, self).__init__(*args, **kwargs)
        self.fields['land'].queryset = Land.objects.filter(available=True)


class PaymentForm(forms.ModelForm):
    amount_paid = CommaSeparatedIntegerField(label='amount paid', widget=CommaSeparatedNumberInput(), initial=0)
    approved = forms.BooleanField(required=True, initial=True,
                                      widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Payment
        fields = ['client_land', 'amount_paid', 'timestamp', 'approved', 'approved_by']
        widgets = {
            'client_land': forms.Select(attrs={'class': 'form-control'}),
            'timestamp': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # 'approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'approved_by': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['approved_by'].queryset = Employees.objects.filter(is_administrator=True)
        self.fields['approved_by'].label = 'Approved by:'


class LandForm(forms.ModelForm):
    price = CommaSeparatedIntegerField(label='land price', widget=CommaSeparatedNumberInput(), initial=0)

    class Meta:
        model = Land
        fields = ['plot_number', 'location', 'price']
        widgets = {
            'plot_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'plot number', 'required': 'required'}),
            'location': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'location', 'required': 'required'}),
            'price': forms.NumberInput(
                attrs={'class': 'form-control', 'oninput': 'formatAmount(this)', 'required': 'required'}),
        }

    def clean_plot_number(self):
        plot_number = self.cleaned_data.get('plot_number')
        if not plot_number:
            raise forms.ValidationError("Plot number is required.")
        if Land.objects.filter(plot_number=plot_number).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("A land with this plot number already exists.")
        return plot_number

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if not location:
            raise forms.ValidationError("Location is required.")
        return location

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise forms.ValidationError("Land Price must be greater than zero.")
        return price


# Edit Employee payment
class EditEmployeePaymentForm(forms.ModelForm):
    class Meta:
        model = EmployeePaymentRecord
        fields = ['amount_paid']

    def clean_amount_paid(self):
        amount_paid = self.cleaned_data.get('amount_paid')
        if amount_paid < 0:
            raise forms.ValidationError("Amount paid cannot be less than zero.")
        return amount_paid


# ===========  form for the admin to enter clients who do not exist in the system =============
class AdminClientForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Daniel Opio'}))
    phoneNumber1 = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'0781218116'}))
    phoneNumber2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'0762179510'})
    )
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Kampala'}))
    is_archived = forms.BooleanField(required=False, widget=forms.HiddenInput())
    employee = forms.ModelChoiceField(
        queryset=Employees.objects.all(),
        label='Distributor',
        required=False,  # Ensure employee is not required if it can be empty
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    class Meta:
        model = Client
        fields = ('name', 'phoneNumber1', 'phoneNumber2', 'location', 'is_archived', 'employee')

    def clean_phoneNumber1(self):
        phone_number1 = normalize_phone_number(self.cleaned_data['phoneNumber1'])
        if Client.objects.filter(phoneNumber1=phone_number1).exists() or Client.objects.filter(phoneNumber2=phone_number1).exists():
            raise forms.ValidationError('Client with the same phone number already exists.')
        return phone_number1

    def clean_phoneNumber2(self):
        phone_number2 = self.cleaned_data.get('phoneNumber2')
        if phone_number2:
            phone_number2 = normalize_phone_number(phone_number2)
            if len(phone_number2) < 7:
                raise forms.ValidationError("Phone number must be at least 7 characters long.")
            if Client.objects.filter(phoneNumber1=phone_number2).exists() or Client.objects.filter(phoneNumber2=phone_number2).exists():
                raise forms.ValidationError('Client with the same phone number already exists.')
        return phone_number2

    def clean(self):
        cleaned_data = super().clean()
        phone_number1 = cleaned_data.get("phoneNumber1")
        phone_number2 = cleaned_data.get("phoneNumber2")

        if phone_number1 and phone_number2 and phone_number1 == phone_number2:
            raise forms.ValidationError("Phone number 1 and phone number 2 cannot be the same.")

        return cleaned_data


class ClientModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        phone_number_2 = f", {obj.phoneNumber2}" if obj.phoneNumber2 else ""
        return f"{obj.name} (Phone 1: {obj.phoneNumber1}{phone_number_2})"


class EmployeeModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Construct the full name using first_name and last_name
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        # Return a label that includes the full name and email
        return f"{full_name} (Email: {obj.user.email})"


class ReassignClientForm(forms.Form):
    client = ClientModelChoiceField(
        queryset=Client.objects.all(),
        label='Select Client',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    new_employee = EmployeeModelChoiceField(
        queryset=Employees.objects.filter(exclude_from_reassignment=False),
        label='Re-assign to Distributor',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
