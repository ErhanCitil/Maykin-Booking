from .models import City, Hotel, Room, Order, ROOM_CHOICES, Highlight
from django.views import generic
import io
from django.core.management import call_command
import base64

from form.forms import OrderForm1, OrderForm2

from django.http import HttpResponseRedirect
from django.shortcuts import render
from formtools.wizard.views import SessionWizardView

from django_weasyprint import WeasyTemplateResponseMixin
from django_weasyprint.views import WeasyTemplateResponse
import io
import uuid
from django.http import Http404
# Create your views here.

class Index(generic.ListView):
    model = City
    template_name = 'index.html'
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = City.objects.values('name').distinct()
        return context

# Class-Based View voor de stad pagina ik geef de stad naam mee als parameter. Altijd met een hoofdletter de naam van een class
class Stad(generic.ListView):
    paginate_by = 4
    model = Hotel
    template_name = 'stad.html'

    def get_queryset(self):
        return Hotel.objects.filter(city__name=self.kwargs['city_name'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['city_name'] = self.kwargs['city_name']
        return context

    """"
    Ik filter hier op de stad naam die ik meegeef als parameter binnen de url en die gebruik ik dan voor de paginate. 
    Eerst filterde ik op alle steden binnen in de database, en toen kreeg ik alle hotels van alle steden in de pagina te zien wat niet de bedoeling is.
    """

class HotelList(generic.ListView):
    model = City
    template_name = 'hotels.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['city_name'] = City.objects.values('name').distinct()
        return context

class HotelDetail(generic.DetailView):
    model = Hotel
    template_name = 'hotel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = Room.objects.filter(hotel=self.kwargs['pk'])
        context['highlights'] = Highlight.objects.filter(hotel=self.kwargs['pk'])
        return context

class DatabaseSchema(generic.TemplateView):
    template_name = 'database_schema.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        with io.StringIO() as out:
            call_command('graph_models', '-a', '-o', 'static/schema.png', stdout=out)
            with open('static/schema.png', 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read())
                context['schema'] = encoded_string
        return context

class OrderWizard(SessionWizardView):
    template_name = 'order.html'
    form_list = [OrderForm1, OrderForm2]

    def get_queryset(self):
        return Hotel.objects.filter(id= self.kwargs['pk'])

    def get_context_data(self, form, **kwargs):
        context = super(OrderWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.current == '0' or self.steps.current == '1':
            context['hotel'] = Hotel.objects.get(id=self.kwargs['pk'])
        if self.steps.current == '1':
            context['step0'] = self.get_cleaned_data_for_step('0')
            context['step1'] = self.get_cleaned_data_for_step('1')
            context['order'] = Order.objects.create(
                start_date = context['step0']['start_date'],
                end_date = context['step0']['end_date'],
                hotel = Hotel.objects.get(id=self.kwargs['pk']),
                room = Room.objects.filter(hotel=self.kwargs['pk'], room_type=context['step0']['room_type']).first(),
            )
            self.request.session['order_id'] = context['order'].id
        return context

    def done(self, form_list, **kwargs):
        order_token = self.request.session.get('order_token')
        if not order_token:
            order_token = self.request.session['order_token'] = str(uuid.uuid4())
        order = Order()
        order = Order.objects.create(
            first_name=form_list[1].cleaned_data['first_name'],
            last_name=form_list[1].cleaned_data['last_name'],
            email=form_list[1].cleaned_data['email'],
            address=form_list[1].cleaned_data['address'],
            zipcode=form_list[1].cleaned_data['zipcode'],
            country=form_list[1].cleaned_data['country'],
            start_date = form_list[0].cleaned_data['start_date'],
            end_date = form_list[0].cleaned_data['end_date'],
            hotel = Hotel.objects.get(id=self.kwargs['pk']),
            room = Room.objects.filter(hotel=self.kwargs['pk']).filter(room_type=form_list[0].cleaned_data['room_type']).first(),
            token = order_token
        )
        order = Order.objects.get(id=self.request.session['order_id'])
        order.first_name = form_list[1].cleaned_data['first_name']
        order.last_name = form_list[1].cleaned_data['last_name']
        order.email = form_list[1].cleaned_data['email']
        order.address = form_list[1].cleaned_data['address']
        order.zipcode = form_list[1].cleaned_data['zipcode']
        order.country = form_list[1].cleaned_data['country']
        order.save()
        return HttpResponseRedirect('/success/{}'.format(order.id))

class Success(generic.DetailView):
    model = Order
    template_name = 'success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = Order.objects.get(id=self.kwargs['pk'])
        return context

    def get(self, request, *args, **kwargs):
        order_id = self.kwargs['pk']
        order = Order.objects.get(id=order_id)
        order_token = request.session.get('order_token')
        if order_token != order.token:
            raise Http404
        return super().get(request, *args, **kwargs)

class OrderPDF(WeasyTemplateResponseMixin, generic.DetailView):
    model = Order
    template_name = 'order_pdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = Order.objects.get(id=self.kwargs['pk'])
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        pdf = WeasyTemplateResponse(
            request=request,
            template=self.template_name,
            context=self.get_context_data(),
            filename='order_{}.pdf'.format(self.kwargs['pk']),
        )
        return pdf