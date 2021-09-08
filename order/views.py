import stripe

from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse

from rest_framework import status, authentication, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import OrderSerializer, MyOrderSerializer

from twilio.rest import Client

@api_view(['POST'])
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    serializer = OrderSerializer(data=request.data)

    if serializer.is_valid():
        stripe.api_key = settings.STRIPE_SECRET_KEY
        paid_amount = sum(item.get('quantity') * item.get('product').price for item in serializer.validated_data['items'])

        try:
            charge = stripe.Charge.create(
                amount=int(paid_amount * 100),
                currency='USD',
                description='Charge from Inner Beauty',
                source=serializer.validated_data['stripe_token']
            )

            serializer.save(user=request.user, paid_amount=paid_amount)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([authentication.TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def checkout_success_sms(request):
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        paid_amount = sum(item.get('quantity') * item.get('product').price for item in serializer.validated_data['items'])

    message_to_broadcast = ("Thank you for your order at Inner Beauty. You'll be charged with' $" + str(paid_amount) + " and your order will be processed within 2 days.\nWhile waiting, go checkout for more latest products at www.innerbeauty.com !")
    # Twilio SMS sender
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    phone_number = "+1" + serializer.validated_data['phone'];

    if phone_number:
        client.messages.create(to=phone_number,
                            from_=settings.TWILIO_NUMBER,
                            body=message_to_broadcast)

    return HttpResponse("messages sent!", 200)

class OrdersList(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        orders = Order.objects.filter(user=request.user)
        serializer = MyOrderSerializer(orders, many=True)
        return Response(serializer.data)