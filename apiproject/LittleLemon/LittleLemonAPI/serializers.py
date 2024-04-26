from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, OrderItem
from django.contrib.auth.models import User

class CategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','title', 'slug']

class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    class Meta:
        model = MenuItem
        fields = ['id','title','price','category','featured']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username', 'email', 'password')

class CartMenuSerializer(serializers.ModelSerializer):
    class Meta():
        model = MenuItem
        fields = ['id','title','price']

class CartSerializer(serializers.ModelSerializer):
    menuitem = CartMenuSerializer()
    username = serializers.CharField(
        source = "user.username", read_only = True
    )
    class Meta():
        model = Cart
        fields = ['username','menuitem','quantity','price']
        
class CartAddSerializer(serializers.ModelSerializer):
    menuitem = CartMenuSerializer
    class Meta():
        model = Cart
        fields = ['user','menuitem','quantity']
        extra_kwargs = {
            'quantity': {'min_value': 1},
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('menuitem', 'user'),
                message="Item already in cart!"
            )
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = CartMenuSerializer()
    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'quantity']


class OrderSerializer(serializers.ModelSerializer):

    orderitem = OrderItemSerializer(many=True, read_only=True, source='order')
    username = serializers.CharField(
        source = "user.username", read_only = True
    )
    class Meta:
        model = Order
        fields = ['id', 'username', 'delivery_crew',
                  'status', 'date', 'total', 'orderitem']


class OrderPostSerializer(serializers.ModelSerializer): 
    class Meta():
        model = Order
        fields = []
    
class OrderPutSerializer(serializers.ModelSerializer):
    class Meta():
        model = Order
        fields = ['delivery_crew', 'status']

class OrderPutDeliverySerializer(serializers.ModelSerializer):
    class Meta():
        model = Order
        fields = ['status']
