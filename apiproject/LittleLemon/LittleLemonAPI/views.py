from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .paginations import MenuItemListPagination, OrderListPagination
from .serializers import MenuItemSerializer, CategorySerializer, UserSerializer, CartSerializer, CartAddSerializer, OrderPostSerializer, OrderSerializer, OrderPutSerializer, OrderPutDeliverySerializer
from django.contrib.auth.models import User, Group
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from .models import MenuItem, Category, Cart, Order, OrderItem
from .permissions import IsManager
from datetime import date

class CategoriesView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class MenuItemsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['title','category__title'] # Can search for menu title or category title
    ordering_fields=['price','category']
    pagination_class = MenuItemListPagination
    
    def get_permissions(self):
        if self.request.method == 'GET': 
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsManager | IsAdminUser]
        return[permission() for permission in permission_classes]
    
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET': 
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PUT' or 'PATCH' or 'DELETE':
            permission_classes = [IsManager | IsAdminUser]
        return[permission() for permission in permission_classes]

class ManagerView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = request.data['username']
        email = request.data['email']
        password = request.data['password']
        headers = self.get_success_headers(serializer.data)
        current_user = User.objects.create(username = username, email = email, password = password)
        managers = Group.objects.get(name="Manager")
        managers.user_set.add(current_user)
        return Response({"message": "User added to Manager group"}, status=status.HTTP_201_CREATED, headers=headers)

class ManagerSingleItemView(generics.RetrieveAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager]

    def get(self, request, *args, **kwargs):
        if self.get_object():
            instance = self.get_object()
            instance.delete()
            return Response({'message': 'Successfully deleted Manager member.'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
             
class DeliveryCrewView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = request.data['username']
        email = request.data['email']
        password = request.data['password']
        headers = self.get_success_headers(serializer.data)
        current_user = User.objects.create(username = username, email = email, password = password)
        delivery_crew = Group.objects.get(name="Delivery crew")
        delivery_crew.user_set.add(current_user)
        return Response({"message": "User added to Delivery crew group"}, status=status.HTTP_201_CREATED, headers=headers)

class DeliverySingleItemView(generics.RetrieveAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager]

    def get(self, request, *args, **kwargs):
        if self.get_object():
            instance = self.get_object()
            instance.delete()
            return Response({'message': 'Successfully deleted Delivery crew member.'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
class CartView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        return Cart.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CartAddSerializer
        return CartSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id = request.data['menuitem']
        quantity = request.data['quantity']
        item = get_object_or_404(MenuItem, id=id)
        price = int(quantity) * item.price
        headers = self.get_success_headers(serializer.data)
        Cart.objects.create(user=request.user, quantity=quantity, unit_price=item.price, price=price, menuitem_id=id)
        return Response({'message':'Item added to cart!'}, status=status.HTTP_201_CREATED, headers=headers)  
                                

    def delete(self, request, *args, **kwargs):
        Cart.objects.all().filter(user=self.request.user).delete()
        return Response({'message':'Cart is now empty!'}, status=status.HTTP_200_OK)
    
    

class OrdersView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    pagination_class = OrderListPagination
    ordering_fields=['total', 'status', 'date']
    search_fields=['user__username'] # Search for user by username 


    def get_queryset(self, *args, **kwargs):
        if self.request.user.groups.filter(name='Manager').exists() or self.request.user.is_superuser == True:
            return Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        else:
            return Order.objects.filter(user=self.request.user)
        
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderPostSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if Cart.objects.filter(user=request.user).exists() == False:
            return Response({'message': 'Your cart is empty, please add items to cart!'}, status=status.HTTP_400_BAD_REQUEST)
        total_price = Cart.objects.filter(user=request.user).aggregate(Sum('price'))['price__sum'] or 0

        order = Order.objects.create(user=request.user, status=False, total=total_price, date=date.today())
        items = Cart.objects.all().filter(user=self.request.user).all()
        for item in items.values():
                orderitem = OrderItem.objects.create(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    quantity=item['quantity'],
                )
                orderitem.save()
        Cart.objects.all().filter(user=self.request.user).delete() #Delete cart items
        return Response({'message':'Your order has been placed! Your order number is {}'.format(str(order.id))}, status=status.HTTP_400_BAD_REQUEST)    


class OrderItemView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]         
    queryset = Order.objects.all()
    
    def get_serializer_class(self):
        is_delivery_crew = self.request.user.groups.filter(name='Delivery crew').exists()
        if self.request.method == 'PUT':
            if is_delivery_crew:
                return OrderPutDeliverySerializer
            else:
                return OrderPutSerializer
        return OrderSerializer

    
    def get_permissions(self):
        if self.request.method == 'GET': 
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'PUT' or 'PATCH' or 'DELETE':
            permission_classes = [IsManager | IsAdminUser]
        return[permission() for permission in permission_classes]
    
    def get(self, request, *args, **kwargs):
        username = Order.objects.get(pk=self.kwargs['pk']).user.username
        current_user = self.request.user
        is_admin = current_user.is_superuser
        is_manager = current_user.groups.filter(name='Manager').exists()
        is_delivery_crew = current_user.groups.filter(name='Delivery crew').exists()
        delivery_crew_assignment = Order.objects.get(pk=self.kwargs['pk']).delivery_crew
        delivery_crew_id = NotImplemented
        
        if delivery_crew_assignment == None:
            delivery_crew_id = None
        else:    
            delivery_crew_id = Order.objects.get(pk=self.kwargs['pk']).delivery_crew.pk

        if is_delivery_crew == True:
            if (delivery_crew_id != current_user.pk):
                return Response({'message': 'Incorrect Order ID for Customer. Please select correct delivery order!'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            else : 
                return self.retrieve(request, *args, **kwargs)
        elif (username != current_user.username) and (is_admin == False) and (is_manager == False):
            return Response({'message': 'Incorrect Order ID for User. Please select another order for {} !'.format(current_user)}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        return self.retrieve(request, *args, **kwargs)
    

    def put(self, request, *args, **kwargs):
        current_user = self.request.user
        is_admin = current_user.is_superuser
        is_manager = current_user.groups.filter(name='Manager').exists()
        if (is_admin == False) and (is_manager == False):        
            return Response({'message': 'Do not have access to this '}, status=status.HTTP_403_FORBIDDEN)
        return super().put(request, *args, **kwargs)