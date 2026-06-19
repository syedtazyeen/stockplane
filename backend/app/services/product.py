import uuid

from fastapi import status

from app.exceptions.base import AppError
from app.models.product import Product, ProductStatus
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductPut, ProductUpdate
from app.services.inventory import InventoryService


class ProductService:
    """Product catalog workflows."""

    def __init__(
        self,
        product_repository: ProductRepository,
        inventory_service: InventoryService,
    ) -> None:
        self.product_repository = product_repository
        self.inventory_service = inventory_service

    @property
    def db(self):
        return self.product_repository.db

    async def _ensure_unique_sku(
        self,
        *,
        business_id: uuid.UUID,
        sku: str,
        exclude_product_id: uuid.UUID | None = None,
    ) -> None:
        existing = await self.product_repository.get_by_sku_for_business(
            sku=sku,
            business_id=business_id,
            exclude_product_id=exclude_product_id,
        )
        if existing:
            raise AppError(status_code=status.HTTP_400_BAD_REQUEST, detail="SKU already in use")

    async def list_products(
        self,
        *,
        business_id: uuid.UUID,
        status_filter: ProductStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        return await self.product_repository.list_for_business(
            business_id=business_id,
            status=status_filter,
            search=search,
            offset=offset,
            limit=limit,
        )

    async def get_product(
        self, *, business_id: uuid.UUID, product_id: uuid.UUID
    ) -> Product:
        product = await self.product_repository.get_by_id_for_business(
            product_id=product_id,
            business_id=business_id,
        )
        if product is None:
            raise AppError(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    async def create_product(
        self, *, business_id: uuid.UUID, product_in: ProductCreate, user_id: uuid.UUID
    ) -> Product:
        await self._ensure_unique_sku(business_id=business_id, sku=product_in.sku)

        product = Product(
            business_id=business_id,
            sku=product_in.sku,
            name=product_in.name,
            description=product_in.description,
            status=product_in.status,
            cost_price=product_in.cost_price,
            selling_price=product_in.selling_price,
        )
        await self.product_repository.create(obj=product)

        await self.inventory_service.create_initial_for_product(
            product=product,
            quantity=product_in.quantity,
            reorder_point=product_in.reorder_point,
            user_id=user_id,
        )

        await self.db.commit()
        return await self.get_product(business_id=business_id, product_id=product.id)

    async def update_product(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        product_in: ProductUpdate,
        user_id: uuid.UUID,
    ) -> Product:
        product = await self.get_product(business_id=business_id, product_id=product_id)

        update_data = product_in.model_dump(exclude_unset=True)
        reorder_point = update_data.pop("reorder_point", None)
        quantity = update_data.pop("quantity", None)

        if "sku" in update_data:
            await self._ensure_unique_sku(
                business_id=business_id,
                sku=update_data["sku"],
                exclude_product_id=product.id,
            )

        for field, value in update_data.items():
            setattr(product, field, value)

        if reorder_point is not None:
            await self.inventory_service.set_reorder_point(
                business_id=business_id,
                product=product,
                reorder_point=reorder_point,
            )

        if quantity is not None:
            await self.inventory_service.set_quantity_on_product(
                business_id=business_id,
                product=product,
                quantity=quantity,
                user_id=user_id,
                notes="Stock updated via product patch",
            )

        await self.db.commit()
        return await self.get_product(business_id=business_id, product_id=product.id)

    async def replace_product(
        self,
        *,
        business_id: uuid.UUID,
        product_id: uuid.UUID,
        product_in: ProductPut,
        user_id: uuid.UUID,
    ) -> Product:
        product = await self.get_product(business_id=business_id, product_id=product_id)

        await self._ensure_unique_sku(
            business_id=business_id,
            sku=product_in.sku,
            exclude_product_id=product.id,
        )

        product.sku = product_in.sku
        product.name = product_in.name
        product.description = product_in.description
        product.status = product_in.status
        product.cost_price = product_in.cost_price
        product.selling_price = product_in.selling_price

        await self.inventory_service.set_reorder_point(
            business_id=business_id,
            product=product,
            reorder_point=product_in.reorder_point,
        )
        await self.inventory_service.set_quantity_on_product(
            business_id=business_id,
            product=product,
            quantity=product_in.quantity,
            user_id=user_id,
            notes="Stock set via product update",
        )

        await self.db.commit()
        return await self.get_product(business_id=business_id, product_id=product.id)

    async def delete_product(
        self, *, business_id: uuid.UUID, product_id: uuid.UUID
    ) -> None:
        product = await self.get_product(business_id=business_id, product_id=product_id)
        await self.product_repository.delete(obj=product)
        await self.db.commit()
