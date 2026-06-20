export function isLowStock(item) {
  if (item.quantity_on_hand === 0) return true;
  return (
    item.reorder_point != null &&
    item.available_quantity <= item.reorder_point
  );
}
