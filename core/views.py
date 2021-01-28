from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import (
    User,
    UserProfile,
    MonitorStock,
    PortHistory,
)
from core.serializers import (
    UserSerializer,
    UserProfileSerializer,
    MonitorStockSerializer,
    PortHistorySerializer,
)
from core.permissions import IsOwnerOrReadOnly

class UserViewList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class LoginView(APIView):
    def post(self, request):
        id = request.data.get('username')
        pw = request.data.get('password')
        user = authenticate(username=id, password=pw)
        if user is not None:
            try:
                return Response({'Token': user.auth_token.key, 'id': user.id})
            except:
                return Response({'success': 'login success, but no token available'})
        else:
            return Response({'fail': 'no such user'})

'''
요청 보내는 법:
import json, requests
data = { ... }
headers = {'Content-Type': 'application/json'}
r = requests.post(url, data=data, headers=headers)
'''

class MonitorStockList(generics.ListCreateAPIView):
    queryset = MonitorStock.objects.all()
    serializer_class = MonitorStockSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    permission_classes = (IsAuthenticated,)

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self, *args, **kwargs):
        queryset = MonitorStock.objects.all()
        user_by = self.request.GET.get('user')
        date_by = self.request.GET.get('date')
        if user_by:
            queryset = queryset.filter(user=user_by)
        if date_by:
            queryset = queryset.filter(date=date_by)
        return queryset

class MonitorStockDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = MonitorStock.objects.all()
    serializer_class = MonitorStockSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

class PortHistoryList(generics.ListCreateAPIView):
    queryset = PortHistory.objects.all()
    serializer_class = PortHistorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    permission_classes = (IsAuthenticated,)

    def get_queryset(self, *args, **kwargs):
        queryset = PortHistory.objects.all()
        user_by = self.request.GET.get('user')
        date_by = self.request.GET.get('date')
        if user_by:
            queryset = queryset.filter(user=user_by)
        if date_by:
            queryset = queryset.filter(date=date_by)
        return queryset


class PortHistoryDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = PortHistory.objects.all()
    serializer_class = PortHistorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]