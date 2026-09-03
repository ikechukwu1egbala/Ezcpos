#from rest_framework.routers import DefaultRouter
#from .views import ProductViewSet

#router = DefaultRouter()
#router.register(r'products', ProductViewSet)

#urlpatterns = router.urls




from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet

router = DefaultRouter()
router.register(r'logs', InventoryViewSet)

urlpatterns = router.urls