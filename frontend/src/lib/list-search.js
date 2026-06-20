export const PAGE_SIZE = 10;

function parsePage(value) {
  const page = Number(value);
  return Number.isInteger(page) && page >= 1 ? page : 1;
}

function parseString(value) {
  return typeof value === "string" ? value : "";
}

function parseLowStock(value) {
  return value === "true" || value === "1" || value === true;
}

export function parseProductsListSearch(search = {}) {
  return {
    page: parsePage(search.page),
    search: parseString(search.search),
    status: parseString(search.status),
  };
}

export function parseCustomersListSearch(search = {}) {
  return {
    page: parsePage(search.page),
    search: parseString(search.search),
    status: parseString(search.status),
  };
}

export function parseOrdersListSearch(search = {}) {
  return {
    page: parsePage(search.page),
    status: parseString(search.status),
  };
}

export function parseDraftOrdersListSearch(search = {}) {
  return {
    page: parsePage(search.page),
  };
}

export function parseInventoryListSearch(search = {}) {
  return {
    page: parsePage(search.page),
    lowStock: parseLowStock(search.lowStock),
  };
}

export function toProductsApiParams(listSearch) {
  return {
    offset: (listSearch.page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
    ...(listSearch.search ? { search: listSearch.search } : {}),
    ...(listSearch.status ? { status: listSearch.status } : {}),
  };
}

export function toCustomersApiParams(listSearch) {
  return {
    offset: (listSearch.page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
    ...(listSearch.search ? { search: listSearch.search } : {}),
    ...(listSearch.status ? { status: listSearch.status } : {}),
  };
}

export function toOrdersApiParams(listSearch, { fixedStatus } = {}) {
  let status = fixedStatus ?? listSearch.status;
  if (!fixedStatus && status === "DRAFT") {
    status = undefined;
  }
  return {
    offset: (listSearch.page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
    ...(status ? { status } : {}),
  };
}

export function toInventoryApiParams(listSearch) {
  return {
    offset: (listSearch.page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
    low_stock_only: listSearch.lowStock,
  };
}

export function cleanListSearch(updates) {
  const next = { ...updates };

  if (!next.search) delete next.search;
  if (!next.status) delete next.status;
  if (!next.lowStock) delete next.lowStock;
  if (!next.page || next.page <= 1) delete next.page;

  return next;
}

export function hasNextPage(itemCount) {
  return itemCount === PAGE_SIZE;
}
