import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useParams } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ArrowLeftIcon } from "@phosphor-icons/react";
import { useForm } from "react-hook-form";

import { productQueryOptions } from "@/api/products";
import { ListPage } from "@/components/shared/list-page";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateProductMutation,
  useUpdateProductMutation,
} from "@/hooks/use-products";
import { productFormSchema, toProductPayload } from "@/lib/schemas/product";

const defaultValues = {
  sku: "",
  name: "",
  description: "",
  status: "DRAFT",
  cost_price: "0.00",
  selling_price: "0.00",
  quantity: 0,
  reorder_point: "",
};

function productToFormValues(product) {
  return {
    sku: product.sku,
    name: product.name,
    description: product.description ?? "",
    status: product.status,
    cost_price: String(product.cost_price),
    selling_price: String(product.selling_price),
    quantity: product.quantity,
    reorder_point: product.inventory?.reorder_point ?? "",
  };
}

function ProductFormFields({
  businessId,
  isEdit,
  mutation,
  initialValues = defaultValues,
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(productFormSchema),
    defaultValues: initialValues,
  });

  const onSubmit = handleSubmit(async (values) => {
    await mutation.mutateAsync(toProductPayload(values));
  });

  return (
    <Card className="max-w-2xl">
      <CardContent className="pt-6">
        <form className="space-y-6" onSubmit={onSubmit}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                aria-invalid={Boolean(errors.name)}
                {...register("name")}
              />
              {errors.name ? (
                <FieldError>{errors.name.message}</FieldError>
              ) : null}
            </Field>

            <Field>
              <Label htmlFor="sku">SKU</Label>
              <Input
                id="sku"
                aria-invalid={Boolean(errors.sku)}
                {...register("sku")}
              />
              {errors.sku ? (
                <FieldError>{errors.sku.message}</FieldError>
              ) : null}
            </Field>
          </div>

          <Field>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              rows={3}
              {...register("description")}
            />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <Label htmlFor="status">Status</Label>
              <Select
                id="status"
                aria-invalid={Boolean(errors.status)}
                {...register("status")}
              >
                <option value="DRAFT">Draft</option>
                <option value="ACTIVE">Active</option>
                <option value="ARCHIVED">Archived</option>
              </Select>
              {errors.status ? (
                <FieldError>{errors.status.message}</FieldError>
              ) : null}
            </Field>

            <Field>
              <Label htmlFor="quantity">Quantity on hand</Label>
              <Input
                id="quantity"
                type="number"
                min={0}
                aria-invalid={Boolean(errors.quantity)}
                {...register("quantity")}
              />
              {errors.quantity ? (
                <FieldError>{errors.quantity.message}</FieldError>
              ) : null}
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <Field>
              <Label htmlFor="cost_price">Cost price</Label>
              <Input
                id="cost_price"
                type="number"
                min={0}
                step="0.01"
                aria-invalid={Boolean(errors.cost_price)}
                {...register("cost_price")}
              />
              {errors.cost_price ? (
                <FieldError>{errors.cost_price.message}</FieldError>
              ) : null}
            </Field>

            <Field>
              <Label htmlFor="selling_price">Selling price</Label>
              <Input
                id="selling_price"
                type="number"
                min={0}
                step="0.01"
                aria-invalid={Boolean(errors.selling_price)}
                {...register("selling_price")}
              />
              {errors.selling_price ? (
                <FieldError>{errors.selling_price.message}</FieldError>
              ) : null}
            </Field>

            <Field>
              <Label htmlFor="reorder_point">Reorder point</Label>
              <Input
                id="reorder_point"
                type="number"
                min={0}
                placeholder="Optional"
                aria-invalid={Boolean(errors.reorder_point)}
                {...register("reorder_point")}
              />
              {errors.reorder_point ? (
                <FieldError>{errors.reorder_point.message}</FieldError>
              ) : null}
            </Field>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              render={
                <Link
                  to="/$businessId/products"
                  params={{ businessId }}
                />
              }
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isSubmitting || mutation.isPending}
              disabled={isSubmitting || mutation.isPending}
            >
              {isEdit ? "Save changes" : "Create product"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function ProductFormPage() {
  const { businessId } = useParams({ strict: false });
  const mutation = useCreateProductMutation(businessId);

  return (
    <ListPage>
      <PageHeader
        title="Add product"
        actions={
          <Button
            variant="outline"
            render={
              <Link
                to="/$businessId/products"
                params={{ businessId }}
              />
            }
          >
            <ArrowLeftIcon />
            Back to products
          </Button>
        }
      />
      <ProductFormFields
        businessId={businessId}
        isEdit={false}
        mutation={mutation}
      />
    </ListPage>
  );
}

function ProductEditPage() {
  const { businessId, productId } = useParams({ strict: false });
  const { data: product } = useSuspenseQuery(
    productQueryOptions(businessId, productId),
  );
  const mutation = useUpdateProductMutation(businessId, productId);

  return (
    <ListPage>
      <PageHeader
        title="Edit product"
        actions={
          <Button
            variant="outline"
            render={
              <Link
                to="/$businessId/products"
                params={{ businessId }}
              />
            }
          >
            <ArrowLeftIcon />
            Back to products
          </Button>
        }
      />
      <ProductFormFields
        businessId={businessId}
        isEdit
        mutation={mutation}
        initialValues={productToFormValues(product)}
      />
    </ListPage>
  );
}

export { ProductFormPage, ProductEditPage };
